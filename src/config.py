"""Analysis constants.

Personal data and Firefly III-specific configuration are loaded
from personal.json (gitignored). This file only contains public
data (CPI) and the basket/color structure.
"""
import json
from pathlib import Path


def _get(d, *keys, default=None):
    """Try multiple keys in order (for backwards compat), return first found."""
    for k in keys:
        if k in d:
            return d[k]
    return default


# ── Personal data (from personal.json) ───────────────────────────
_personal_path = Path(__file__).resolve().parent.parent / "personal.json"
if not _personal_path.exists():
    raise FileNotFoundError(
        f"Cannot find {_personal_path}. "
        "Create personal.json from personal.example.json."
    )

with open(_personal_path, "r", encoding="utf-8") as _f:
    _personal = json.load(_f)

# Tax / fiscal data
_tax = _get(_personal, "tax_data", "fiscal", default={})
FISCAL = {}
for k, v in _tax.items():
    FISCAL[int(k)] = {
        "neto": v.get("net", v.get("neto", 0)),
        "bruto": v.get("gross", v.get("bruto", 0)),
    }

SALARY_SOURCES = set(_personal.get("salary_sources", []))
SALARY_CATS = set(_personal.get("salary_categories", []))

# Accounts
MAIN_ACCOUNTS = {k: int(v) for k, v in _personal.get("main_accounts", {}).items()}
MAIN_ACCOUNTS_LABEL = " + ".join(MAIN_ACCOUNTS.keys()) or "Main accounts"
ESCUDO_ACCOUNTS = _get(_personal, "shield_accounts", "escudo_accounts", default={})
INVESTMENT_ACCOUNTS = _personal.get("investment_accounts", {})
OTHER_ACCOUNTS = _personal.get("other_accounts", {})

# Partner / shared expenses (all optional)
PARTNER_NAME = _personal.get("partner_name", "")
PARTNER_SOURCE_PATTERN = _personal.get("partner_source_pattern", "")
PARTNER_CATEGORIES = set(_personal.get("partner_categories", []))

# Income classification
INCOME_INVESTMENT_SOURCES = set(_personal.get("income_investment_sources", []))
INCOME_INVESTMENT_CATS = set(_get(_personal, "income_investment_categories", "investment_categories", default=[]))
INCOME_HERITAGE_KEYWORDS = set(_personal.get("income_heritage_keywords", []))
INCOME_TAX_RETURN_SOURCES = set(_personal.get("income_tax_return_sources", []))

# Firefly categories excluded from expense analysis
EXCLUDE_CATS = set(_personal.get("exclude_categories", []))

# Capital expenditure detection
CAPITAL_TAGS = set(_personal.get("capital_tags", []))
CAPITAL_KEYWORDS = list(_personal.get("capital_keywords", []))
CAPITAL_DESTINATIONS = _personal.get("capital_destinations", {})

# Renovation tags (excluded from waterfall)
RENOVATION_TAGS = set(_personal.get("renovation_tags", []))

# Subscription reclassification
SUBSCRIPTION_CATEGORY = _personal.get("subscription_category", "")
SUBS_EDUCATION = set(_get(_personal, "subs_education", "subs_formacion", default=[]))
SUBS_TECHNOLOGY = set(_get(_personal, "subs_technology", "subs_tecnologia", default=[]))

# Firefly category -> basket mapping
BASKET_MAP = _get(_personal, "basket_map", "cesta_map", default={})

# ── Public data (CPI, INE Spain) ─────────────────────────────────
IPC_ACUM = {
    2017: 1.000, 2018: 1.012, 2019: 1.020, 2020: 1.015,
    2021: 1.081, 2022: 1.143, 2023: 1.178, 2024: 1.211,
    2025: 1.246, 2026: 1.277,
}

IPC_INTER = {
    2017: 1.1, 2018: 1.2, 2019: 0.8, 2020: -0.5,
    2021: 6.5, 2022: 5.7, 2023: 3.1, 2024: 2.8,
    2025: 2.9, 2026: 2.5,
}

# ── Analytical baskets ───────────────────────────────────────────
BASKETS_NEC = {"Housing", "Food", "Public transport", "Motor", "Health"}
BASKETS_DISC = {"Dining & leisure", "Clothing & personal care", "Travel", "Gaming"}

BASKETS_ORDER = [
    "Housing", "Food", "Public transport", "Motor", "Health",
    "Dining & leisure", "Clothing & personal care",
    "Education", "Technology", "Gaming", "Travel",
    "Gifts & donations",
    "Home repairs", "Admin & taxes", "Investments", "Other",
]

COLORS = [
    "#2563eb", "#16a34a", "#0891b2", "#d97706", "#dc2626",
    "#9333ea", "#ec4899", "#06b6d4", "#4f46e5", "#65a30d",
    "#ea580c", "#a855f7", "#b45309", "#64748b", "#0d9488", "#94a3b8",
]
