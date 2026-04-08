#!/usr/bin/env python3
"""
Real purchasing power analysis — Firefly III + income tax data.

Usage:
    uv run main.py              # extract fresh data + generate dashboard
    uv run main.py --no-fetch   # use cache, only regenerate dashboard
    uv run main.py --force      # force re-download of all years
"""
import argparse
import io
import sys
from pathlib import Path

# Windows: force UTF-8 on stdout/stderr
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from src.extract import extract_all
from src.analyze import build_dataframe, compute_all
from src.report import generate as generate_report
from src.dashboard import generate
from src.firefly import check_connection


def main():
    parser = argparse.ArgumentParser(description="Real purchasing power analysis")
    parser.add_argument("--no-fetch", action="store_true", help="Use cached data only")
    parser.add_argument("--force", action="store_true", help="Re-download all years (not just current)")
    parser.add_argument("-o", "--output", default="dashboard.html", help="Dashboard output path (default: dashboard.html)")
    args = parser.parse_args()

    print("=" * 60)
    print(" Real purchasing power analysis")
    print("=" * 60)

    if not args.no_fetch:
        print("\n[1/4] Verifying Firefly III connection...")
        try:
            version = check_connection()
            print(f"  Firefly III v{version} OK")
        except Exception as e:
            print(f"  ERROR: {e}")
            print("  Use --no-fetch to work with cached data.")
            sys.exit(1)

        print("\n[2/4] Extracting data...")
        data = extract_all(force_all=args.force)
    else:
        print("\n[1/4] Offline mode: loading cached data...")
        print("[2/4] Loading cache...")
        data = _load_cached()

    print("\n[3/4] Analyzing...")
    df = build_dataframe(data["withdrawals"])
    results = compute_all(df, data["partner_deposits"], data["income"], data["flows"])
    print(f"  {len(df)} recurring transactions")
    print(f"  {df['year'].min()} - {df['year'].max()}")

    print("\n[4/4] Generating outputs...")
    output = generate(results, Path(args.output))
    print(f"  {output.resolve()} ({output.stat().st_size / 1024:.1f} KB)")

    report_path = Path(args.output).with_suffix(".md")
    generate_report(results, report_path, balances=data.get("balances"))
    print(f"  {report_path.resolve()} ({report_path.stat().st_size / 1024:.1f} KB)")

    print("\n" + "-" * 60)
    for row in results["summary"]:
        y = row["year"]
        dc = f"{row['delta_accounts']:+,}" if row["delta_accounts"] is not None else "—"
        print(f"  {y} | deposits {row['total_deposits']:>7,} | net expense {row['net_expense']:>6,} | "
              f"margin/mo {row['margin_mo']:>+5,} | Δ accounts {dc:>7}")
    print("-" * 60)
    print("\n  Open dashboard.html in your browser.")


def _load_cached():
    """Load data from cached JSONs (--no-fetch mode)."""
    import json
    from src.classify import classify_income, is_partner_deposit

    data_dir = Path("data")
    withdrawals, deposits = {}, {}
    for f in sorted(data_dir.glob("withdrawals_*.json")):
        year = int(f.stem.split("_")[1])
        with open(f, "r", encoding="utf-8") as fh:
            withdrawals[year] = json.load(fh)

    for f in sorted(data_dir.glob("deposits_*.json")):
        year = int(f.stem.split("_")[1])
        with open(f, "r", encoding="utf-8") as fh:
            deposits[year] = json.load(fh)

    partner_deposits = []
    for deps in deposits.values():
        for d in deps:
            if is_partner_deposit(d.get("source", "")):
                partner_deposits.append(d)

    income = {}
    for y, deps in deposits.items():
        by_type = {}
        for d in deps:
            itype = classify_income(d.get("category", ""), d.get("source", ""))
            by_type[itype] = by_type.get(itype, 0) + d["amount"]
        income[y] = {k: round(v, 2) for k, v in by_type.items()}

    flows = {}
    flows_file = data_dir / "account_flows.json"
    if flows_file.exists():
        with open(flows_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
            flows = {int(k): v for k, v in raw.items()}

    balances = None
    balances_file = data_dir / "balances.json"
    if balances_file.exists():
        with open(balances_file, "r", encoding="utf-8") as f:
            balances = json.load(f)

    return {
        "withdrawals": withdrawals, "deposits": deposits,
        "partner_deposits": partner_deposits, "income": income,
        "flows": flows, "balances": balances,
        "years": sorted(withdrawals.keys()),
    }


if __name__ == "__main__":
    main()
