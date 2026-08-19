from __future__ import annotations

import re
import sqlite3
import time
from threading import Lock
from typing import Any

from app.core.config import get_state_backend
from app.core.db import get_db, init_db
from app.services.supabase_state import (
    delete_rows,
    fetch_rows,
    insert_row,
    is_supabase_state_available,
    patch_rows,
    upsert_rows,
)

_CACHE_LOCK = Lock()
_CATALOG_STATE_CACHE: dict[tuple[int, str], dict[str, dict[str, Any]]] = {}
_VARIATION_OWNED_COUNT_CACHE: dict[tuple[int, str], dict[str, int]] = {}
_VARIATION_QTY_TOTAL_CACHE: dict[tuple[int, str], dict[str, int]] = {}


def _clone_catalog_state_map(src: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {k: dict(v) for k, v in src.items()}


def invalidate_catalog_state_caches(catalog_type: str | None = None, island_id: int | None = None) -> None:
    with _CACHE_LOCK:
        if catalog_type is None and island_id is None:
            _CATALOG_STATE_CACHE.clear()
            _VARIATION_OWNED_COUNT_CACHE.clear()
            _VARIATION_QTY_TOTAL_CACHE.clear()
            return

        catalog_keys = list(_CATALOG_STATE_CACHE.keys())
        count_keys = list(_VARIATION_OWNED_COUNT_CACHE.keys())
        qty_keys = list(_VARIATION_QTY_TOTAL_CACHE.keys())

        for key in catalog_keys:
            if island_id is not None and key[0] != island_id:
                continue
            if catalog_type is not None and key[1] != catalog_type:
                continue
            _CATALOG_STATE_CACHE.pop(key, None)
        for key in count_keys:
            if island_id is not None and key[0] != island_id:
                continue
            if catalog_type is not None and key[1] != catalog_type:
                continue
            _VARIATION_OWNED_COUNT_CACHE.pop(key, None)
        for key in qty_keys:
            if island_id is not None and key[0] != island_id:
                continue
            if catalog_type is not None and key[1] != catalog_type:
                continue
            _VARIATION_QTY_TOTAL_CACHE.pop(key, None)


def _exec_with_retry(
    conn: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
    *,
    retries: int = 6,
    delay_sec: float = 0.03,
) -> sqlite3.Cursor:
    for attempt in range(retries + 1):
        try:
            return conn.execute(sql, params)
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower() or attempt >= retries:
                raise
            time.sleep(delay_sec * (attempt + 1))
    raise RuntimeError("unreachable")


def _executemany_with_retry(
    conn: sqlite3.Connection,
    sql: str,
    params_seq: list[tuple[Any, ...]],
    *,
    retries: int = 6,
    delay_sec: float = 0.03,
) -> sqlite3.Cursor:
    for attempt in range(retries + 1):
        try:
            return conn.executemany(sql, params_seq)
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower() or attempt >= retries:
                raise
            time.sleep(delay_sec * (attempt + 1))
    raise RuntimeError("unreachable")


def _normalize_month_day(value: str) -> str:
    src = str(value or "").strip()
    if not src:
        return ""

    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", src)
    if m:
        month = int(m.group(2))
        day = int(m.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{month:02d}-{day:02d}"

    m = re.match(r"^(\d{1,2})[-/.](\d{1,2})$", src)
    if m:
        month = int(m.group(1))
        day = int(m.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{month:02d}-{day:02d}"

    return ""


def _normalize_island_name(value: str) -> str:
    text = str(value or "").strip()
    return text if text else "New Island"


def list_islands() -> list[dict[str, Any]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT i.id, i.name, p.island_name
            FROM island i
            LEFT JOIN island_profile p ON p.island_id = i.id
            ORDER BY i.id ASC
            """
        ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        profile_name = str(row["island_name"] or "").strip()
        island_name = profile_name or str(row["name"] or "").strip() or f"Island {int(row['id'])}"
        items.append({"id": int(row["id"]), "name": island_name})
    return items


def create_island(name: str) -> dict[str, Any]:
    init_db()
    display_name = _normalize_island_name(name)
    with get_db() as conn:
        conn.execute("INSERT INTO island (name) VALUES (?)", (display_name,))
        row = conn.execute("SELECT id, name FROM island WHERE id = last_insert_rowid()").fetchone()
        if not row:
            raise RuntimeError("island create failed")
        island_id = int(row["id"])
        conn.execute(
            """
            INSERT OR IGNORE INTO island_profile (
                island_id, island_name, nickname, representative_fruit, representative_flower, birthday,
                hemisphere, time_travel_enabled, game_datetime
            ) VALUES (?, ?, '', '', '', '', 'north', 0, '')
            """,
            (island_id, display_name),
        )
    return {"id": island_id, "name": display_name}


def delete_island(island_id: int) -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        row = conn.execute("SELECT id, name FROM island WHERE id = ?", (island_id,)).fetchone()
        if not row:
            raise ValueError("island not found")
        count_row = conn.execute("SELECT COUNT(*) AS cnt FROM island").fetchone()
        island_count = int(count_row["cnt"] or 0) if count_row else 0
        if island_count <= 1:
            raise ValueError("cannot delete the last island")

        conn.execute("DELETE FROM villager_state WHERE island_id = ?", (island_id,))
        conn.execute("DELETE FROM catalog_variation_state WHERE island_id = ?", (island_id,))
        conn.execute("DELETE FROM catalog_state WHERE island_id = ?", (island_id,))
        conn.execute("DELETE FROM calendar_entry WHERE island_id = ?", (island_id,))
        conn.execute("DELETE FROM player_profile WHERE island_id = ?", (island_id,))
        conn.execute("DELETE FROM island_profile WHERE island_id = ?", (island_id,))
        conn.execute("DELETE FROM island WHERE id = ?", (island_id,))

    invalidate_catalog_state_caches(island_id=island_id)
    return {"deleted": True, "id": island_id}


def get_villager_state_map(island_id: int) -> dict[str, dict[str, bool]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT villager_id, liked, on_island, camping_visited, former_resident, island_order
            FROM villager_state
            WHERE island_id = ?
            """,
            (island_id,),
        ).fetchall()
    return {
        str(r["villager_id"]): {
            "liked": bool(r["liked"]),
            "on_island": bool(r["on_island"]),
            "camping_visited": bool(r["camping_visited"]),
            "former_resident": bool(r["former_resident"]),
            "island_order": int(r["island_order"] or 0),
        }
        for r in rows
    }


def with_villager_state(island_id: int, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state_map = get_villager_state_map(island_id)
    merged = []
    for item in items:
        s = state_map.get(
            item["id"],
            {
                "liked": False,
                "on_island": False,
                "camping_visited": False,
                "former_resident": False,
                "island_order": 0,
            },
        )
        merged.append({**item, **s})
    return merged


def get_catalog_state_map(island_id: int, catalog_type: str) -> dict[str, dict[str, Any]]:
    cache_key = (island_id, catalog_type)
    with _CACHE_LOCK:
        cached = _CATALOG_STATE_CACHE.get(cache_key)
        if cached is not None:
            return _clone_catalog_state_map(cached)

    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT item_id, owned, donated, quantity
            FROM catalog_state
            WHERE island_id = ? AND catalog_type = ?
            """,
            (island_id, catalog_type),
        ).fetchall()
    result = {
        str(r["item_id"]): {
            "owned": bool(r["owned"]),
            "donated": bool(r["donated"]),
            "quantity": max(0, int(r["quantity"] or 0)),
        }
        for r in rows
    }
    with _CACHE_LOCK:
        _CATALOG_STATE_CACHE[cache_key] = _clone_catalog_state_map(result)
    return result


def with_catalog_state(island_id: int, catalog_type: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state_map = get_catalog_state_map(island_id, catalog_type)
    merged = []
    for item in items:
        s = state_map.get(item["id"], {"owned": False, "donated": False, "quantity": 0})
        merged.append({**item, **s})
    return merged


def get_catalog_variation_state_map(
    island_id: int,
    catalog_type: str,
    item_id: str,
) -> dict[str, dict[str, Any]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT variation_id, owned, quantity
            FROM catalog_variation_state
            WHERE island_id = ? AND catalog_type = ? AND item_id = ?
            """,
            (island_id, catalog_type, item_id),
        ).fetchall()
    return {
        str(r["variation_id"]): {
            "owned": bool(r["owned"]),
            "quantity": max(0, int(r["quantity"] or 0)),
        }
        for r in rows
    }


def upsert_catalog_state(
    conn: sqlite3.Connection,
    island_id: int,
    catalog_type: str,
    item_id: str,
    owned: bool,
    quantity: int,
    donated: bool = False,
) -> None:
    safe_qty = max(0, int(quantity or 0))
    _exec_with_retry(
        conn,
        """
        INSERT INTO catalog_state (island_id, catalog_type, item_id, owned, donated, quantity)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(island_id, catalog_type, item_id) DO UPDATE SET
            owned = excluded.owned,
            donated = excluded.donated,
            quantity = excluded.quantity,
            updated_at = CURRENT_TIMESTAMP
        """,
        (island_id, catalog_type, item_id, int(owned), int(donated), safe_qty),
    )


def upsert_all_variation_states(
    conn: sqlite3.Connection,
    island_id: int,
    catalog_type: str,
    item_id: str,
    variation_ids: list[str],
    owned: bool,
) -> None:
    if not variation_ids:
        return
    qty = 1 if owned else 0
    _executemany_with_retry(
        conn,
        """
        INSERT INTO catalog_variation_state (island_id, catalog_type, item_id, variation_id, owned, quantity)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(island_id, catalog_type, item_id, variation_id) DO UPDATE SET
            owned = excluded.owned,
            quantity = excluded.quantity,
            updated_at = CURRENT_TIMESTAMP
        """,
        [(island_id, catalog_type, item_id, vid, int(owned), qty) for vid in variation_ids],
    )


def recalc_item_owned_from_variations(
    conn: sqlite3.Connection,
    island_id: int,
    catalog_type: str,
    item_id: str,
    variation_ids: list[str],
) -> bool:
    existing_row = conn.execute(
        """
        SELECT donated
        FROM catalog_state
        WHERE island_id = ? AND catalog_type = ? AND item_id = ?
        """,
        (island_id, catalog_type, item_id),
    ).fetchone()
    existing_donated = bool(existing_row["donated"]) if existing_row else False

    if not variation_ids:
        upsert_catalog_state(conn, island_id, catalog_type, item_id, False, 0, existing_donated)
        return False
    placeholders = ",".join("?" for _ in variation_ids)
    row = conn.execute(
        f"""
        SELECT
            COUNT(*) AS owned_count,
            SUM(
                CASE
                    WHEN COALESCE(quantity, 0) > 0 THEN quantity
                    WHEN owned = 1 THEN 1
                    ELSE 0
                END
            ) AS quantity_total
        FROM catalog_variation_state
        WHERE island_id = ? AND catalog_type = ? AND item_id = ? AND owned = 1
          AND variation_id IN ({placeholders})
        """,
        (island_id, catalog_type, item_id, *variation_ids),
    ).fetchone()
    owned_count = int(row["owned_count"] or 0) if row else 0
    quantity_total = int(row["quantity_total"] or 0) if row else 0
    all_owned = owned_count == len(variation_ids)
    upsert_catalog_state(
        conn,
        island_id,
        catalog_type,
        item_id,
        all_owned,
        quantity_total,
        existing_donated,
    )
    return all_owned


def get_catalog_variation_owned_counts(island_id: int, catalog_type: str) -> dict[str, int]:
    cache_key = (island_id, catalog_type)
    with _CACHE_LOCK:
        cached = _VARIATION_OWNED_COUNT_CACHE.get(cache_key)
        if cached is not None:
            return dict(cached)

    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT item_id, SUM(CASE WHEN owned = 1 THEN 1 ELSE 0 END) AS owned_count
            FROM catalog_variation_state
            WHERE island_id = ? AND catalog_type = ?
            GROUP BY item_id
            """,
            (island_id, catalog_type),
        ).fetchall()
    result = {str(r["item_id"]): int(r["owned_count"] or 0) for r in rows}
    with _CACHE_LOCK:
        _VARIATION_OWNED_COUNT_CACHE[cache_key] = dict(result)
    return result


def get_catalog_variation_quantity_totals(island_id: int, catalog_type: str) -> dict[str, int]:
    cache_key = (island_id, catalog_type)
    with _CACHE_LOCK:
        cached = _VARIATION_QTY_TOTAL_CACHE.get(cache_key)
        if cached is not None:
            return dict(cached)

    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT
                item_id,
                SUM(
                    CASE
                        WHEN COALESCE(quantity, 0) > 0 THEN quantity
                        WHEN owned = 1 THEN 1
                        ELSE 0
                    END
                ) AS quantity_total
            FROM catalog_variation_state
            WHERE island_id = ? AND catalog_type = ?
            GROUP BY item_id
            """,
            (island_id, catalog_type),
        ).fetchall()
    result = {str(r["item_id"]): int(r["quantity_total"] or 0) for r in rows}
    with _CACHE_LOCK:
        _VARIATION_QTY_TOTAL_CACHE[cache_key] = dict(result)
    return result


def with_catalog_variation_counts(
    island_id: int,
    catalog_type: str,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    count_map = get_catalog_variation_owned_counts(island_id, catalog_type)
    qty_map = get_catalog_variation_quantity_totals(island_id, catalog_type)
    return [
        {
            **x,
            "variation_owned_count": count_map.get(x["id"], 0),
            "variation_quantity_total": qty_map.get(x["id"], 0),
        }
        for x in items
    ]


def get_island_profile(island_id: int) -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT i.id AS island_id, i.name AS island_label, p.island_name, p.nickname, p.representative_fruit,
                   p.representative_flower, p.birthday, p.hemisphere, p.time_travel_enabled, p.game_datetime
            FROM island i
            LEFT JOIN island_profile p ON p.island_id = i.id
            WHERE i.id = ?
            """,
            (island_id,),
        ).fetchone()
        if not row:
            row = conn.execute(
                """
                SELECT i.id AS island_id, i.name AS island_label, p.island_name, p.nickname, p.representative_fruit,
                       p.representative_flower, p.birthday, p.hemisphere, p.time_travel_enabled, p.game_datetime
                FROM island i
                LEFT JOIN island_profile p ON p.island_id = i.id
                ORDER BY i.id ASC
                LIMIT 1
                """
            ).fetchone()
    if not row:
        return {
            "island_id": 1,
            "island_name": "",
            "nickname": "",
            "representative_fruit": "",
            "representative_flower": "",
            "birthday": "",
            "hemisphere": "north",
            "time_travel_enabled": False,
            "game_datetime": "",
        }
    island_name = str(row["island_name"] or row["island_label"] or "").strip()
    return {
        "island_id": int(row["island_id"]),
        "island_name": island_name,
        "nickname": str(row["nickname"] or ""),
        "representative_fruit": str(row["representative_fruit"] or ""),
        "representative_flower": str(row["representative_flower"] or ""),
        "birthday": _normalize_month_day(str(row["birthday"] or "")),
        "hemisphere": str(row["hemisphere"] or "north"),
        "time_travel_enabled": bool(row["time_travel_enabled"]),
        "game_datetime": str(row["game_datetime"] or ""),
    }


def upsert_island_profile(
    island_id: int,
    island_name: str,
    nickname: str,
    representative_fruit: str,
    representative_flower: str,
    birthday: str,
    hemisphere: str,
    time_travel_enabled: bool = False,
    game_datetime: str = "",
) -> dict[str, Any]:
    init_db()
    hemi = "south" if hemisphere == "south" else "north"
    birthday_mmdd = _normalize_month_day(birthday)
    clean_name = _normalize_island_name(island_name)
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO island (id, name) VALUES (?, ?)",
            (island_id, clean_name),
        )
        conn.execute(
            "UPDATE island SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (clean_name, island_id),
        )
        conn.execute(
            """
            INSERT INTO island_profile (
                island_id, island_name, nickname, representative_fruit, representative_flower, birthday,
                hemisphere, time_travel_enabled, game_datetime
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(island_id) DO UPDATE SET
                island_name = excluded.island_name,
                nickname = excluded.nickname,
                representative_fruit = excluded.representative_fruit,
                representative_flower = excluded.representative_flower,
                birthday = excluded.birthday,
                hemisphere = excluded.hemisphere,
                time_travel_enabled = excluded.time_travel_enabled,
                game_datetime = excluded.game_datetime,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                island_id,
                clean_name,
                nickname.strip(),
                representative_fruit.strip(),
                representative_flower.strip(),
                birthday_mmdd,
                hemi,
                int(time_travel_enabled),
                game_datetime.strip(),
            ),
        )
    return get_island_profile(island_id)


def list_calendar_entries(island_id: int, month: str) -> list[dict[str, Any]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, visit_date, npc_name, note, checked
            FROM calendar_entry
            WHERE island_id = ? AND visit_date >= ? AND visit_date < ?
            ORDER BY visit_date ASC, id ASC
            """,
            (island_id, f"{month}-01", f"{month}-32"),
        ).fetchall()
    return [
        {
            "id": int(r["id"]),
            "visit_date": str(r["visit_date"]),
            "npc_name": str(r["npc_name"]),
            "note": str(r["note"] or ""),
            "checked": bool(r["checked"]),
        }
        for r in rows
    ]


def list_calendar_entries_by_date(island_id: int, visit_date: str) -> list[dict[str, Any]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, visit_date, npc_name, note, checked
            FROM calendar_entry
            WHERE island_id = ? AND visit_date = ?
            ORDER BY id ASC
            """,
            (island_id, visit_date),
        ).fetchall()
    return [
        {
            "id": int(r["id"]),
            "visit_date": str(r["visit_date"]),
            "npc_name": str(r["npc_name"]),
            "note": str(r["note"] or ""),
            "checked": bool(r["checked"]),
        }
        for r in rows
    ]


def upsert_calendar_entry(
    island_id: int,
    visit_date: str,
    npc_name: str,
    note: str,
    checked: bool,
    entry_id: int | None = None,
) -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        if entry_id:
            conn.execute(
                """
                UPDATE calendar_entry
                SET visit_date = ?, npc_name = ?, note = ?, checked = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND island_id = ?
                """,
                (visit_date, npc_name.strip(), note.strip(), int(checked), entry_id, island_id),
            )
            row = conn.execute(
                """
                SELECT id, visit_date, npc_name, note, checked
                FROM calendar_entry
                WHERE id = ? AND island_id = ?
                """,
                (entry_id, island_id),
            ).fetchone()
        else:
            conn.execute(
                """
                INSERT INTO calendar_entry (island_id, visit_date, npc_name, note, checked)
                VALUES (?, ?, ?, ?, ?)
                """,
                (island_id, visit_date, npc_name.strip(), note.strip(), int(checked)),
            )
            row = conn.execute(
                """
                SELECT id, visit_date, npc_name, note, checked
                FROM calendar_entry
                WHERE id = last_insert_rowid()
                """
            ).fetchone()
    if not row:
        raise RuntimeError("calendar entry save failed")
    return {
        "id": int(row["id"]),
        "visit_date": str(row["visit_date"]),
        "npc_name": str(row["npc_name"]),
        "note": str(row["note"] or ""),
        "checked": bool(row["checked"]),
    }


def update_calendar_entry_checked(island_id: int, entry_id: int, checked: bool) -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        conn.execute(
            """
            UPDATE calendar_entry
            SET checked = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND island_id = ?
            """,
            (int(checked), entry_id, island_id),
        )
        row = conn.execute(
            """
            SELECT id, visit_date, npc_name, note, checked
            FROM calendar_entry
            WHERE id = ? AND island_id = ?
            """,
            (entry_id, island_id),
        ).fetchone()
    if not row:
        raise RuntimeError("calendar entry not found")
    return {
        "id": int(row["id"]),
        "visit_date": str(row["visit_date"]),
        "npc_name": str(row["npc_name"]),
        "note": str(row["note"] or ""),
        "checked": bool(row["checked"]),
    }


def delete_calendar_entry(island_id: int, entry_id: int) -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        conn.execute("DELETE FROM calendar_entry WHERE id = ? AND island_id = ?", (entry_id, island_id))
    return {"deleted": True, "id": entry_id}


def _normalize_player_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "name": str(row["name"] or ""),
        "birthday": _normalize_month_day(str(row["birthday"] or "")),
        "is_main": bool(row["is_main"]),
        "is_sub": bool(row["is_sub"]),
    }


def list_players(island_id: int) -> list[dict[str, Any]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, name, birthday, is_main, is_sub
            FROM player_profile
            WHERE island_id = ?
            ORDER BY is_main DESC, id ASC
            """,
            (island_id,),
        ).fetchall()
    return [_normalize_player_row(r) for r in rows]


def upsert_player(
    island_id: int,
    name: str,
    birthday: str,
    is_main: bool = False,
    is_sub: bool = False,
    player_id: int | None = None,
) -> dict[str, Any]:
    init_db()
    clean_name = name.strip()
    birthday_mmdd = _normalize_month_day(birthday)
    if not clean_name:
        raise ValueError("player name is required")

    with get_db() as conn:
        if player_id:
            exists = conn.execute(
                "SELECT id FROM player_profile WHERE id = ? AND island_id = ?",
                (player_id, island_id),
            ).fetchone()
            if not exists:
                raise ValueError("player not found")

            if is_main:
                conn.execute(
                    "UPDATE player_profile SET is_main = 0 WHERE island_id = ? AND id != ?",
                    (island_id, player_id),
                )
            conn.execute(
                """
                UPDATE player_profile
                SET name = ?, birthday = ?, is_main = ?, is_sub = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND island_id = ?
                """,
                (clean_name, birthday_mmdd, int(is_main), int(is_sub), player_id, island_id),
            )
            row = conn.execute(
                """
                SELECT id, name, birthday, is_main, is_sub
                FROM player_profile
                WHERE id = ? AND island_id = ?
                """,
                (player_id, island_id),
            ).fetchone()
        else:
            count_row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM player_profile WHERE island_id = ?",
                (island_id,),
            ).fetchone()
            count = int(count_row["cnt"] or 0) if count_row else 0
            if count >= 8:
                raise ValueError("up to 8 players can be registered per island")

            has_main_row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM player_profile WHERE island_id = ? AND is_main = 1",
                (island_id,),
            ).fetchone()
            has_main = int(has_main_row["cnt"] or 0) > 0 if has_main_row else False
            target_main = bool(is_main) or not has_main
            if target_main:
                conn.execute("UPDATE player_profile SET is_main = 0 WHERE island_id = ?", (island_id,))

            conn.execute(
                """
                INSERT INTO player_profile (island_id, name, birthday, is_main, is_sub)
                VALUES (?, ?, ?, ?, ?)
                """,
                (island_id, clean_name, birthday_mmdd, int(target_main), int(is_sub)),
            )
            row = conn.execute(
                """
                SELECT id, name, birthday, is_main, is_sub
                FROM player_profile
                WHERE id = last_insert_rowid()
                """
            ).fetchone()

    if not row:
        raise RuntimeError("player save failed")
    return _normalize_player_row(row)


def set_main_player(island_id: int, player_id: int) -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        exists = conn.execute(
            "SELECT id FROM player_profile WHERE id = ? AND island_id = ?",
            (player_id, island_id),
        ).fetchone()
        if not exists:
            raise ValueError("player not found")
        conn.execute("UPDATE player_profile SET is_main = 0 WHERE island_id = ?", (island_id,))
        conn.execute(
            """
            UPDATE player_profile
            SET is_main = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND island_id = ?
            """,
            (player_id, island_id),
        )
        row = conn.execute(
            """
            SELECT id, name, birthday, is_main, is_sub
            FROM player_profile
            WHERE id = ? AND island_id = ?
            """,
            (player_id, island_id),
        ).fetchone()
    if not row:
        raise RuntimeError("main player update failed")
    return _normalize_player_row(row)


def delete_player(island_id: int, player_id: int) -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, is_main FROM player_profile WHERE id = ? AND island_id = ?",
            (player_id, island_id),
        ).fetchone()
        if not row:
            raise ValueError("player not found")

        was_main = bool(row["is_main"])
        conn.execute("DELETE FROM player_profile WHERE id = ? AND island_id = ?", (player_id, island_id))

        if was_main:
            next_row = conn.execute(
                "SELECT id FROM player_profile WHERE island_id = ? ORDER BY id ASC LIMIT 1",
                (island_id,),
            ).fetchone()
            if next_row:
                conn.execute(
                    """
                    UPDATE player_profile
                    SET is_main = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND island_id = ?
                    """,
                    (int(next_row["id"]), island_id),
                )
    return {"deleted": True, "id": player_id}


def _use_supabase_state_mode() -> bool:
    backend = get_state_backend()
    if backend == "sqlite":
        return False
    if backend == "supabase":
        return is_supabase_state_available()
    return is_supabase_state_available()


def _eq(value: Any) -> str:
    return f"eq.{value}"


def _bool_int(value: Any) -> int:
    return 1 if bool(value) else 0


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "on"}


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _ensure_default_island_supabase() -> dict[str, Any]:
    rows = fetch_rows("island", select="id,name", order="id.asc", limit=1)
    if rows:
        row = rows[0]
        island_id = _int_value(row.get("id"), 1)
        profile_rows = fetch_rows(
            "island_profile",
            select="island_id",
            filters={"island_id": _eq(island_id)},
            limit=1,
        )
        if not profile_rows:
            upsert_rows(
                "island_profile",
                [
                    {
                        "island_id": island_id,
                        "island_name": str(row.get("name") or "Default Island"),
                        "nickname": "",
                        "representative_fruit": "",
                        "representative_flower": "",
                        "birthday": "",
                        "hemisphere": "north",
                        "time_travel_enabled": False,
                        "game_datetime": "",
                    }
                ],
                "island_id",
            )
        return {"id": island_id, "name": str(row.get("name") or "Default Island")}

    inserted = insert_row("island", {"name": "Default Island"})
    island_id = _int_value(inserted.get("id"), 1)
    upsert_rows(
        "island_profile",
        [
            {
                "island_id": island_id,
                "island_name": "Default Island",
                "nickname": "",
                "representative_fruit": "",
                "representative_flower": "",
                "birthday": "",
                "hemisphere": "north",
                "time_travel_enabled": False,
                "game_datetime": "",
            }
        ],
        "island_id",
    )
    return {"id": island_id, "name": "Default Island"}


def list_islands() -> list[dict[str, Any]]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT i.id, i.name, p.island_name
                FROM island i
                LEFT JOIN island_profile p ON p.island_id = i.id
                ORDER BY i.id ASC
                """
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "name": str(row["island_name"] or row["name"] or "").strip() or f"Island {int(row['id'])}",
            }
            for row in rows
        ]

    _ensure_default_island_supabase()
    islands = fetch_rows("island", select="id,name", order="id.asc")
    profiles = fetch_rows("island_profile", select="island_id,island_name")
    profile_map = {_int_value(row.get("island_id")): str(row.get("island_name") or "").strip() for row in profiles}
    return [
        {
            "id": _int_value(row.get("id")),
            "name": profile_map.get(_int_value(row.get("id"))) or str(row.get("name") or "").strip() or f"Island {_int_value(row.get('id'))}",
        }
        for row in islands
    ]


def create_island(name: str) -> dict[str, Any]:
    if not _use_supabase_state_mode():
        init_db()
        display_name = _normalize_island_name(name)
        with get_db() as conn:
            conn.execute("INSERT INTO island (name) VALUES (?)", (display_name,))
            row = conn.execute("SELECT id, name FROM island WHERE id = last_insert_rowid()").fetchone()
            if not row:
                raise RuntimeError("island create failed")
            island_id = int(row["id"])
            conn.execute(
                """
                INSERT OR IGNORE INTO island_profile (
                    island_id, island_name, nickname, representative_fruit, representative_flower, birthday,
                    hemisphere, time_travel_enabled, game_datetime
                ) VALUES (?, ?, '', '', '', '', 'north', 0, '')
                """,
                (island_id, display_name),
            )
        return {"id": island_id, "name": display_name}

    display_name = _normalize_island_name(name)
    row = insert_row("island", {"name": display_name})
    island_id = _int_value(row.get("id"))
    upsert_rows(
        "island_profile",
        [
            {
                "island_id": island_id,
                "island_name": display_name,
                "nickname": "",
                "representative_fruit": "",
                "representative_flower": "",
                "birthday": "",
                "hemisphere": "north",
                "time_travel_enabled": False,
                "game_datetime": "",
            }
        ],
        "island_id",
    )
    return {"id": island_id, "name": display_name}


def delete_island(island_id: int) -> dict[str, Any]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            row = conn.execute("SELECT id, name FROM island WHERE id = ?", (island_id,)).fetchone()
            if not row:
                raise ValueError("island not found")
            count_row = conn.execute("SELECT COUNT(*) AS cnt FROM island").fetchone()
            island_count = int(count_row["cnt"] or 0) if count_row else 0
            if island_count <= 1:
                raise ValueError("cannot delete the last island")
            conn.execute("DELETE FROM villager_state WHERE island_id = ?", (island_id,))
            conn.execute("DELETE FROM catalog_variation_state WHERE island_id = ?", (island_id,))
            conn.execute("DELETE FROM catalog_state WHERE island_id = ?", (island_id,))
            conn.execute("DELETE FROM calendar_entry WHERE island_id = ?", (island_id,))
            conn.execute("DELETE FROM player_profile WHERE island_id = ?", (island_id,))
            conn.execute("DELETE FROM island_profile WHERE island_id = ?", (island_id,))
            conn.execute("DELETE FROM island WHERE id = ?", (island_id,))
        invalidate_catalog_state_caches(island_id=island_id)
        return {"deleted": True, "id": island_id}

    islands = list_islands()
    if not any(int(row["id"]) == island_id for row in islands):
        raise ValueError("island not found")
    if len(islands) <= 1:
        raise ValueError("cannot delete the last island")
    delete_rows("island", {"id": _eq(island_id)})
    invalidate_catalog_state_caches(island_id=island_id)
    return {"deleted": True, "id": island_id}


def get_villager_state_map(island_id: int) -> dict[str, dict[str, bool]]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT villager_id, liked, on_island, camping_visited, former_resident, island_order
                FROM villager_state
                WHERE island_id = ?
                """,
                (island_id,),
            ).fetchall()
        return {
            str(r["villager_id"]): {
                "liked": bool(r["liked"]),
                "on_island": bool(r["on_island"]),
                "camping_visited": bool(r["camping_visited"]),
                "former_resident": bool(r["former_resident"]),
                "island_order": int(r["island_order"] or 0),
            }
            for r in rows
        }

    rows = fetch_rows(
        "villager_state",
        select="villager_id,liked,on_island,camping_visited,former_resident,island_order",
        filters={"island_id": _eq(island_id)},
    )
    return {
        str(r.get("villager_id") or ""): {
            "liked": _bool_value(r.get("liked")),
            "on_island": _bool_value(r.get("on_island")),
            "camping_visited": _bool_value(r.get("camping_visited")),
            "former_resident": _bool_value(r.get("former_resident")),
            "island_order": _int_value(r.get("island_order")),
        }
        for r in rows
        if str(r.get("villager_id") or "")
    }


def get_catalog_state_map(island_id: int, catalog_type: str) -> dict[str, dict[str, Any]]:
    cache_key = (island_id, catalog_type)
    with _CACHE_LOCK:
        cached = _CATALOG_STATE_CACHE.get(cache_key)
        if cached is not None:
            return _clone_catalog_state_map(cached)

    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT item_id, owned, donated, quantity
                FROM catalog_state
                WHERE island_id = ? AND catalog_type = ?
                """,
                (island_id, catalog_type),
            ).fetchall()
        result = {
            str(r["item_id"]): {
                "owned": bool(r["owned"]),
                "donated": bool(r["donated"]),
                "quantity": max(0, int(r["quantity"] or 0)),
            }
            for r in rows
        }
    else:
        rows = fetch_rows(
            "catalog_state",
            select="item_id,owned,donated,quantity",
            filters={"island_id": _eq(island_id), "catalog_type": _eq(catalog_type)},
        )
        result = {
            str(r.get("item_id") or ""): {
                "owned": _bool_value(r.get("owned")),
                "donated": _bool_value(r.get("donated")),
                "quantity": max(0, _int_value(r.get("quantity"))),
            }
            for r in rows
            if str(r.get("item_id") or "")
        }
    with _CACHE_LOCK:
        _CATALOG_STATE_CACHE[cache_key] = _clone_catalog_state_map(result)
    return result


def get_catalog_variation_state_map(island_id: int, catalog_type: str, item_id: str) -> dict[str, dict[str, Any]]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT variation_id, owned, quantity
                FROM catalog_variation_state
                WHERE island_id = ? AND catalog_type = ? AND item_id = ?
                """,
                (island_id, catalog_type, item_id),
            ).fetchall()
        return {
            str(r["variation_id"]): {
                "owned": bool(r["owned"]),
                "quantity": max(0, int(r["quantity"] or 0)),
            }
            for r in rows
        }

    rows = fetch_rows(
        "catalog_variation_state",
        select="variation_id,owned,quantity",
        filters={"island_id": _eq(island_id), "catalog_type": _eq(catalog_type), "item_id": _eq(item_id)},
    )
    return {
        str(r.get("variation_id") or ""): {
            "owned": _bool_value(r.get("owned")),
            "quantity": max(0, _int_value(r.get("quantity"))),
        }
        for r in rows
        if str(r.get("variation_id") or "")
    }


def get_catalog_variation_owned_counts(island_id: int, catalog_type: str) -> dict[str, int]:
    cache_key = (island_id, catalog_type)
    with _CACHE_LOCK:
        cached = _VARIATION_OWNED_COUNT_CACHE.get(cache_key)
        if cached is not None:
            return dict(cached)
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT item_id, SUM(CASE WHEN owned = 1 THEN 1 ELSE 0 END) AS owned_count
                FROM catalog_variation_state
                WHERE island_id = ? AND catalog_type = ?
                GROUP BY item_id
                """,
                (island_id, catalog_type),
            ).fetchall()
        result = {str(r["item_id"]): int(r["owned_count"] or 0) for r in rows}
    else:
        rows = fetch_rows(
            "catalog_variation_state",
            select="item_id,owned",
            filters={"island_id": _eq(island_id), "catalog_type": _eq(catalog_type)},
        )
        result: dict[str, int] = {}
        for row in rows:
            item_id = str(row.get("item_id") or "")
            if not item_id:
                continue
            result[item_id] = result.get(item_id, 0) + (1 if _bool_value(row.get("owned")) else 0)
    with _CACHE_LOCK:
        _VARIATION_OWNED_COUNT_CACHE[cache_key] = dict(result)
    return result


def get_catalog_variation_quantity_totals(island_id: int, catalog_type: str) -> dict[str, int]:
    cache_key = (island_id, catalog_type)
    with _CACHE_LOCK:
        cached = _VARIATION_QTY_TOTAL_CACHE.get(cache_key)
        if cached is not None:
            return dict(cached)
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT
                    item_id,
                    SUM(
                        CASE
                            WHEN COALESCE(quantity, 0) > 0 THEN quantity
                            WHEN owned = 1 THEN 1
                            ELSE 0
                        END
                    ) AS quantity_total
                FROM catalog_variation_state
                WHERE island_id = ? AND catalog_type = ?
                GROUP BY item_id
                """,
                (island_id, catalog_type),
            ).fetchall()
        result = {str(r["item_id"]): int(r["quantity_total"] or 0) for r in rows}
    else:
        rows = fetch_rows(
            "catalog_variation_state",
            select="item_id,owned,quantity",
            filters={"island_id": _eq(island_id), "catalog_type": _eq(catalog_type)},
        )
        result: dict[str, int] = {}
        for row in rows:
            item_id = str(row.get("item_id") or "")
            if not item_id:
                continue
            qty = _int_value(row.get("quantity"))
            if qty <= 0 and _bool_value(row.get("owned")):
                qty = 1
            result[item_id] = result.get(item_id, 0) + max(0, qty)
    with _CACHE_LOCK:
        _VARIATION_QTY_TOTAL_CACHE[cache_key] = dict(result)
    return result


def get_island_profile(island_id: int) -> dict[str, Any]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT i.id AS island_id, i.name AS island_label, p.island_name, p.nickname, p.representative_fruit,
                       p.representative_flower, p.birthday, p.hemisphere, p.time_travel_enabled, p.game_datetime
                FROM island i
                LEFT JOIN island_profile p ON p.island_id = i.id
                WHERE i.id = ?
                """,
                (island_id,),
            ).fetchone()
            if not row:
                row = conn.execute(
                    """
                    SELECT i.id AS island_id, i.name AS island_label, p.island_name, p.nickname, p.representative_fruit,
                           p.representative_flower, p.birthday, p.hemisphere, p.time_travel_enabled, p.game_datetime
                    FROM island i
                    LEFT JOIN island_profile p ON p.island_id = i.id
                    ORDER BY i.id ASC
                    LIMIT 1
                    """
                ).fetchone()
        if not row:
            return {
                "island_id": 1,
                "island_name": "",
                "nickname": "",
                "representative_fruit": "",
                "representative_flower": "",
                "birthday": "",
                "hemisphere": "north",
                "time_travel_enabled": False,
                "game_datetime": "",
            }
        island_name = str(row["island_name"] or row["island_label"] or "").strip()
        return {
            "island_id": int(row["island_id"]),
            "island_name": island_name,
            "nickname": str(row["nickname"] or ""),
            "representative_fruit": str(row["representative_fruit"] or ""),
            "representative_flower": str(row["representative_flower"] or ""),
            "birthday": _normalize_month_day(str(row["birthday"] or "")),
            "hemisphere": str(row["hemisphere"] or "north"),
            "time_travel_enabled": bool(row["time_travel_enabled"]),
            "game_datetime": str(row["game_datetime"] or ""),
        }

    ensured = _ensure_default_island_supabase()
    islands = fetch_rows("island", select="id,name", filters={"id": _eq(island_id)}, limit=1)
    island = islands[0] if islands else {"id": ensured["id"], "name": ensured["name"]}
    profiles = fetch_rows("island_profile", select="*", filters={"island_id": _eq(_int_value(island.get("id")))} , limit=1)
    profile = profiles[0] if profiles else {}
    return {
        "island_id": _int_value(island.get("id"), 1),
        "island_name": str(profile.get("island_name") or island.get("name") or "").strip(),
        "nickname": str(profile.get("nickname") or ""),
        "representative_fruit": str(profile.get("representative_fruit") or ""),
        "representative_flower": str(profile.get("representative_flower") or ""),
        "birthday": _normalize_month_day(str(profile.get("birthday") or "")),
        "hemisphere": str(profile.get("hemisphere") or "north"),
        "time_travel_enabled": _bool_value(profile.get("time_travel_enabled")),
        "game_datetime": str(profile.get("game_datetime") or ""),
    }


def upsert_island_profile(
    island_id: int,
    island_name: str,
    nickname: str,
    representative_fruit: str,
    representative_flower: str,
    birthday: str,
    hemisphere: str,
    time_travel_enabled: bool = False,
    game_datetime: str = "",
) -> dict[str, Any]:
    if not _use_supabase_state_mode():
        init_db()
        hemi = "south" if hemisphere == "south" else "north"
        birthday_mmdd = _normalize_month_day(birthday)
        clean_name = _normalize_island_name(island_name)
        with get_db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO island (id, name) VALUES (?, ?)",
                (island_id, clean_name),
            )
            conn.execute(
                "UPDATE island SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (clean_name, island_id),
            )
            conn.execute(
                """
                INSERT INTO island_profile (
                    island_id, island_name, nickname, representative_fruit, representative_flower, birthday,
                    hemisphere, time_travel_enabled, game_datetime
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(island_id) DO UPDATE SET
                    island_name = excluded.island_name,
                    nickname = excluded.nickname,
                    representative_fruit = excluded.representative_fruit,
                    representative_flower = excluded.representative_flower,
                    birthday = excluded.birthday,
                    hemisphere = excluded.hemisphere,
                    time_travel_enabled = excluded.time_travel_enabled,
                    game_datetime = excluded.game_datetime,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    island_id,
                    clean_name,
                    nickname.strip(),
                    representative_fruit.strip(),
                    representative_flower.strip(),
                    birthday_mmdd,
                    hemi,
                    int(time_travel_enabled),
                    game_datetime.strip(),
                ),
            )
        return get_island_profile(island_id)

    clean_name = _normalize_island_name(island_name)
    hemi = "south" if hemisphere == "south" else "north"
    birthday_mmdd = _normalize_month_day(birthday)
    upsert_rows("island", [{"id": island_id, "name": clean_name}], "id")
    upsert_rows(
        "island_profile",
        [
            {
                "island_id": island_id,
                "island_name": clean_name,
                "nickname": nickname.strip(),
                "representative_fruit": representative_fruit.strip(),
                "representative_flower": representative_flower.strip(),
                "birthday": birthday_mmdd,
                "hemisphere": hemi,
                "time_travel_enabled": bool(time_travel_enabled),
                "game_datetime": game_datetime.strip(),
            }
        ],
        "island_id",
    )
    return get_island_profile(island_id)


def list_calendar_entries(island_id: int, month: str) -> list[dict[str, Any]]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT id, visit_date, npc_name, note, checked
                FROM calendar_entry
                WHERE island_id = ? AND visit_date >= ? AND visit_date < ?
                ORDER BY visit_date ASC, id ASC
                """,
                (island_id, f"{month}-01", f"{month}-32"),
            ).fetchall()
        return [
            {
                "id": int(r["id"]),
                "visit_date": str(r["visit_date"]),
                "npc_name": str(r["npc_name"]),
                "note": str(r["note"] or ""),
                "checked": bool(r["checked"]),
            }
            for r in rows
        ]

    rows = fetch_rows(
        "calendar_entry",
        select="id,visit_date,npc_name,note,checked",
        filters={"island_id": _eq(island_id), "visit_date": f"gte.{month}-01", "visit_date": f"gte.{month}-01"},
    )
    items = [
        {
            "id": _int_value(r.get("id")),
            "visit_date": str(r.get("visit_date") or ""),
            "npc_name": str(r.get("npc_name") or ""),
            "note": str(r.get("note") or ""),
            "checked": _bool_value(r.get("checked")),
        }
        for r in rows
        if f"{month}-01" <= str(r.get("visit_date") or "") < f"{month}-32"
    ]
    items.sort(key=lambda r: (r["visit_date"], r["id"]))
    return items


def list_calendar_entries_by_date(island_id: int, visit_date: str) -> list[dict[str, Any]]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT id, visit_date, npc_name, note, checked
                FROM calendar_entry
                WHERE island_id = ? AND visit_date = ?
                ORDER BY id ASC
                """,
                (island_id, visit_date),
            ).fetchall()
        return [
            {
                "id": int(r["id"]),
                "visit_date": str(r["visit_date"]),
                "npc_name": str(r["npc_name"]),
                "note": str(r["note"] or ""),
                "checked": bool(r["checked"]),
            }
            for r in rows
        ]

    rows = fetch_rows(
        "calendar_entry",
        select="id,visit_date,npc_name,note,checked",
        filters={"island_id": _eq(island_id), "visit_date": _eq(visit_date)},
        order="id.asc",
    )
    return [
        {
            "id": _int_value(r.get("id")),
            "visit_date": str(r.get("visit_date") or ""),
            "npc_name": str(r.get("npc_name") or ""),
            "note": str(r.get("note") or ""),
            "checked": _bool_value(r.get("checked")),
        }
        for r in rows
    ]


def upsert_calendar_entry(
    island_id: int,
    visit_date: str,
    npc_name: str,
    note: str,
    checked: bool,
    entry_id: int | None = None,
) -> dict[str, Any]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            if entry_id:
                conn.execute(
                    """
                    UPDATE calendar_entry
                    SET visit_date = ?, npc_name = ?, note = ?, checked = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND island_id = ?
                    """,
                    (visit_date, npc_name.strip(), note.strip(), int(checked), entry_id, island_id),
                )
                row = conn.execute(
                    """
                    SELECT id, visit_date, npc_name, note, checked
                    FROM calendar_entry
                    WHERE id = ? AND island_id = ?
                    """,
                    (entry_id, island_id),
                ).fetchone()
            else:
                conn.execute(
                    """
                    INSERT INTO calendar_entry (island_id, visit_date, npc_name, note, checked)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (island_id, visit_date, npc_name.strip(), note.strip(), int(checked)),
                )
                row = conn.execute(
                    """
                    SELECT id, visit_date, npc_name, note, checked
                    FROM calendar_entry
                    WHERE id = last_insert_rowid()
                    """
                ).fetchone()
        if not row:
            raise RuntimeError("calendar entry save failed")
        return {
            "id": int(row["id"]),
            "visit_date": str(row["visit_date"]),
            "npc_name": str(row["npc_name"]),
            "note": str(row["note"] or ""),
            "checked": bool(row["checked"]),
        }

    if entry_id:
        rows = patch_rows(
            "calendar_entry",
            {"id": _eq(entry_id), "island_id": _eq(island_id)},
            {
                "visit_date": visit_date,
                "npc_name": npc_name.strip(),
                "note": note.strip(),
                "checked": bool(checked),
            },
        )
        row = rows[0] if rows else {}
    else:
        row = insert_row(
            "calendar_entry",
            {
                "island_id": island_id,
                "visit_date": visit_date,
                "npc_name": npc_name.strip(),
                "note": note.strip(),
                "checked": bool(checked),
            },
        )
    if not row:
        raise RuntimeError("calendar entry save failed")
    return {
        "id": _int_value(row.get("id")),
        "visit_date": str(row.get("visit_date") or ""),
        "npc_name": str(row.get("npc_name") or ""),
        "note": str(row.get("note") or ""),
        "checked": _bool_value(row.get("checked")),
    }


def update_calendar_entry_checked(island_id: int, entry_id: int, checked: bool) -> dict[str, Any]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            conn.execute(
                """
                UPDATE calendar_entry
                SET checked = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND island_id = ?
                """,
                (int(checked), entry_id, island_id),
            )
            row = conn.execute(
                """
                SELECT id, visit_date, npc_name, note, checked
                FROM calendar_entry
                WHERE id = ? AND island_id = ?
                """,
                (entry_id, island_id),
            ).fetchone()
        if not row:
            raise RuntimeError("calendar entry not found")
        return {
            "id": int(row["id"]),
            "visit_date": str(row["visit_date"]),
            "npc_name": str(row["npc_name"]),
            "note": str(row["note"] or ""),
            "checked": bool(row["checked"]),
        }

    rows = patch_rows(
        "calendar_entry",
        {"id": _eq(entry_id), "island_id": _eq(island_id)},
        {"checked": bool(checked)},
    )
    row = rows[0] if rows else {}
    if not row:
        raise RuntimeError("calendar entry not found")
    return {
        "id": _int_value(row.get("id")),
        "visit_date": str(row.get("visit_date") or ""),
        "npc_name": str(row.get("npc_name") or ""),
        "note": str(row.get("note") or ""),
        "checked": _bool_value(row.get("checked")),
    }


def delete_calendar_entry(island_id: int, entry_id: int) -> dict[str, Any]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            conn.execute("DELETE FROM calendar_entry WHERE id = ? AND island_id = ?", (entry_id, island_id))
        return {"deleted": True, "id": entry_id}
    delete_rows("calendar_entry", {"id": _eq(entry_id), "island_id": _eq(island_id)})
    return {"deleted": True, "id": entry_id}


def list_players(island_id: int) -> list[dict[str, Any]]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT id, name, birthday, is_main, is_sub
                FROM player_profile
                WHERE island_id = ?
                ORDER BY is_main DESC, id ASC
                """,
                (island_id,),
            ).fetchall()
        return [_normalize_player_row(r) for r in rows]

    rows = fetch_rows(
        "player_profile",
        select="id,name,birthday,is_main,is_sub",
        filters={"island_id": _eq(island_id)},
        order="is_main.desc,id.asc",
    )
    return [
        {
            "id": _int_value(r.get("id")),
            "name": str(r.get("name") or ""),
            "birthday": _normalize_month_day(str(r.get("birthday") or "")),
            "is_main": _bool_value(r.get("is_main")),
            "is_sub": _bool_value(r.get("is_sub")),
        }
        for r in rows
    ]


def upsert_player(
    island_id: int,
    name: str,
    birthday: str,
    is_main: bool = False,
    is_sub: bool = False,
    player_id: int | None = None,
) -> dict[str, Any]:
    if not _use_supabase_state_mode():
        init_db()
        clean_name = name.strip()
        birthday_mmdd = _normalize_month_day(birthday)
        if not clean_name:
            raise ValueError("player name is required")
        with get_db() as conn:
            if player_id:
                exists = conn.execute(
                    "SELECT id FROM player_profile WHERE id = ? AND island_id = ?",
                    (player_id, island_id),
                ).fetchone()
                if not exists:
                    raise ValueError("player not found")
                if is_main:
                    conn.execute(
                        "UPDATE player_profile SET is_main = 0 WHERE island_id = ? AND id != ?",
                        (island_id, player_id),
                    )
                conn.execute(
                    """
                    UPDATE player_profile
                    SET name = ?, birthday = ?, is_main = ?, is_sub = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND island_id = ?
                    """,
                    (clean_name, birthday_mmdd, int(is_main), int(is_sub), player_id, island_id),
                )
                row = conn.execute(
                    """
                    SELECT id, name, birthday, is_main, is_sub
                    FROM player_profile
                    WHERE id = ? AND island_id = ?
                    """,
                    (player_id, island_id),
                ).fetchone()
            else:
                count = len(list_players(island_id))
                if count >= 8:
                    raise ValueError("up to 8 players can be registered per island")
                has_main = any(player.get("is_main") for player in list_players(island_id))
                target_main = bool(is_main) or not has_main
                if target_main:
                    conn.execute("UPDATE player_profile SET is_main = 0 WHERE island_id = ?", (island_id,))
                conn.execute(
                    """
                    INSERT INTO player_profile (island_id, name, birthday, is_main, is_sub)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (island_id, clean_name, birthday_mmdd, int(target_main), int(is_sub)),
                )
                row = conn.execute(
                    """
                    SELECT id, name, birthday, is_main, is_sub
                    FROM player_profile
                    WHERE id = last_insert_rowid()
                    """
                ).fetchone()
        if not row:
            raise RuntimeError("player save failed")
        return _normalize_player_row(row)

    players = list_players(island_id)
    clean_name = name.strip()
    birthday_mmdd = _normalize_month_day(birthday)
    if not clean_name:
        raise ValueError("player name is required")
    if player_id and not any(int(player["id"]) == player_id for player in players):
        raise ValueError("player not found")
    if not player_id and len(players) >= 8:
        raise ValueError("up to 8 players can be registered per island")
    target_main = bool(is_main) or (not any(player.get("is_main") for player in players))
    if target_main:
        for player in players:
            if player_id and int(player["id"]) == player_id:
                continue
            if player.get("is_main"):
                patch_rows("player_profile", {"id": _eq(int(player["id"])), "island_id": _eq(island_id)}, {"is_main": False})
    if player_id:
        rows = patch_rows(
            "player_profile",
            {"id": _eq(player_id), "island_id": _eq(island_id)},
            {"name": clean_name, "birthday": birthday_mmdd, "is_main": target_main, "is_sub": bool(is_sub)},
        )
        row = rows[0] if rows else {}
    else:
        row = insert_row(
            "player_profile",
            {
                "island_id": island_id,
                "name": clean_name,
                "birthday": birthday_mmdd,
                "is_main": target_main,
                "is_sub": bool(is_sub),
            },
        )
    if not row:
        raise RuntimeError("player save failed")
    return {
        "id": _int_value(row.get("id")),
        "name": str(row.get("name") or ""),
        "birthday": _normalize_month_day(str(row.get("birthday") or "")),
        "is_main": _bool_value(row.get("is_main")),
        "is_sub": _bool_value(row.get("is_sub")),
    }


def set_main_player(island_id: int, player_id: int) -> dict[str, Any]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            exists = conn.execute(
                "SELECT id FROM player_profile WHERE id = ? AND island_id = ?",
                (player_id, island_id),
            ).fetchone()
            if not exists:
                raise ValueError("player not found")
            conn.execute("UPDATE player_profile SET is_main = 0 WHERE island_id = ?", (island_id,))
            conn.execute(
                """
                UPDATE player_profile
                SET is_main = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND island_id = ?
                """,
                (player_id, island_id),
            )
            row = conn.execute(
                """
                SELECT id, name, birthday, is_main, is_sub
                FROM player_profile
                WHERE id = ? AND island_id = ?
                """,
                (player_id, island_id),
            ).fetchone()
        if not row:
            raise RuntimeError("main player update failed")
        return _normalize_player_row(row)

    if not any(int(player["id"]) == player_id for player in list_players(island_id)):
        raise ValueError("player not found")
    for player in list_players(island_id):
        patch_rows(
            "player_profile",
            {"id": _eq(int(player["id"])), "island_id": _eq(island_id)},
            {"is_main": int(int(player["id"]) == player_id)},
        )
    row = next(player for player in list_players(island_id) if int(player["id"]) == player_id)
    return row


def delete_player(island_id: int, player_id: int) -> dict[str, Any]:
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            row = conn.execute(
                "SELECT id, is_main FROM player_profile WHERE id = ? AND island_id = ?",
                (player_id, island_id),
            ).fetchone()
            if not row:
                raise ValueError("player not found")
            was_main = bool(row["is_main"])
            conn.execute("DELETE FROM player_profile WHERE id = ? AND island_id = ?", (player_id, island_id))
            if was_main:
                next_row = conn.execute(
                    "SELECT id FROM player_profile WHERE island_id = ? ORDER BY id ASC LIMIT 1",
                    (island_id,),
                ).fetchone()
                if next_row:
                    conn.execute(
                        """
                        UPDATE player_profile
                        SET is_main = 1, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND island_id = ?
                        """,
                        (int(next_row["id"]), island_id),
                    )
        return {"deleted": True, "id": player_id}

    players = list_players(island_id)
    target = next((player for player in players if int(player["id"]) == player_id), None)
    if not target:
        raise ValueError("player not found")
    was_main = bool(target.get("is_main"))
    delete_rows("player_profile", {"id": _eq(player_id), "island_id": _eq(island_id)})
    if was_main:
        remaining = list_players(island_id)
        if remaining:
            patch_rows(
                "player_profile",
                {"id": _eq(int(remaining[0]["id"])), "island_id": _eq(island_id)},
                {"is_main": True},
            )
    return {"deleted": True, "id": player_id}


def save_villager_state(
    island_id: int,
    villager_id: str,
    *,
    liked: bool | None,
    on_island: bool | None,
    camping_visited: bool | None,
    former_resident: bool | None,
) -> dict[str, Any]:
    current = get_villager_state_map(island_id).get(
        villager_id,
        {
            "liked": False,
            "on_island": False,
            "camping_visited": False,
            "former_resident": False,
            "island_order": 0,
        },
    )
    new_liked = current["liked"] if liked is None else bool(liked)
    new_on_island = current["on_island"] if on_island is None else bool(on_island)
    new_camping = current["camping_visited"] if camping_visited is None else bool(camping_visited)
    new_former = current["former_resident"] if former_resident is None else bool(former_resident)
    if new_on_island and not current["on_island"]:
        active_rows = [row for row in get_villager_state_map(island_id).values() if row.get("on_island")]
        if len(active_rows) >= 10:
            raise ValueError("up to 10 villagers can be on island")
        next_order = max([int(row.get("island_order") or 0) for row in active_rows] or [0]) + 1
    elif not new_on_island:
        next_order = 0
    else:
        next_order = int(current.get("island_order") or 0)

    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO villager_state (island_id, villager_id, liked, on_island, camping_visited, former_resident, island_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(island_id, villager_id) DO UPDATE SET
                    liked = excluded.liked,
                    on_island = excluded.on_island,
                    camping_visited = excluded.camping_visited,
                    former_resident = excluded.former_resident,
                    island_order = excluded.island_order,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (island_id, villager_id, _bool_int(new_liked), _bool_int(new_on_island), _bool_int(new_camping), _bool_int(new_former), next_order),
            )
    else:
        upsert_rows(
            "villager_state",
            [
                {
                    "island_id": island_id,
                    "villager_id": villager_id,
                    "liked": new_liked,
                    "on_island": new_on_island,
                    "camping_visited": new_camping,
                    "former_resident": new_former,
                    "island_order": next_order,
                }
            ],
            "island_id,villager_id",
        )
    return {
        "villager_id": villager_id,
        "liked": new_liked,
        "on_island": new_on_island,
        "camping_visited": new_camping,
        "former_resident": new_former,
    }


def save_villager_island_order(island_id: int, ordered_ids: list[str]) -> dict[str, Any]:
    current = get_villager_state_map(island_id)
    existing_ids = [villager_id for villager_id, row in current.items() if row.get("on_island")]
    if set(existing_ids) != set(ordered_ids):
        raise ValueError("island villager ids do not match current on-island list")
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            for idx, villager_id in enumerate(ordered_ids, start=1):
                conn.execute(
                    """
                    UPDATE villager_state
                    SET island_order = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE island_id = ? AND villager_id = ?
                    """,
                    (idx, island_id, villager_id),
                )
    else:
        for idx, villager_id in enumerate(ordered_ids, start=1):
            patch_rows(
                "villager_state",
                {"island_id": _eq(island_id), "villager_id": _eq(villager_id)},
                {"island_order": idx},
            )
    return {"ok": True, "count": len(ordered_ids)}


def save_catalog_state(
    island_id: int,
    catalog_type: str,
    item_id: str,
    *,
    owned: bool,
    donated: bool,
    quantity: int,
) -> None:
    qty = max(0, int(quantity or 0))
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            upsert_catalog_state(conn, island_id, catalog_type, item_id, owned, qty, donated)
        invalidate_catalog_state_caches(catalog_type, island_id)
        return
    upsert_rows(
        "catalog_state",
        [
            {
                "island_id": island_id,
                "catalog_type": catalog_type,
                "item_id": item_id,
                "owned": bool(owned),
                "donated": bool(donated),
                "quantity": qty,
            }
        ],
        "island_id,catalog_type,item_id",
    )
    invalidate_catalog_state_caches(catalog_type, island_id)


def save_all_variation_states(
    island_id: int,
    catalog_type: str,
    item_id: str,
    variation_ids: list[str],
    owned: bool,
) -> None:
    if not variation_ids:
        return
    rows = [
        {
            "island_id": island_id,
            "catalog_type": catalog_type,
            "item_id": item_id,
            "variation_id": variation_id,
            "owned": bool(owned),
            "quantity": 1 if owned else 0,
        }
        for variation_id in variation_ids
    ]
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            upsert_all_variation_states(conn, island_id, catalog_type, item_id, variation_ids, owned)
        invalidate_catalog_state_caches(catalog_type, island_id)
        return
    upsert_rows("catalog_variation_state", rows, "island_id,catalog_type,item_id,variation_id")
    invalidate_catalog_state_caches(catalog_type, island_id)


def save_catalog_variation_state(
    island_id: int,
    catalog_type: str,
    item_id: str,
    variation_id: str,
    *,
    owned: bool,
    quantity: int,
    all_variation_ids: list[str],
) -> bool:
    qty = max(0, int(quantity or 0))
    eff_owned = qty > 0 if quantity is not None else bool(owned)
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO catalog_variation_state (island_id, catalog_type, item_id, variation_id, owned, quantity)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(island_id, catalog_type, item_id, variation_id) DO UPDATE SET
                    owned = excluded.owned,
                    quantity = excluded.quantity,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (island_id, catalog_type, item_id, variation_id, int(eff_owned), qty),
            )
            item_owned = recalc_item_owned_from_variations(conn, island_id, catalog_type, item_id, all_variation_ids)
        invalidate_catalog_state_caches(catalog_type, island_id)
        return item_owned
    upsert_rows(
        "catalog_variation_state",
        [
            {
                "island_id": island_id,
                "catalog_type": catalog_type,
                "item_id": item_id,
                "variation_id": variation_id,
                "owned": eff_owned,
                "quantity": qty,
            }
        ],
        "island_id,catalog_type,item_id,variation_id",
    )
    item_owned = recalc_item_owned_from_variation_map(island_id, catalog_type, item_id, all_variation_ids)
    invalidate_catalog_state_caches(catalog_type, island_id)
    return item_owned


def save_catalog_variation_batch(
    island_id: int,
    catalog_type: str,
    item_id: str,
    items: list[dict[str, Any]],
    all_variation_ids: list[str],
) -> bool:
    if not items:
        return False
    rows = [
        {
            "island_id": island_id,
            "catalog_type": catalog_type,
            "item_id": item_id,
            "variation_id": str(row.get("variation_id") or ""),
            "owned": bool((max(0, int(row.get("quantity"))) > 0) if row.get("quantity") is not None else row.get("owned")),
            "quantity": int(max(0, int(row.get("quantity"))) if row.get("quantity") is not None else (1 if row.get("owned") else 0)),
        }
        for row in items
    ]
    if not _use_supabase_state_mode():
        init_db()
        with get_db() as conn:
            conn.executemany(
                """
                INSERT INTO catalog_variation_state (island_id, catalog_type, item_id, variation_id, owned, quantity)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(island_id, catalog_type, item_id, variation_id) DO UPDATE SET
                    owned = excluded.owned,
                    quantity = excluded.quantity,
                    updated_at = CURRENT_TIMESTAMP
                """,
                [
                    (row["island_id"], row["catalog_type"], row["item_id"], row["variation_id"], _bool_int(row["owned"]), row["quantity"])
                    for row in rows
                ],
            )
            item_owned = recalc_item_owned_from_variations(conn, island_id, catalog_type, item_id, all_variation_ids)
        invalidate_catalog_state_caches(catalog_type, island_id)
        return item_owned
    upsert_rows("catalog_variation_state", rows, "island_id,catalog_type,item_id,variation_id")
    item_owned = recalc_item_owned_from_variation_map(island_id, catalog_type, item_id, all_variation_ids)
    invalidate_catalog_state_caches(catalog_type, island_id)
    return item_owned


def recalc_item_owned_from_variation_map(
    island_id: int,
    catalog_type: str,
    item_id: str,
    variation_ids: list[str],
) -> bool:
    existing_state = get_catalog_state_map(island_id, catalog_type).get(item_id, {})
    existing_donated = bool(existing_state.get("donated"))
    if not variation_ids:
        save_catalog_state(island_id, catalog_type, item_id, owned=False, donated=existing_donated, quantity=0)
        return False
    variation_map = get_catalog_variation_state_map(island_id, catalog_type, item_id)
    owned_count = 0
    quantity_total = 0
    for variation_id in variation_ids:
        row = variation_map.get(variation_id, {})
        is_owned = bool(row.get("owned"))
        qty = max(0, int(row.get("quantity") or 0))
        if is_owned:
            owned_count += 1
        quantity_total += qty if qty > 0 else (1 if is_owned else 0)
    all_owned = owned_count == len(variation_ids)
    save_catalog_state(
        island_id,
        catalog_type,
        item_id,
        owned=all_owned,
        donated=existing_donated,
        quantity=quantity_total,
    )
    return all_owned
