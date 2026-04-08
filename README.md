# Prismfly

**Decompose your spending, track your real purchasing power.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Firefly III](https://img.shields.io/badge/Firefly%20III-6.x-orange.svg)](https://www.firefly-iii.org/)
[![Plotly.js](https://img.shields.io/badge/charts-Plotly.js-3F4F75.svg)](https://plotly.com/javascript/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Cross-analysis of [Firefly III](https://www.firefly-iii.org/) transaction data with tax return records to track real purchasing power evolution, personal inflation vs official CPI, and lifestyle inflation dynamics.

## Features

- **Personal Inflation Index (ICVP)**: tracks how your cost of living evolves relative to a base year, compared against official CPI
- **Lifestyle inflation elasticity**: measures whether discretionary spending grows faster or slower than income
- **Account-based savings tracking**: net flow in main accounts as the most reliable savings metric
- **Investment sustainability waterfall**: monthly cascade from salary through needs, investment, and discretionary spending to free margin
- **Interactive Plotly.js dashboard**: 11 charts with zoom, pan, hover, legend toggle, range sliders, and stacked/grouped modes
- **Markdown report**: raw analytical data exportable for LLM-assisted analysis
- **Shared expenses support**: optional partner reimbursement tracking via Settle Up or similar
- **Capital expenditure filtering**: automatic exclusion via Firefly tags or description keywords

## Requirements

- [uv](https://docs.astral.sh/uv/)
- Firefly III instance accessible on your network
- `.env` file with `FIREFLY_URL` and `FIREFLY_TOKEN`
- `personal.json` with your tax data and account structure (see `personal.example.json`)

## Usage

```bash
# Fetch latest data from Firefly III and generate dashboard + report
uv run main.py

# Regenerate outputs from cached data only (no network)
uv run main.py --no-fetch

# Force re-download of all years (not just current)
uv run main.py --force
```

**Outputs:**
- `dashboard.html` — interactive dashboard, open in any browser
- `dashboard.md` — raw metrics in markdown, for LLM analysis or external tools

For LLM-assisted discussion, provide both `dashboard.md` and `CONTEXTO.md` (your manually maintained narrative context).

## Project Structure

```
├── main.py               # CLI entry point
├── src/
│   ├── config.py         # Loads personal.json + public data (CPI)
│   ├── firefly.py        # Firefly III API client (read-only)
│   ├── extract.py        # Data extraction, pagination, and caching
│   ├── analyze.py        # Basket classification, ICVP, elasticity, waterfall
│   ├── dashboard.py      # Plotly.js HTML generation
│   └── report.py         # Markdown report generation
├── personal.json         # Your tax data, accounts, filters (gitignored)
├── personal.example.json # Template for personal.json
├── CONTEXTO.md           # Narrative context for LLM analysis (manual, gitignored)
├── data/                 # Cached JSON (auto-generated, gitignored)
├── .env                  # API URL and token (gitignored)
├── dashboard.html        # Generated dashboard (gitignored)
└── dashboard.md          # Generated report (gitignored)
```

## Configuration

All personal data lives in `personal.json` (gitignored). See `personal.example.json` for the full schema. Key sections:

| Section | Purpose |
|---|---|
| `tax_data` | Annual gross/net salary by year |
| `salary_sources` | Employer names for income classification |
| `main_accounts` | Firefly account names + IDs for savings tracking |
| `partner_*` | Shared expense reimbursement config (optional) |
| `basket_map` | Firefly category → analytical basket mapping |
| `capital_tags` / `capital_keywords` | Capital expenditure detection |
| `renovation_tags` | One-off renovation exclusion from sustainability waterfall |
| `shield_accounts` / `investment_accounts` / `other_accounts` | Financial snapshot for the report |

## Dashboard

11 interactive charts (Plotly.js):

1. **Quarterly spending** — needs / discretionary / other, with stacked/grouped toggle
2. **Monthly explorer by basket** — range slider, stacked/grouped/100% modes
3. **ICVP vs CPI** — personal inflation vs official index
4. **Elasticity scatter** — income variation vs discretionary spending variation
5. **Heatmap** — average monthly spend by basket and year
6. **Distribution (%)** — spending composition by basket
7. **Dining & leisure** — EUR/month and % of salary (lifestyle inflation indicator)
8. **Monthly savings rate** — with 3-month moving average
9. **Main accounts delta** — annual net flow
10. **Income composition** — salary, reimbursements, inheritance, other
11. **Sustainability waterfall** — full per-basket breakdown from salary to free margin

## Caching

Transaction data is cached as JSON in `data/`. Closed years are never re-fetched unless `--force` is used. The current year is always refreshed. Account balances are refreshed on every fetch run.

## Maintenance

### Tax data
Update `personal.json` with each new tax year. Update `IPC_ACUM` / `IPC_INTER` in `config.py` with official CPI data.

### Categories and filters
- Subscription reclassification: `subs_education` / `subs_technology` in `personal.json`
- Renovation one-offs: tag transactions in Firefly with the tags listed in `renovation_tags`
- Capital expenditures: tag with `capital_tags` or add description keywords to `capital_keywords`

### Narrative context
Update `CONTEXTO.md` when personal circumstances, investment strategy, or major financial events change.

## License

[MIT](LICENSE)
