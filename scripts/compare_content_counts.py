from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import CATALOG_TYPES, get_content_db_path
from app.services.catalog_data import _catalog_row_index, load_catalog, load_villagers


def _load_counts_from_source() -> tuple[dict[str, int], dict[str, int], int]:
    prev = os.environ.get("USE_CONTENT_DB")
    os.environ["USE_CONTENT_DB"] = "0"
    for fn in (load_catalog, _catalog_row_index, load_villagers):
        try:
            fn.cache_clear()  # type: ignore[attr-defined]
        except Exception:
            pass
    try:
        item_counts: dict[str, int] = {}
        variation_counts: dict[str, int] = {}
        for catalog_type in CATALOG_TYPES.keys():
            items = load_catalog(catalog_type)
            rows = _catalog_row_index(catalog_type)
            item_counts[catalog_type] = len(items)
            variation_counts[catalog_type] = sum(
                len(v) if isinstance(v, list) else 0
                for v in (r.get("variations") for r in rows.values() if isinstance(r, dict))
            )
        villager_count = len(load_villagers())
        return item_counts, variation_counts, villager_count
    finally:
        if prev is None:
            os.environ.pop("USE_CONTENT_DB", None)
        else:
            os.environ["USE_CONTENT_DB"] = prev
        for fn in (load_catalog, _catalog_row_index, load_villagers):
            try:
                fn.cache_clear()  # type: ignore[attr-defined]
            except Exception:
                pass


def _load_counts_from_db() -> tuple[dict[str, int], dict[str, int], int]:
    conn = sqlite3.connect(get_content_db_path())
    try:
        item_counts = {
            str(r[0]): int(r[1])
            for r in conn.execute(
                "SELECT catalog_type, COUNT(*) FROM catalog_items GROUP BY catalog_type"
            ).fetchall()
        }
        variation_counts = {
            str(r[0]): int(r[1])
            for r in conn.execute(
                "SELECT catalog_type, COUNT(*) FROM catalog_variations GROUP BY catalog_type"
            ).fetchall()
        }
        villager_count = int(conn.execute("SELECT COUNT(*) FROM villagers").fetchone()[0])
        return item_counts, variation_counts, villager_count
    finally:
        conn.close()


def main() -> int:
    if not get_content_db_path().exists():
        print(f"ERROR: content.db 없음: {get_content_db_path()}")
        return 1

    src_items, src_vars, src_villagers = _load_counts_from_source()
    db_items, db_vars, db_villagers = _load_counts_from_db()

    has_diff = False
    print("== Catalog item counts ==")
    for ctype in CATALOG_TYPES.keys():
        s = src_items.get(ctype, 0)
        d = db_items.get(ctype, 0)
        ok = "OK" if s == d else "DIFF"
        if ok == "DIFF":
            has_diff = True
        print(f"{ctype:16} source={s:5d} db={d:5d} [{ok}]")

    print("\n== Catalog variation counts ==")
    for ctype in CATALOG_TYPES.keys():
        s = src_vars.get(ctype, 0)
        d = db_vars.get(ctype, 0)
        ok = "OK" if s == d else "DIFF"
        if ok == "DIFF":
            has_diff = True
        print(f"{ctype:16} source={s:5d} db={d:5d} [{ok}]")

    ok = "OK" if src_villagers == db_villagers else "DIFF"
    if ok == "DIFF":
        has_diff = True
    print("\n== Villagers ==")
    print(f"villagers         source={src_villagers:5d} db={db_villagers:5d} [{ok}]")

    return 2 if has_diff else 0


if __name__ == "__main__":
    raise SystemExit(main())
