from __future__ import annotations

import sqlite3
from threading import Lock

from app.core.config import get_db_path, get_state_backend, is_running_on_vercel
from app.services.supabase_state import is_supabase_state_available

_INIT_LOCK = Lock()
_INIT_DONE = False

ISLAND_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS island (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

VILLAGER_STATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS villager_state (
    island_id INTEGER NOT NULL,
    villager_id TEXT NOT NULL,
    liked INTEGER NOT NULL DEFAULT 0,
    on_island INTEGER NOT NULL DEFAULT 0,
    camping_visited INTEGER NOT NULL DEFAULT 0,
    former_resident INTEGER NOT NULL DEFAULT 0,
    island_order INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (island_id, villager_id)
)
"""

CATALOG_STATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS catalog_state (
    island_id INTEGER NOT NULL,
    catalog_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    owned INTEGER NOT NULL DEFAULT 0,
    donated INTEGER NOT NULL DEFAULT 0,
    quantity INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (island_id, catalog_type, item_id)
)
"""

CATALOG_VARIATION_STATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS catalog_variation_state (
    island_id INTEGER NOT NULL,
    catalog_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    variation_id TEXT NOT NULL,
    owned INTEGER NOT NULL DEFAULT 0,
    quantity INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (island_id, catalog_type, item_id, variation_id)
)
"""

ISLAND_PROFILE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS island_profile (
    island_id INTEGER PRIMARY KEY,
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
    island_id INTEGER NOT NULL,
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
    island_id INTEGER NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    birthday TEXT NOT NULL DEFAULT '',
    is_main INTEGER NOT NULL DEFAULT 0,
    is_sub INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def get_db() -> sqlite3.Connection:
    if _use_supabase_state_mode():
        raise RuntimeError("SQLite state DB is disabled when STATE_BACKEND uses Supabase")
    conn = sqlite3.connect(get_db_path(), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL" if not is_running_on_vercel() else "PRAGMA journal_mode = DELETE")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _ensure_default_island(conn: sqlite3.Connection) -> None:
    conn.execute(ISLAND_TABLE_SQL)
    row = conn.execute("SELECT id FROM island WHERE id = 1").fetchone()
    if row:
        return
    profile_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='island_profile'"
    ).fetchone()
    island_name = "Default Island"
    if profile_exists:
        cols = _column_names(conn, "island_profile")
        if "island_name" in cols:
            profile_row = conn.execute(
                "SELECT island_name FROM island_profile ORDER BY ROWID ASC LIMIT 1"
            ).fetchone()
            if profile_row and str(profile_row["island_name"] or "").strip():
                island_name = str(profile_row["island_name"]).strip()
    conn.execute(
        "INSERT INTO island (id, name) VALUES (1, ?)",
        (island_name,),
    )


def _migrate_islands(conn: sqlite3.Connection) -> None:
    conn.execute(ISLAND_TABLE_SQL)
    _ensure_default_island(conn)


def _migrate_villager_state(conn: sqlite3.Connection) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='villager_state'"
    ).fetchone()
    if not exists:
        conn.execute(VILLAGER_STATE_TABLE_SQL)
        return

    cols = _column_names(conn, "villager_state")
    info = conn.execute("PRAGMA table_info(villager_state)").fetchall()
    pk_cols = [str(row["name"]) for row in info if int(row["pk"] or 0) > 0]
    villager_col = next((r for r in info if r["name"] == "villager_id"), None)
    villager_type = str(villager_col["type"] or "").upper() if villager_col else ""
    legacy_int_id = "TEXT" not in villager_type
    needs_rebuild = legacy_int_id or "island_id" not in cols or pk_cols != ["island_id", "villager_id"]

    if not needs_rebuild:
        for sql in [
            "ALTER TABLE villager_state ADD COLUMN camping_visited INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE villager_state ADD COLUMN former_resident INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE villager_state ADD COLUMN island_order INTEGER NOT NULL DEFAULT 0",
        ]:
            col = sql.split(" ADD COLUMN ", 1)[1].split(" ", 1)[0]
            if col not in cols:
                conn.execute(sql)
        return

    conn.execute("ALTER TABLE villager_state RENAME TO villager_state_old")
    conn.execute(VILLAGER_STATE_TABLE_SQL)
    old_cols = _column_names(conn, "villager_state_old")
    villager_id_expr = "CAST(villager_id AS TEXT)" if legacy_int_id else "villager_id"
    island_id_expr = "COALESCE(island_id, 1)" if "island_id" in old_cols else "1"
    camping_expr = "COALESCE(camping_visited, 0)" if "camping_visited" in old_cols else "0"
    former_expr = "COALESCE(former_resident, 0)" if "former_resident" in old_cols else "0"
    order_expr = "COALESCE(island_order, 0)" if "island_order" in old_cols else "0"
    conn.execute(
        f"""
        INSERT INTO villager_state (
            island_id, villager_id, liked, on_island, camping_visited, former_resident, island_order, updated_at
        )
        SELECT
            {island_id_expr},
            {villager_id_expr},
            COALESCE(liked, 0),
            COALESCE(on_island, 0),
            {camping_expr},
            {former_expr},
            {order_expr},
            COALESCE(updated_at, CURRENT_TIMESTAMP)
        FROM villager_state_old
        """
    )
    conn.execute("DROP TABLE villager_state_old")


def _migrate_catalog_state(conn: sqlite3.Connection) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='catalog_state'"
    ).fetchone()
    if not exists:
        conn.execute(CATALOG_STATE_TABLE_SQL)
    else:
        cols = _column_names(conn, "catalog_state")
        info = conn.execute("PRAGMA table_info(catalog_state)").fetchall()
        pk_cols = [str(row["name"]) for row in info if int(row["pk"] or 0) > 0]
        needs_rebuild = "island_id" not in cols or pk_cols != ["island_id", "catalog_type", "item_id"]
        if needs_rebuild:
            conn.execute("ALTER TABLE catalog_state RENAME TO catalog_state_old")
            conn.execute(CATALOG_STATE_TABLE_SQL)
            old_cols = _column_names(conn, "catalog_state_old")
            island_id_expr = "COALESCE(island_id, 1)" if "island_id" in old_cols else "1"
            donated_expr = "COALESCE(donated, 0)" if "donated" in old_cols else "0"
            quantity_expr = "COALESCE(quantity, 0)" if "quantity" in old_cols else "0"
            conn.execute(
                f"""
                INSERT INTO catalog_state (
                    island_id, catalog_type, item_id, owned, donated, quantity, updated_at
                )
                SELECT
                    {island_id_expr},
                    catalog_type,
                    item_id,
                    COALESCE(owned, 0),
                    {donated_expr},
                    {quantity_expr},
                    COALESCE(updated_at, CURRENT_TIMESTAMP)
                FROM catalog_state_old
                """
            )
            conn.execute("DROP TABLE catalog_state_old")
        else:
            if "donated" not in cols:
                conn.execute(
                    "ALTER TABLE catalog_state ADD COLUMN donated INTEGER NOT NULL DEFAULT 0"
                )
            if "quantity" not in cols:
                conn.execute(
                    "ALTER TABLE catalog_state ADD COLUMN quantity INTEGER NOT NULL DEFAULT 0"
                )

    vexists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='catalog_variation_state'"
    ).fetchone()
    if not vexists:
        conn.execute(CATALOG_VARIATION_STATE_TABLE_SQL)
        return

    cols = _column_names(conn, "catalog_variation_state")
    info = conn.execute("PRAGMA table_info(catalog_variation_state)").fetchall()
    pk_cols = [str(row["name"]) for row in info if int(row["pk"] or 0) > 0]
    needs_rebuild = "island_id" not in cols or pk_cols != [
        "island_id",
        "catalog_type",
        "item_id",
        "variation_id",
    ]
    if needs_rebuild:
        conn.execute("ALTER TABLE catalog_variation_state RENAME TO catalog_variation_state_old")
        conn.execute(CATALOG_VARIATION_STATE_TABLE_SQL)
        old_cols = _column_names(conn, "catalog_variation_state_old")
        island_id_expr = "COALESCE(island_id, 1)" if "island_id" in old_cols else "1"
        quantity_expr = "COALESCE(quantity, 0)" if "quantity" in old_cols else "0"
        conn.execute(
            f"""
            INSERT INTO catalog_variation_state (
                island_id, catalog_type, item_id, variation_id, owned, quantity, updated_at
            )
            SELECT
                {island_id_expr},
                catalog_type,
                item_id,
                variation_id,
                COALESCE(owned, 0),
                {quantity_expr},
                COALESCE(updated_at, CURRENT_TIMESTAMP)
            FROM catalog_variation_state_old
            """
        )
        conn.execute("DROP TABLE catalog_variation_state_old")
    elif "quantity" not in cols:
        conn.execute(
            "ALTER TABLE catalog_variation_state ADD COLUMN quantity INTEGER NOT NULL DEFAULT 0"
        )


def _migrate_clothing_state(conn: sqlite3.Connection) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='clothing_state'"
    ).fetchone()
    if not exists:
        return
    conn.execute(
        """
        INSERT OR IGNORE INTO catalog_state (island_id, catalog_type, item_id, owned, updated_at)
        SELECT 1, 'clothing', CAST(item_id AS TEXT), COALESCE(owned, 0), COALESCE(updated_at, CURRENT_TIMESTAMP)
        FROM clothing_state
        """
    )


def _migrate_island_profile(conn: sqlite3.Connection) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='island_profile'"
    ).fetchone()
    if not exists:
        conn.execute(ISLAND_PROFILE_TABLE_SQL)
        conn.execute("INSERT OR IGNORE INTO island_profile (island_id) VALUES (1)")
        return

    cols = _column_names(conn, "island_profile")
    info = conn.execute("PRAGMA table_info(island_profile)").fetchall()
    pk_cols = [str(row["name"]) for row in info if int(row["pk"] or 0) > 0]
    needs_rebuild = "island_id" not in cols or pk_cols != ["island_id"]
    if not needs_rebuild:
        for sql in [
            "ALTER TABLE island_profile ADD COLUMN birthday TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE island_profile ADD COLUMN hemisphere TEXT NOT NULL DEFAULT 'north'",
            "ALTER TABLE island_profile ADD COLUMN time_travel_enabled INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE island_profile ADD COLUMN game_datetime TEXT NOT NULL DEFAULT ''",
        ]:
            col = sql.split(" ADD COLUMN ", 1)[1].split(" ", 1)[0]
            if col not in cols:
                conn.execute(sql)
        conn.execute("INSERT OR IGNORE INTO island_profile (island_id) VALUES (1)")
        return

    conn.execute("ALTER TABLE island_profile RENAME TO island_profile_old")
    conn.execute(ISLAND_PROFILE_TABLE_SQL)
    old_cols = _column_names(conn, "island_profile_old")
    island_id_expr = "COALESCE(island_id, id, 1)"
    hemi_expr = "COALESCE(hemisphere, 'north')" if "hemisphere" in old_cols else "'north'"
    birthday_expr = "COALESCE(birthday, '')" if "birthday" in old_cols else "''"
    time_travel_expr = (
        "COALESCE(time_travel_enabled, 0)" if "time_travel_enabled" in old_cols else "0"
    )
    game_dt_expr = "COALESCE(game_datetime, '')" if "game_datetime" in old_cols else "''"
    conn.execute(
        f"""
        INSERT INTO island_profile (
            island_id, island_name, nickname, representative_fruit, representative_flower,
            birthday, hemisphere, time_travel_enabled, game_datetime, updated_at
        )
        SELECT
            {island_id_expr},
            COALESCE(island_name, ''),
            COALESCE(nickname, ''),
            COALESCE(representative_fruit, ''),
            COALESCE(representative_flower, ''),
            {birthday_expr},
            {hemi_expr},
            {time_travel_expr},
            {game_dt_expr},
            COALESCE(updated_at, CURRENT_TIMESTAMP)
        FROM island_profile_old
        """
    )
    conn.execute("DROP TABLE island_profile_old")
    conn.execute("INSERT OR IGNORE INTO island_profile (island_id) VALUES (1)")


def _migrate_calendar_entry(conn: sqlite3.Connection) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='calendar_entry'"
    ).fetchone()
    if not exists:
        conn.execute(CALENDAR_ENTRY_TABLE_SQL)
        return

    cols = _column_names(conn, "calendar_entry")
    needs_rebuild = "island_id" not in cols
    has_unique_pair = False
    for idx in conn.execute("PRAGMA index_list(calendar_entry)").fetchall():
        if not int(idx["unique"]):
            continue
        idx_name = str(idx["name"])
        idx_cols = conn.execute(f"PRAGMA index_info('{idx_name}')").fetchall()
        col_names = [str(c["name"]) for c in idx_cols]
        if col_names == ["visit_date", "npc_name"]:
            has_unique_pair = True
            break
    if not needs_rebuild and not has_unique_pair:
        return

    conn.execute("ALTER TABLE calendar_entry RENAME TO calendar_entry_old")
    conn.execute(CALENDAR_ENTRY_TABLE_SQL)
    old_cols = _column_names(conn, "calendar_entry_old")
    island_id_expr = "COALESCE(island_id, 1)" if "island_id" in old_cols else "1"
    conn.execute(
        f"""
        INSERT INTO calendar_entry (
            id, island_id, visit_date, npc_name, note, checked, created_at, updated_at
        )
        SELECT
            id,
            {island_id_expr},
            visit_date,
            npc_name,
            COALESCE(note, ''),
            COALESCE(checked, 0),
            COALESCE(created_at, CURRENT_TIMESTAMP),
            COALESCE(updated_at, CURRENT_TIMESTAMP)
        FROM calendar_entry_old
        ORDER BY id ASC
        """
    )
    conn.execute("DROP TABLE calendar_entry_old")


def _migrate_player_profile(conn: sqlite3.Connection) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='player_profile'"
    ).fetchone()
    if not exists:
        conn.execute(PLAYER_PROFILE_TABLE_SQL)
        return

    cols = _column_names(conn, "player_profile")
    if "island_id" in cols:
        return

    conn.execute("ALTER TABLE player_profile RENAME TO player_profile_old")
    conn.execute(PLAYER_PROFILE_TABLE_SQL)
    conn.execute(
        """
        INSERT INTO player_profile (
            id, island_id, name, birthday, is_main, is_sub, created_at, updated_at
        )
        SELECT
            id,
            1,
            COALESCE(name, ''),
            COALESCE(birthday, ''),
            COALESCE(is_main, 0),
            COALESCE(is_sub, 0),
            COALESCE(created_at, CURRENT_TIMESTAMP),
            COALESCE(updated_at, CURRENT_TIMESTAMP)
        FROM player_profile_old
        ORDER BY id ASC
        """
    )
    conn.execute("DROP TABLE player_profile_old")


def init_db() -> None:
    if _use_supabase_state_mode():
        return
    global _INIT_DONE
    if _INIT_DONE:
        return

    with _INIT_LOCK:
        if _INIT_DONE:
            return
        with get_db() as conn:
            _migrate_islands(conn)
            _migrate_villager_state(conn)
            _migrate_catalog_state(conn)
            _migrate_clothing_state(conn)
            _migrate_island_profile(conn)
            _migrate_calendar_entry(conn)
            _migrate_player_profile(conn)
        _INIT_DONE = True


def _use_supabase_state_mode() -> bool:
    backend = get_state_backend()
    if backend == "sqlite":
        return False
    if backend == "supabase":
        return is_supabase_state_available()
    return is_supabase_state_available()
