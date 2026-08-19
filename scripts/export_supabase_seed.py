from __future__ import annotations

import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DB_PATH = BASE_DIR / "app.db"
CONTENT_DB_PATH = BASE_DIR / "content.db"
OUT_DIR = BASE_DIR / "tmp" / "supabase_seed"

APP_TABLES = (
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


def _table_rows(conn: sqlite3.Connection, table: str) -> list[dict[str, object]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    return [{k: row[k] for k in row.keys()} for row in rows]


def _existing_tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {str(row[0]) for row in rows}


def _dump_db(db_path: Path, tables: tuple[str, ...], out_dir: Path) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    if not db_path.exists() or db_path.stat().st_size <= 0:
        for table in tables:
            counts[table] = 0
            (out_dir / f"{table}.json").write_text("[]\n", encoding="utf-8")
        return counts
    with sqlite3.connect(db_path) as conn:
        existing = _existing_tables(conn)
        for table in tables:
            if table not in existing:
                counts[table] = 0
                (out_dir / f"{table}.json").write_text("[]\n", encoding="utf-8")
                continue
            rows = _table_rows(conn, table)
            counts[table] = len(rows)
            (out_dir / f"{table}.json").write_text(
                json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    return counts


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "app_db": _dump_db(APP_DB_PATH, APP_TABLES, OUT_DIR / "app_db"),
        "content_db": _dump_db(CONTENT_DB_PATH, CONTENT_TABLES, OUT_DIR / "content_db"),
    }
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"seed_dir={OUT_DIR}")
    for db_name, counts in summary.items():
        for table, count in counts.items():
            print(f"{db_name}.{table}={count}")


if __name__ == "__main__":
    main()
