"""Data extraction and caching from Firefly III."""
import json
from datetime import date
from pathlib import Path

from .firefly import fetch_all
from .config import MAIN_ACCOUNTS
from .classify import classify_income, is_partner_deposit

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def _tx_record(tx: dict) -> dict:
    """Extract relevant fields from an API transaction."""
    return {
        "date": tx["date"][:10],
        "amount": float(tx["amount"]),
        "category": tx.get("category_name") or "",
        "description": tx.get("description") or "",
        "destination": tx.get("destination_name") or "",
        "destination_id": int(tx.get("destination_id") or 0),
        "source": tx.get("source_name") or "",
        "source_id": int(tx.get("source_id") or 0),
        "tags": tx.get("tags") or [],
    }


def fetch_withdrawals(year: int, force: bool = False) -> list[dict]:
    """Download withdrawals for a year and cache them in data/."""
    cache = DATA_DIR / f"withdrawals_{year}.json"
    today = date.today()
    current_year = today.year

    if cache.exists() and not force and year < current_year:
        with open(cache, "r", encoding="utf-8") as f:
            return json.load(f)

    end = today.isoformat() if year == current_year else f"{year}-12-31"
    raw = fetch_all("/transactions", {
        "start": f"{year}-01-01", "end": end, "type": "withdrawal",
    })
    txs = [_tx_record(t["attributes"]["transactions"][0]) for t in raw]

    with open(cache, "w", encoding="utf-8") as f:
        json.dump(txs, f, ensure_ascii=False, indent=2)
    return txs


def fetch_deposits(year: int, force: bool = False) -> list[dict]:
    """Download deposits for a year and cache them."""
    cache = DATA_DIR / f"deposits_{year}.json"
    today = date.today()
    current_year = today.year

    if cache.exists() and not force and year < current_year:
        with open(cache, "r", encoding="utf-8") as f:
            return json.load(f)

    end = today.isoformat() if year == current_year else f"{year}-12-31"
    raw = fetch_all("/transactions", {
        "start": f"{year}-01-01", "end": end, "type": "deposit",
    })
    txs = [_tx_record(t["attributes"]["transactions"][0]) for t in raw]

    with open(cache, "w", encoding="utf-8") as f:
        json.dump(txs, f, ensure_ascii=False, indent=2)
    return txs


def fetch_account_flows(year: int, force: bool = False) -> dict:
    """Compute net flow (dep - wd + tin - tout) for the main accounts."""
    cache = DATA_DIR / "account_flows.json"
    existing = {}
    if cache.exists():
        with open(cache, "r", encoding="utf-8") as f:
            existing = json.load(f)

    today = date.today()
    current_year = today.year
    key = str(year)

    if key in existing and not force and year < current_year:
        return existing[key]

    end = today.isoformat() if year == current_year else f"{year}-12-31"
    start = f"{year}-01-01"

    all_dep = fetch_all("/transactions", {"start": start, "end": end, "type": "deposit"})
    all_wd = fetch_all("/transactions", {"start": start, "end": end, "type": "withdrawal"})
    all_tr = fetch_all("/transactions", {"start": start, "end": end, "type": "transfer"})

    year_data = {}
    for acct_name, acct_id in MAIN_ACCOUNTS.items():
        deposits = sum(float(t["attributes"]["transactions"][0]["amount"])
                       for t in all_dep if int(t["attributes"]["transactions"][0].get("destination_id", 0)) == acct_id)
        withdrawals = sum(float(t["attributes"]["transactions"][0]["amount"])
                         for t in all_wd if int(t["attributes"]["transactions"][0].get("source_id", 0)) == acct_id)
        tin = sum(float(t["attributes"]["transactions"][0]["amount"])
                  for t in all_tr if int(t["attributes"]["transactions"][0].get("destination_id", 0)) == acct_id)
        tout = sum(float(t["attributes"]["transactions"][0]["amount"])
                   for t in all_tr if int(t["attributes"]["transactions"][0].get("source_id", 0)) == acct_id)
        year_data[acct_name] = {
            "deposits": round(deposits, 2), "withdrawals": round(withdrawals, 2),
            "transfers_in": round(tin, 2), "transfers_out": round(tout, 2),
            "net": round(deposits - withdrawals + tin - tout, 2),
        }

    result = {"accounts": year_data, "total_net": round(sum(v["net"] for v in year_data.values()), 2)}
    existing[key] = result
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    return result


def fetch_account_balances() -> list[dict]:
    """Get current balances of all asset accounts."""
    raw = fetch_all("/accounts", {"type": "asset"})
    return [
        {
            "id": int(a["id"]),
            "name": a["attributes"]["name"],
            "role": a["attributes"].get("account_role", ""),
            "balance": round(float(a["attributes"]["current_balance"]), 2),
            "currency": a["attributes"].get("currency_code", "EUR"),
        }
        for a in raw
    ]


def extract_all(start_year: int = 2017, force_all: bool = False) -> dict:
    """Extract all required data. Returns dict with withdrawals, deposits, flows."""
    today = date.today()
    end_year = today.year
    years = list(range(start_year, end_year + 1))

    print("  Extracting withdrawals...")
    withdrawals = {}
    for y in years:
        force = force_all or y == end_year
        txs = fetch_withdrawals(y, force=force)
        withdrawals[y] = txs
        print(f"    {y}: {len(txs)} transactions")

    print("  Extracting deposits...")
    deposits = {}
    for y in years:
        force = force_all or y == end_year
        txs = fetch_deposits(y, force=force)
        deposits[y] = txs
        print(f"    {y}: {len(txs)} deposits")

    print("  Computing main account flows...")
    flows = {}
    for y in years:
        force = force_all or y == end_year
        fl = fetch_account_flows(y, force=force)
        flows[y] = fl
        print(f"    {y}: Δ = {fl['total_net']:+,.0f} EUR")

    # Partner reimbursement deposits
    partner_deposits = []
    for deps in deposits.values():
        for d in deps:
            if is_partner_deposit(d["source"]):
                partner_deposits.append(d)

    # Income classified
    income = {}
    for y, deps in deposits.items():
        by_type = {}
        for d in deps:
            itype = classify_income(d["category"], d["source"])
            by_type[itype] = by_type.get(itype, 0) + d["amount"]
        income[y] = {k: round(v, 2) for k, v in by_type.items()}

    # Account balances (current snapshot, always refreshed)
    print("  Fetching current balances...")
    balances = fetch_account_balances()
    with open(DATA_DIR / "balances.json", "w", encoding="utf-8") as f:
        json.dump(balances, f, ensure_ascii=False, indent=2)
    print(f"    {len(balances)} accounts")

    return {
        "withdrawals": withdrawals,
        "deposits": deposits,
        "partner_deposits": partner_deposits,
        "income": income,
        "flows": flows,
        "balances": balances,
        "years": years,
    }
