"""Analysis computations: classification, baskets, PCLPI, sustainability."""
import pandas as pd
import numpy as np

from .config import (
    BASKET_MAP, EXCLUDE_CATS, BASKETS_NEC, BASKETS_DISC, BASKETS_ORDER,
    FISCAL, IPC_ACUM, CAPITAL_TAGS, CAPITAL_KEYWORDS, CAPITAL_DESTINATIONS,
    RENOVATION_TAGS, COLORS, SUBSCRIPTION_CATEGORY, SUBS_EDUCATION, SUBS_TECHNOLOGY,
    PARTNER_NAME, MAIN_ACCOUNTS_LABEL, INCOME_INVESTMENT_CATS,
)


def is_capital(tx: dict) -> bool:
    """Detect capital expenditures: first by tags, then by keywords/destinations."""
    tags = set(tx.get("tags", []))
    if tags & CAPITAL_TAGS:
        return True
    desc = (tx.get("description") or "").lower()
    dest = tx.get("destination", "")
    amt = tx["amount"]
    if any(k in desc for k in CAPITAL_KEYWORDS):
        return True
    if dest in CAPITAL_DESTINATIONS and amt >= CAPITAL_DESTINATIONS[dest]:
        return True
    return False


def build_dataframe(withdrawals: dict[int, list]) -> pd.DataFrame:
    """Build classified DataFrame from withdrawals by year."""
    rows = []
    for year, txs in withdrawals.items():
        for tx in txs:
            cat = tx["category"]
            if cat in EXCLUDE_CATS:
                continue
            if is_capital(tx):
                continue
            basket = BASKET_MAP.get(cat, "Other")
            # Reclassify subscriptions by destination
            if SUBSCRIPTION_CATEGORY and cat == SUBSCRIPTION_CATEGORY:
                dest = tx.get("destination", "")
                if dest in SUBS_EDUCATION:
                    basket = "Education"
                elif dest in SUBS_TECHNOLOGY:
                    basket = "Technology"
            rows.append({
                "date": tx["date"],
                "year": int(tx["date"][:4]),
                "month": int(tx["date"][5:7]),
                "amount": tx["amount"],
                "category": cat,
                "basket": basket,
                "destination": tx.get("destination", ""),
                "description": tx.get("description", ""),
                "renovation": bool(set(tx.get("tags", [])) & RENOVATION_TAGS),
            })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["quarter"] = df["date"].dt.to_period("Q").astype(str)
    df["ym"] = df["date"].dt.to_period("M").astype(str)
    return df


def compute_all(df: pd.DataFrame, partner_deposits: list, income: dict, flows: dict) -> dict:
    """Compute all metrics for the dashboard. Returns a JSON-serializable dict."""
    avail_years = sorted(df["year"].unique())
    months_active = df.groupby("year")["month"].nunique()

    # Partner reimbursements per year
    p_df = pd.DataFrame(partner_deposits)
    p_yr = {}
    if not p_df.empty:
        p_df["date"] = pd.to_datetime(p_df["date"])
        p_df["year"] = p_df["date"].dt.year
        p_df["ym"] = p_df["date"].dt.to_period("M").astype(str)
        p_yr = p_df.groupby("year")["amount"].sum().to_dict()

    # Account flows
    acct_net = {int(k): v["total_net"] for k, v in flows.items()}

    # Gross income per year (all deposit types)
    gross_income = {y: sum(inc.values()) for y, inc in income.items()}

    # ── Pivot by basket ──
    gross_expense_yr = df.groupby("year")["amount"].sum()
    annual_basket = df.groupby(["year", "basket"])["amount"].sum().unstack(fill_value=0)
    annual_m = annual_basket.div(months_active, axis=0)

    # Monthly by basket
    monthly_basket = df.groupby(["ym", "basket"])["amount"].sum().unstack(fill_value=0)
    all_months = sorted(df["ym"].unique())

    # PCLPI (Personal Cost of Living Price Index)
    nec_cols = [c for c in BASKETS_NEC if c in annual_m.columns]
    nec_m = annual_m[nec_cols].sum(axis=1)
    base_nec = nec_m.get(2017, 1) or 1
    pclpi = {int(y): round(float(nec_m.get(y, 0) / base_nec), 3) for y in avail_years}

    # Discretionary monthly
    disc_cols = [c for c in BASKETS_DISC if c in annual_m.columns]
    disc_m = annual_m[disc_cols].sum(axis=1)

    # ── Quarterly ──
    all_q = sorted(df["quarter"].unique())
    q_nec = df[df["basket"].isin(BASKETS_NEC)].groupby("quarter")["amount"].sum()
    q_disc = df[df["basket"].isin(BASKETS_DISC)].groupby("quarter")["amount"].sum()
    q_other = df[~df["basket"].isin(BASKETS_NEC | BASKETS_DISC)].groupby("quarter")["amount"].sum()

    # ── Elasticity ──
    elast = []
    for i in range(1, len(avail_years)):
        y, yp = avail_years[i], avail_years[i - 1]
        if y not in FISCAL or yp not in FISCAL:
            continue
        nv = round((FISCAL[y]["neto"] / FISCAL[yp]["neto"] - 1) * 100, 1)
        dc, dp = disc_m.get(y, 0), disc_m.get(yp, 0)
        if dp > 0:
            dv = round((dc / dp - 1) * 100, 1)
            elast.append({"label": f"{yp}-{y}", "x": nv, "y": dv})

    # ── Dining & leisure ──
    rest_col = "Dining & leisure"
    rest_data = {}
    if rest_col in annual_m.columns:
        for y in avail_years:
            if y in annual_m.index:
                v = float(annual_m.loc[y, rest_col])
                sal = FISCAL.get(y, {}).get("neto", 1) / 12
                rest_data[int(y)] = {"eur": round(v), "pct": round(v / sal * 100, 1)}

    # ── Sustainability waterfall (last 9 months excl renovations) ──
    recent = df[df["date"] >= df["date"].max() - pd.Timedelta(days=270)]
    recent_rec = recent[~recent["renovation"]]
    ss_months = recent_rec["ym"].nunique() or 1

    ss_by_basket = recent_rec.groupby("basket")["amount"].sum() / ss_months
    p_recent = p_df[p_df["date"] >= p_df["date"].max() - pd.Timedelta(days=270)] if not p_df.empty else pd.DataFrame()
    p_ss_m = p_recent["amount"].sum() / ss_months if not p_recent.empty else 0
    salary_m = FISCAL.get(avail_years[-1], list(FISCAL.values())[-1])["neto"] / 12

    has_partner = bool(PARTNER_NAME)
    wf = [
        {"label": "Net salary", "value": round(salary_m), "type": "income"},
    ]
    if has_partner and p_ss_m > 0:
        wf.append({"label": f"+ Reimbursement {PARTNER_NAME}", "value": round(p_ss_m), "type": "income"})
    for c in list(BASKETS_NEC):
        v = ss_by_basket.get(c, 0)
        if v > 0:
            wf.append({"label": f"- {c}", "value": -round(v), "type": "necessity"})
    wf.append({"label": "- Investment (1K/mo)", "value": -1000, "type": "investment"})
    remaining = [c for c in BASKETS_ORDER if c not in BASKETS_NEC and ss_by_basket.get(c, 0) > 10]
    for c in remaining:
        v = ss_by_basket.get(c, 0)
        wf.append({"label": f"- {c}", "value": -round(v), "type": "discretionary" if c in BASKETS_DISC else "other"})
    running = sum(item["value"] for item in wf)
    wf.append({"label": "= Free margin", "value": round(running), "type": "margin"})

    # ── Summary table ──
    summary = []
    for y in avail_years:
        m = int(months_active.get(y, 0))
        gb = float(gross_expense_yr.get(y, 0))
        cr = p_yr.get(y, 0)
        gn = gb - cr
        fiscal = FISCAL.get(y, list(FISCAL.values())[-1])
        sm = fiscal["neto"] / 12
        gm = gn / m if m else 0
        sp = fiscal["neto"] * m / 12
        ta = round((1 - gn / sp) * 100, 1) if sp else 0
        an = acct_net.get(y)
        gi = round(gross_income.get(y, 0))
        summary.append({
            "year": y, "months": m, "total_deposits": gi,
            "gross_expense": round(gb), "reimbursement": round(cr), "net_expense": round(gn),
            "expense_mo": round(gm), "salary_mo": round(sm),
            "margin_mo": round(sm - gm), "savings_rate": ta,
            "delta_accounts": round(an) if an is not None else None,
        })

    # ── Heatmap ──
    hm_baskets = [c for c in BASKETS_ORDER[:11] if c in annual_m.columns]
    hm_z = [[round(float(annual_m.loc[y, c])) if y in annual_m.index else 0 for y in avail_years] for c in hm_baskets]

    # ── Monthly chart data ──
    c2_baskets = [c for c in BASKETS_ORDER if c in monthly_basket.columns]
    c2 = {"months": all_months}
    for c in c2_baskets:
        c2[c] = [round(float(monthly_basket.loc[m, c])) if m in monthly_basket.index else 0 for m in all_months]

    # ── Monthly savings rate ──
    monthly_total = df.groupby("ym")["amount"].sum()
    savings = {"months": [], "rate": [], "ma3": []}
    rate_list = []
    for m in all_months:
        yr = int(m[:4])
        sal = FISCAL.get(yr, list(FISCAL.values())[-1])["neto"] / 12
        t = round((1 - float(monthly_total.get(m, 0)) / sal) * 100, 1) if sal else 0
        rate_list.append(t)
        savings["months"].append(m)
        savings["rate"].append(t)
    for i in range(len(rate_list)):
        w = rate_list[max(0, i - 2):i + 1]
        savings["ma3"].append(round(sum(w) / len(w), 1))

    # ── Income stacked ──
    _reemb_label = f"Reimbursement {PARTNER_NAME}" if has_partner else "Reimbursements"
    inc_types = ["Salary"] + ([_reemb_label] if has_partner else []) + ["Tax refund", "Inheritance", "Other income", "Investment return"]
    inc_data = {"years": [str(y) for y in avail_years], "types": {}}
    for t in inc_types:
        inc_data["types"][t] = [round(income.get(y, {}).get(t, 0)) for y in avail_years]

    # ── Relative weights ──
    total_yr = annual_basket.sum(axis=1)
    weights = {}
    for c in BASKETS_ORDER[:11]:
        if c in annual_basket.columns:
            weights[c] = {int(y): round(float(annual_basket.loc[y, c] / total_yr[y] * 100), 1)
                          for y in annual_basket.index if total_yr[y] > 0}

    return _to_native({
        "summary": summary,
        "c1": {
            "quarters": all_q,
            "necessities": [round(q_nec.get(q, 0)) for q in all_q],
            "discretionary": [round(q_disc.get(q, 0)) for q in all_q],
            "other": [round(q_other.get(q, 0)) for q in all_q],
            "salary": [round(FISCAL.get(int(q[:4]), list(FISCAL.values())[-1])["neto"] / 4) for q in all_q],
        },
        "c2": c2,
        "c3": {
            "years": [str(y) for y in avail_years],
            "pclpi": [pclpi.get(y, 1) for y in avail_years],
            "cpi": [IPC_ACUM.get(y, 1) for y in avail_years],
        },
        "heatmap": {"baskets": hm_baskets, "years": [str(y) for y in avail_years], "z": hm_z},
        "elasticity": elast,
        "rest": rest_data,
        "accounts_delta": {
            "years": [str(y) for y in sorted(acct_net.keys())],
            "values": [round(acct_net[y]) for y in sorted(acct_net.keys())],
        },
        "savings": savings,
        "waterfall": wf,
        "income": inc_data,
        "baskets_order": BASKETS_ORDER,
        "colors": COLORS,
        "weights": weights,
        "fiscal": {str(k): v for k, v in FISCAL.items()},
        "labels": {
            "has_partner": has_partner,
            "partner": PARTNER_NAME if has_partner else "",
            "reemb": f"Reimb. {PARTNER_NAME}" if has_partner else "Reimbursements",
            "accounts": MAIN_ACCOUNTS_LABEL,
        },
    })


def _to_native(obj):
    """Convert numpy types to native Python for JSON serialization."""
    if isinstance(obj, dict):
        return {(str(k) if isinstance(k, np.integer) else k): _to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_native(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    return obj
