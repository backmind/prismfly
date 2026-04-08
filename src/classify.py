"""Income classification logic (shared between extract and main)."""
from .config import (
    SALARY_SOURCES, SALARY_CATS, PARTNER_NAME, PARTNER_SOURCE_PATTERN,
    PARTNER_CATEGORIES, INCOME_INVESTMENT_SOURCES, INCOME_INVESTMENT_CATS,
    INCOME_HERITAGE_KEYWORDS, INCOME_TAX_RETURN_SOURCES,
)


def classify_income(cat: str, src: str) -> str:
    """Classify an income deposit into a type label."""
    if cat in SALARY_CATS or src in SALARY_SOURCES:
        return "Salary"
    if (PARTNER_SOURCE_PATTERN and PARTNER_SOURCE_PATTERN in src) or cat in PARTNER_CATEGORIES:
        return f"Reimbursement {PARTNER_NAME}" if PARTNER_NAME else "Reimbursements"
    if cat in INCOME_HERITAGE_KEYWORDS or src in INCOME_HERITAGE_KEYWORDS:
        return "Inheritance"
    if src in INCOME_TAX_RETURN_SOURCES:
        return "Tax refund"
    if cat in INCOME_INVESTMENT_CATS or src in INCOME_INVESTMENT_SOURCES:
        return "Investment return"
    return "Other income"


def is_partner_deposit(source: str) -> bool:
    """Check if a deposit is from the partner."""
    return bool(PARTNER_SOURCE_PATTERN and PARTNER_SOURCE_PATTERN in source)
