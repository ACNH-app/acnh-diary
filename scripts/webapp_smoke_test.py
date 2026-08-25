"""Read-only API smoke checks for the local web app.

Run from the repository root with:
    python scripts/webapp_smoke_test.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("STATE_BACKEND", "sqlite")
os.environ.setdefault("CONTENT_BACKEND", "sqlite")
os.environ.setdefault("ASSET_BACKEND", "local")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


def check(response, label: str) -> dict:
    if response.status_code != 200:
        raise SystemExit(f"{label} failed: HTTP {response.status_code} {response.text[:200]}")
    return response.json()


def main() -> None:
    with TestClient(app) as client:
        headers = {"X-Island-Id": "1"}
        islands = check(client.get("/api/islands"), "islands")
        check(client.get("/api/profile", headers=headers), "profile")
        check(client.get("/api/home/summary", headers=headers), "home summary")
        check(client.get("/api/home/creatures-now", headers=headers), "current creatures")
        catalog = check(client.get("/api/catalog/fish", headers=headers), "catalog")
        if catalog.get("items"):
            item_id = catalog["items"][0]["id"]
            detail = check(client.get(f"/api/catalog/fish/{item_id}/detail", headers=headers), "catalog detail")
            if not {"item", "summary", "variations"}.issubset(detail):
                raise SystemExit("catalog detail failed: missing required keys")
        villagers = check(client.get("/api/villagers", headers=headers), "villagers")
        meta = check(client.get("/api/meta"), "meta")
        if "subtypes" not in meta:
            raise SystemExit("meta failed: missing subtypes")
        check(client.get("/api/villagers?subtype=A", headers=headers), "villager subtype filter")
        check(client.get("/api/calendar/day?date=2026-08-24", headers=headers), "calendar day")

    print(
        "webapp smoke passed: "
        f"islands={len(islands)}, catalog={catalog.get('count', 0)}, "
        f"villagers={villagers.get('count', 0)}, subtypes={len(meta.get('subtypes', []))}"
    )


if __name__ == "__main__":
    main()
