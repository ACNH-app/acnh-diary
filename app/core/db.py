from __future__ import annotations

import sqlite3

from app.core.config import get_db_path

VILLAGER_STATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS villager_state (
    villager_id TEXT PRIMARY KEY,
    liked INTEGER NOT NULL DEFAULT 0,
    on_island INTEGER NOT NULL DEFAULT 0,
    former_resident INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

CATALOG_STATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS catalog_state (
    catalog_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    owned INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (catalog_type, item_id)
)
"""

CATALOG_VARIATION_STATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS catalog_variation_state (
    catalog_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    variation_id TEXT NOT NULL,
    owned INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (catalog_type, item_id, variation_id)
)
"""


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_villager_state(conn: sqlite3.Connection) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='villager_state'"
    ).fetchone()

    if not exists:
        conn.execute(VILLAGER_STATE_TABLE_SQL)
        return

    info = conn.execute("PRAGMA table_info(villager_state)").fetchall()
    villager_col = next((r for r in info if r["name"] == "villager_id"), None)
    villager_type = (villager_col["type"] if villager_col else "").upper()

    if "TEXT" in villager_type:
        column_names = {str(r["name"]) for r in info}
        if "former_resident" not in column_names:
            conn.execute(
                "ALTER TABLE villager_state ADD COLUMN former_resident INTEGER NOT NULL DEFAULT 0"
            )
        return

    conn.execute("ALTER TABLE villager_state RENAME TO villager_state_old")
    conn.execute(VILLAGER_STATE_TABLE_SQL)
    conn.execute(
        """
        INSERT INTO villager_state (villager_id, liked, on_island, former_resident, updated_at)
        SELECT CAST(villager_id AS TEXT), COALESCE(liked, 0), COALESCE(on_island, 0),
               0,
               COALESCE(updated_at, CURRENT_TIMESTAMP)
        FROM villager_state_old
        """
    )
    conn.execute("DROP TABLE villager_state_old")


def _migrate_clothing_state(conn: sqlite3.Connection) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='clothing_state'"
    ).fetchone()
    if not exists:
        return

    conn.execute(
        """
        INSERT OR IGNORE INTO catalog_state (catalog_type, item_id, owned, updated_at)
        SELECT 'clothing', CAST(item_id AS TEXT), COALESCE(owned, 0), COALESCE(updated_at, CURRENT_TIMESTAMP)
        FROM clothing_state
        """
    )


def init_db() -> None:
    with get_db() as conn:
        _migrate_villager_state(conn)
        conn.execute(CATALOG_STATE_TABLE_SQL)
        conn.execute(CATALOG_VARIATION_STATE_TABLE_SQL)
        _migrate_clothing_state(conn)
