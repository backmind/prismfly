"""Generate a markdown report with raw analytical data."""
from pathlib import Path
from datetime import date

from .config import ESCUDO_ACCOUNTS, INVESTMENT_ACCOUNTS, OTHER_ACCOUNTS


def generate(data: dict, output: Path = Path("report.md"), balances: list | None = None) -> Path:
    """Generate the markdown report from computed data."""
    lines = []
    w = lines.append

    w("# Real Purchasing Power Analysis")
    w("")
    w(f"Generated: {date.today().isoformat()}")
    w("")

    # ── Current balances ──
    if balances:
        bal_map = {a["name"]: a["balance"] for a in balances}

        def _render_group(title, accounts_cfg, extra_rows=None):
            """Render a table of accounts from personal.json config."""
            rows = extra_rows or []
            for name, info in accounts_cfg.items():
                bal = bal_map.get(name, 0)
                fe_amt = info.get("fe_amount")
                if fe_amt:
                    rows.append((f"{name} (FE)", min(bal, fe_amt), info["desc"]))
                    remainder = max(bal - fe_amt, 0)
                    if remainder > 0:
                        rows.append((f"{name} (DCA)", remainder, "Capital in migration"))
                else:
                    rows.append((name, bal, info["desc"]))
            total = sum(v for _, v, _ in rows)
            w(f"### {title}")
            w("")
            w("| Account | Balance | Purpose |")
            w("|---------|--------:|---------|")
            for name, bal, desc in rows:
                w(f"| {name} | {bal:,.2f} EUR | {desc} |")
            w(f"| **Total** | **{total:,.2f} EUR** | |")
            w("")
            return total

        w("## Current Financial Snapshot")
        w("")
        t_escudo = _render_group("Emergency fund (shield)", ESCUDO_ACCOUNTS)
        t_inv = _render_group("Investments", INVESTMENT_ACCOUNTS)
        t_other = _render_group("Other assets", OTHER_ACCOUNTS)
        w(f"**Total financial assets: {t_escudo + t_inv + t_other:,.2f} EUR**")
        w("")

    w("> For interpretation of this data, see **CONTEXTO.md** (personal situation, account structure, investment strategy, financial events, notes on volatile items).")
    w("")

    # ── KPIs ──
    if len(data["summary"]) >= 2:
        first = data["summary"][0]
        last = data["summary"][-2] if len(data["summary"]) > 2 else data["summary"][-1]
        sal_first = data["fiscal"][str(first["year"])]["neto"]
        sal_last = data["fiscal"][str(last["year"])]["neto"]
        growth = (sal_last / sal_first - 1) * 100
        icvp_last = data["c3"]["pclpi"][-2] if len(data["c3"]["pclpi"]) > 1 else 1
        ipc_last = data["c3"]["cpi"][-2] if len(data["c3"]["cpi"]) > 1 else 1

        w("## Key Indicators")
        w("")
        w("| Indicator | Value |")
        w("|-----------|------:|")
        w(f"| Net salary growth {first['year']}→{last['year']} | +{growth:.0f}% |")
        w(f"| PCLPI {last['year']} (base {first['year']}=1) | {icvp_last:.3f} |")
        w(f"| Cumulative CPI {last['year']} | {ipc_last:.3f} |")
        w(f"| Savings rate {last['year']} | {last['savings_rate']:+.1f}% |")
        w(f"| Monthly margin {last['year']} | {last['margin_mo']:+,} EUR |")
        w("")

    # ── Annual summary ──
    w("## Annual Summary")
    w("")
    has_partner = data["labels"]["has_partner"]
    reemb_label = data["labels"]["reemb"]
    accts_label = data["labels"]["accounts"]
    reemb_col = f" {reemb_label} |" if has_partner else ""
    reemb_sep = "---:|" if has_partner else ""
    w(f"| Year | Months | Total deposits | Gross spending |{reemb_col} Net spending | Net/mo | Salary/mo | Margin/mo | Savings rate | Δ accounts |")
    w(f"|-----:|-------:|---------------:|---------------:|{reemb_sep}-------------:|-------:|----------:|----------:|-------------:|-----------:|")
    for r in data["summary"]:
        dc = f"{r['delta_accounts']:+,}" if r["delta_accounts"] is not None else "—"
        rc = f" {r['reimbursement']:,} |" if has_partner else ""
        w(f"| {r['year']} | {r['months']} | {r['total_deposits']:,} | {r['gross_expense']:,} |{rc} {r['net_expense']:,} | {r['expense_mo']:,} | {r['salary_mo']:,} | {r['margin_mo']:+,} | {r['savings_rate']:+.1f}% | {dc} |")
    w("")

    # ── Monthly average by basket ──
    w("## Average Monthly Spending by Basket (EUR/mo)")
    w("")
    hm = data["heatmap"]
    baskets = hm["baskets"]
    years = hm["years"]
    header = "| Basket | " + " | ".join(years) + " |"
    sep = "|---|" + "|".join(["---:" for _ in years]) + "|"
    w(header)
    w(sep)
    for i, bsk in enumerate(baskets):
        vals = " | ".join(str(v) for v in hm["z"][i])
        w(f"| {bsk} | {vals} |")
    w("")

    # ── Distribution % ──
    if "weights" in data and data["weights"]:
        w("## Spending Distribution by Basket (% of total)")
        w("")
        weights = data["weights"]
        w_baskets = list(weights.keys())
        p_years = sorted({y for vals in weights.values() for y in vals})
        header = "| Basket | " + " | ".join(str(y) for y in p_years) + " |"
        sep = "|---|" + "|".join(["---:" for _ in p_years]) + "|"
        w(header)
        w(sep)
        for c in w_baskets:
            vals = " | ".join(f"{weights[c].get(str(y), weights[c].get(y, 0)):.1f}" for y in p_years)
            w(f"| {c} | {vals} |")
        w("")

    # ── PCLPI vs CPI ──
    w("## PCLPI vs Cumulative CPI (base 2017 = 1.000)")
    w("")
    w("| Year | PCLPI | CPI | Divergence |")
    w("|-----:|------:|----:|-----------:|")
    for y_str, icvp, ipc in zip(data["c3"]["years"], data["c3"]["pclpi"], data["c3"]["cpi"]):
        div = icvp - ipc
        w(f"| {y_str} | {icvp:.3f} | {ipc:.3f} | {div:+.3f} |")
    w("")

    # ── Elasticity ──
    w("## Discretionary Spending Elasticity vs Income")
    w("")
    w("Elasticity < 1 = spending restraint. > 1 = lifestyle inflation.")
    w("")
    w("| Period | Δ Income % | Δ Disc. spending % | Elasticity |")
    w("|--------|----------:|-----------------:|----------:|")
    for e in data["elasticity"]:
        elast = e["y"] / e["x"] if e["x"] != 0 else 0
        w(f"| {e['label']} | {e['x']:+.1f} | {e['y']:+.1f} | {elast:+.2f} |")
    w("")

    # ── Dining & leisure ──
    w("## Dining & Leisure (lifestyle inflation indicator)")
    w("")
    w("| Year | EUR/mo | % salary |")
    w("|-----:|-------:|---------:|")
    for y in sorted(data["rest"].keys(), key=int):
        r = data["rest"][y]
        w(f"| {y} | {r['eur']} | {r['pct']}% |")
    w("")

    # ── Quarterly spending ──
    w("## Quarterly Spending (necessities / discretionary / other)")
    w("")
    w("| Quarter | Necessities | Discretionary | Other | Quarterly salary |")
    w("|---------|------------:|--------------:|------:|-----------------:|")
    c1 = data["c1"]
    for i, q in enumerate(c1["quarters"]):
        w(f"| {q} | {c1['necessities'][i]:,} | {c1['discretionary'][i]:,} | {c1['other'][i]:,} | {c1['salary'][i]:,} |")
    w("")

    # ── Account delta ──
    w(f"## Net Change in Main Accounts ({accts_label})")
    w("")
    w("| Year | Δ EUR |")
    w("|-----:|------:|")
    for y, v in zip(data["accounts_delta"]["years"], data["accounts_delta"]["values"]):
        w(f"| {y} | {v:+,} |")
    w("")

    # ── Income composition ──
    w("## Income Composition by Year")
    w("")
    inc = data["income"]
    types = [t for t, vals in inc["types"].items() if any(v > 0 for v in vals)]
    header = "| Year | " + " | ".join(types) + " |"
    sep = "|-----:|" + "|".join(["---:" for _ in types]) + "|"
    w(header)
    w(sep)
    for i, y in enumerate(inc["years"]):
        vals = " | ".join(f"{inc['types'][t][i]:,}" for t in types)
        w(f"| {y} | {vals} |")
    w("")

    # ── Monthly savings rate ──
    w("## Monthly Savings Rate (gross)")
    w("")
    w("| Month | Rate % | 3-mo avg |")
    w("|-------|-------:|---------:|")
    sav = data["savings"]
    for i, m in enumerate(sav["months"]):
        w(f"| {m} | {sav['rate'][i]:+.1f} | {sav['ma3'][i]:+.1f} |")
    w("")

    # ── Sustainability waterfall ──
    w("## Sustainability: Monthly Budget (recent steady-state)")
    w("")
    from .config import RENOVATION_TAGS
    tags_str = " / ".join(sorted(RENOVATION_TAGS)) if RENOVATION_TAGS else "none"
    w(f"Excludes one-off renovations (tags: {tags_str}).")
    w("")
    w("| Item | EUR/mo |")
    w("|------|-------:|")
    for item in data["waterfall"]:
        sign = "+" if item["value"] >= 0 else ""
        w(f"| {item['label']} | {sign}{item['value']:,} |")
    w("")

    content = "\n".join(lines)
    output.write_text(content, encoding="utf-8")
    return output
