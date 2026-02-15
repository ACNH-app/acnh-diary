from __future__ import annotations

import sqlite3

from app.core.config import get_db_path

VILLAGER_STATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS villager_state (
    villager_id TEXT PRIMARY KEY,
    liked INTEGER NOT NULL DEFAULT 0,
    on_island INTEGER NOT NULL DEFAULT 0,
    former_resident INTEGER NOT NULL DEFAULT 0,
    island_order INTEGER NOT NULL DEFAULT 0,
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

ISLAND_PROFILE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS island_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    island_name TEXT NOT NULL DEFAULT '',
    nickname TEXT NOT NULL DEFAULT '',
    representative_fruit TEXT NOT NULL DEFAULT '',
    representative_flower TEXT NOT NULL DEFAULT '',
    birthday TEXT NOT NULL DEFAULT '',
    hemisphere TEXT NOT NULL DEFAULT 'north',
    time_travel_enabled INTEGER NOT NULL DEFAULT 0,
    game_datetime TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

CALENDAR_ENTRY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS calendar_entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_date TEXT NOT NULL,
    npc_name TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    checked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

PLAYER_PROFILE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT '',
    birthday TEXT NOT NULL DEFAULT '',
    is_main INTEGER NOT NULL DEFAULT 0,
    is_sub INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
        if "island_order" not in column_names:
            conn.execute(
                "ALTER TABLE villager_state ADD COLUMN island_order INTEGER NOT NULL DEFAULT 0"
            )
        return

    conn.execute("ALTER TABLE villager_state RENAME TO villager_state_old")
    conn.execute(VILLAGER_STATE_TABLE_SQL)
    conn.execute(
        """
        INSERT INTO villager_state (villager_id, liked, on_island, former_resident, island_order, updated_at)
        SELECT CAST(villager_id AS TEXT), COALESCE(liked, 0), COALESCE(on_island, 0),
               0,
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


def _migrate_island_profile(conn: sqlite3.Connection) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='island_profile'"
    ).fetchone()
    if not exists:
        conn.execute(ISLAND_PROFILE_TABLE_SQL)
        conn.execute("INSERT OR IGNORE INTO island_profile (id) VALUES (1)")
        return

    info = conn.execute("PRAGMA table_info(island_profile)").fetchall()
    cols = {str(r["name"]) for r in info}
    if "hemisphere" not in cols:
        conn.execute(
            "ALTER TABLE island_profile ADD COLUMN hemisphere TEXT NOT NULL DEFAULT 'north'"
        )
    if "birthday" not in cols:
        conn.execute(
            "ALTER TABLE island_profile ADD COLUMN birthday TEXT NOT NULL DEFAULT ''"
        )
    if "time_travel_enabled" not in cols:
        conn.execute(
            "ALTER TABLE island_profile ADD COLUMN time_travel_enabled INTEGER NOT NULL DEFAULT 0"
        )
    if "game_datetime" not in cols:
        conn.execute(
            "ALTER TABLE island_profile ADD COLUMN game_datetime TEXT NOT NULL DEFAULT ''"
        )
    conn.execute("INSERT OR IGNORE INTO island_profile (id) VALUES (1)")


def _migrate_calendar_entry(conn: sqlite3.Connection) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='calendar_entry'"
    ).fetchone()
    if not exists:
        conn.execute(CALENDAR_ENTRY_TABLE_SQL)
        return

    # 과거 스키마의 UNIQUE(visit_date, npc_name)를 제거한다.
    # (같은 날짜 동일 NPC 중복 방문 기록 허용)
    has_unique_pair = False
    for idx in conn.execute("PRAGMA index_list(calendar_entry)").fetchall():
        if not int(idx["unique"]):
            continue
        idx_name = str(idx["name"])
        cols = conn.execute(f"PRAGMA index_info('{idx_name}')").fetchall()
        col_names = [str(c["name"]) for c in cols]
        if col_names == ["visit_date", "npc_name"]:
            has_unique_pair = True
            break
    if not has_unique_pair:
        conn.execute(CALENDAR_ENTRY_TABLE_SQL)
        return

    conn.execute("ALTER TABLE calendar_entry RENAME TO calendar_entry_old")
    conn.execute(CALENDAR_ENTRY_TABLE_SQL)
    conn.execute(
        """
        INSERT INTO calendar_entry (id, visit_date, npc_name, note, checked, created_at, updated_at)
        SELECT id, visit_date, npc_name, COALESCE(note, ''), COALESCE(checked, 0),
               COALESCE(created_at, CURRENT_TIMESTAMP), COALESCE(updated_at, CURRENT_TIMESTAMP)
        FROM calendar_entry_old
        ORDER BY id ASC
        """
    )
    conn.execute("DROP TABLE calendar_entry_old")


def _migrate_player_profile(conn: sqlite3.Connection) -> None:
    conn.execute(PLAYER_PROFILE_TABLE_SQL)


def init_db() -> None:
    with get_db() as conn:
        _migrate_villager_state(conn)
        conn.execute(CATALOG_STATE_TABLE_SQL)
        conn.execute(CATALOG_VARIATION_STATE_TABLE_SQL)
        _migrate_clothing_state(conn)
        _migrate_island_profile(conn)
        _migrate_calendar_entry(conn)
        _migrate_player_profile(conn)
