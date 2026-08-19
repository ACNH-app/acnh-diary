from __future__ import annotations

import json
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.config import get_supabase_service_role_key, get_supabase_url

SEED_DIR = BASE_DIR / "tmp" / "supabase_seed"

STATE_TABLES = (
    "island",
    "island_profile",
    "villager_state",
    "catalog_state",
    "catalog_variation_state",
    "calendar_entry",
    "player_profile",
)

CONTENT_TABLES = (
    "catalog_items",
    "catalog_variations",
    "villagers",
    "catalog_meta",
    "content_version",
    "recipe_tags",
    "recipe_tag_links",
)

PK_MAP: dict[str, str] = {
    "island": "id",
    "island_profile": "island_id",
    "villager_state": "island_id,villager_id",
    "catalog_state": "island_id,catalog_type,item_id",
    "catalog_variation_state": "island_id,catalog_type,item_id,variation_id",
    "calendar_entry": "id",
    "player_profile": "id",
    "catalog_items": "catalog_type,item_id",
    "catalog_variations": "catalog_type,item_id,variation_id",
    "villagers": "villager_id",
    "catalog_meta": "catalog_type",
    "content_version": "key",
    "recipe_tags": "tag_key",
    "recipe_tag_links": "recipe_item_id,tag_key",
}

CHUNK_SIZE_MAP: dict[str, int] = {
    "catalog_items": 250,
    "catalog_variations": 250,
    "catalog_state": 500,
    "catalog_variation_state": 500,
    "villagers": 250,
}


def _seed_file(table: str) -> Path:
    if table in STATE_TABLES:
        return SEED_DIR / "app_db" / f"{table}.json"
    return SEED_DIR / "content_db" / f"{table}.json"


def _load_rows(table: str) -> list[dict[str, object]]:
    path = _seed_file(table)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise RuntimeError(f"seed file is not a list: {path}")
    return [row for row in payload if isinstance(row, dict)]


def _chunks(rows: list[dict[str, object]], size: int) -> list[list[dict[str, object]]]:
    if not rows:
        return []
    return [rows[i : i + size] for i in range(0, len(rows), size)]


def _postgrest_url(table: str) -> str:
    base = get_supabase_url().rstrip("/")
    return f"{base}/rest/v1/{quote(table, safe='')}"


def _upsert_rows(table: str, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    service_key = get_supabase_service_role_key().strip()
    base_url = get_supabase_url().strip()
    if not service_key or not base_url:
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    pk = PK_MAP[table]
    body = json.dumps(rows, ensure_ascii=False).encode("utf-8")
    req = Request(
        f"{_postgrest_url(table)}?on_conflict={quote(pk, safe=',')}",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
    )
    try:
        with urlopen(req, timeout=180):
            return
    except HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"upsert failed for {table}: {exc.code} {payload}") from exc


def _import_table(table: str) -> None:
    rows = _load_rows(table)
    if not rows:
        print(f"{table}: skipped (0 rows)")
        return
    chunk_size = CHUNK_SIZE_MAP.get(table, 1000)
    chunks = _chunks(rows, chunk_size)
    total = len(chunks)
    for idx, chunk in enumerate(chunks, start=1):
        _upsert_rows(table, chunk)
        print(f"{table}: {idx}/{total} chunks uploaded ({len(chunk)} rows)")


def main() -> None:
    if not SEED_DIR.exists():
        raise SystemExit(
            f"missing seed dir: {SEED_DIR}. run `python scripts/export_supabase_seed.py` first"
        )

    all_tables = (*STATE_TABLES, *CONTENT_TABLES)
    print(f"seed_dir={SEED_DIR}")
    print(f"tables={len(all_tables)}")
    for table in all_tables:
        _import_table(table)
    print("done")


if __name__ == "__main__":
    main()
