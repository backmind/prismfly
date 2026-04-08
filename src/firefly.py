"""Firefly III API client (read-only)."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = os.environ.get("FIREFLY_URL", "http://localhost:8080").rstrip("/") + "/api/v1"


def _headers():
    token = os.environ["FIREFLY_TOKEN"]
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def fetch_all(endpoint: str, params: dict | None = None) -> list[dict]:
    """Fully paginate an endpoint and return all items."""
    params = dict(params or {})
    params.setdefault("limit", 100)
    page, results = 1, []
    while True:
        params["page"] = page
        r = requests.get(f"{BASE}{endpoint}", headers=_headers(), params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        results.extend(data["data"])
        if page >= data["meta"]["pagination"]["total_pages"]:
            break
        page += 1
    return results


def check_connection() -> str:
    """Verify connection and return the Firefly III version."""
    r = requests.get(f"{BASE}/about", headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()["data"]["version"]
