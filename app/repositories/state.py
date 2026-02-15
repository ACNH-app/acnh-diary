from __future__ import annotations

import re
import sqlite3
from typing import Any

from app.core.db import get_db, init_db


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


def get_villager_state_map() -> dict[str, dict[str, bool]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT villager_id, liked, on_island, former_resident, island_order FROM villager_state"
        ).fetchall()
    return {
        str(r["villager_id"]): {
            "liked": bool(r["liked"]),
            "on_island": bool(r["on_island"]),
            "former_resident": bool(r["former_resident"]),
            "island_order": int(r["island_order"] or 0),
        }
        for r in rows
    }


def with_villager_state(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state_map = get_villager_state_map()
    merged = []
    for item in items:
        s = state_map.get(
            item["id"], {"liked": False, "on_island": False, "former_resident": False, "island_order": 0}
        )
        merged.append({**item, **s})
    return merged


def get_catalog_state_map(catalog_type: str) -> dict[str, dict[str, bool]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT item_id, owned FROM catalog_state WHERE catalog_type = ?",
            (catalog_type,),
        ).fetchall()
    return {str(r["item_id"]): {"owned": bool(r["owned"])} for r in rows}


def with_catalog_state(catalog_type: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state_map = get_catalog_state_map(catalog_type)
    merged = []
    for item in items:
        s = state_map.get(item["id"], {"owned": False})
        merged.append({**item, **s})
    return merged


def get_catalog_variation_state_map(
    catalog_type: str, item_id: str
) -> dict[str, dict[str, bool]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT variation_id, owned
            FROM catalog_variation_state
            WHERE catalog_type = ? AND item_id = ?
            """,
            (catalog_type, item_id),
        ).fetchall()
    return {str(r["variation_id"]): {"owned": bool(r["owned"])} for r in rows}


def upsert_catalog_state(
    conn: sqlite3.Connection, catalog_type: str, item_id: str, owned: bool
) -> None:
    conn.execute(
        """
        INSERT INTO catalog_state (catalog_type, item_id, owned)
        VALUES (?, ?, ?)
        ON CONFLICT(catalog_type, item_id) DO UPDATE SET
            owned = excluded.owned,
            updated_at = CURRENT_TIMESTAMP
        """,
        (catalog_type, item_id, int(owned)),
    )


def upsert_all_variation_states(
    conn: sqlite3.Connection,
    catalog_type: str,
    item_id: str,
    variation_ids: list[str],
    owned: bool,
) -> None:
    if not variation_ids:
        return
    conn.executemany(
        """
        INSERT INTO catalog_variation_state (catalog_type, item_id, variation_id, owned)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(catalog_type, item_id, variation_id) DO UPDATE SET
            owned = excluded.owned,
            updated_at = CURRENT_TIMESTAMP
        """,
        [(catalog_type, item_id, vid, int(owned)) for vid in variation_ids],
    )


def recalc_item_owned_from_variations(
    conn: sqlite3.Connection,
    catalog_type: str,
    item_id: str,
    variation_ids: list[str],
) -> bool:
    if not variation_ids:
        upsert_catalog_state(conn, catalog_type, item_id, False)
        return False
    placeholders = ",".join("?" for _ in variation_ids)
    row = conn.execute(
        f"""
        SELECT COUNT(*) AS owned_count
        FROM catalog_variation_state
        WHERE catalog_type = ? AND item_id = ? AND owned = 1
          AND variation_id IN ({placeholders})
        """,
        (catalog_type, item_id, *variation_ids),
    ).fetchone()
    owned_count = int(row["owned_count"] or 0) if row else 0
    all_owned = owned_count == len(variation_ids)
    upsert_catalog_state(conn, catalog_type, item_id, all_owned)
    return all_owned


def get_catalog_variation_owned_counts(catalog_type: str) -> dict[str, int]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT item_id, SUM(CASE WHEN owned = 1 THEN 1 ELSE 0 END) AS owned_count
            FROM catalog_variation_state
            WHERE catalog_type = ?
            GROUP BY item_id
            """,
            (catalog_type,),
        ).fetchall()
    return {str(r["item_id"]): int(r["owned_count"] or 0) for r in rows}


def with_catalog_variation_counts(
    catalog_type: str, items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    count_map = get_catalog_variation_owned_counts(catalog_type)
    return [{**x, "variation_owned_count": count_map.get(x["id"], 0)} for x in items]


def get_island_profile() -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT island_name, nickname, representative_fruit, representative_flower, birthday, hemisphere,
                   time_travel_enabled, game_datetime
            FROM island_profile
            WHERE id = 1
            """
        ).fetchone()
    if not row:
        return {
            "island_name": "",
            "nickname": "",
            "representative_fruit": "",
            "representative_flower": "",
            "birthday": "",
            "hemisphere": "north",
            "time_travel_enabled": False,
            "game_datetime": "",
        }
    return {
        "island_name": str(row["island_name"] or ""),
        "nickname": str(row["nickname"] or ""),
        "representative_fruit": str(row["representative_fruit"] or ""),
        "representative_flower": str(row["representative_flower"] or ""),
        "birthday": _normalize_month_day(str(row["birthday"] or "")),
        "hemisphere": str(row["hemisphere"] or "north"),
        "time_travel_enabled": bool(row["time_travel_enabled"]),
        "game_datetime": str(row["game_datetime"] or ""),
    }


def upsert_island_profile(
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
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO island_profile (
                id, island_name, nickname, representative_fruit, representative_flower, birthday, hemisphere,
                time_travel_enabled, game_datetime
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
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
                island_name.strip(),
                nickname.strip(),
                representative_fruit.strip(),
                representative_flower.strip(),
                birthday_mmdd,
                hemi,
                int(time_travel_enabled),
                game_datetime.strip(),
            ),
        )
    return get_island_profile()


def list_calendar_entries(month: str) -> list[dict[str, Any]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, visit_date, npc_name, note, checked
            FROM calendar_entry
            WHERE visit_date >= ? AND visit_date < ?
            ORDER BY visit_date ASC, id ASC
            """,
            (f"{month}-01", f"{month}-32"),
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


def list_calendar_entries_by_date(visit_date: str) -> list[dict[str, Any]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, visit_date, npc_name, note, checked
            FROM calendar_entry
            WHERE visit_date = ?
            ORDER BY id ASC
            """,
            (visit_date,),
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
                WHERE id = ?
                """,
                (visit_date, npc_name.strip(), note.strip(), int(checked), entry_id),
            )
            row = conn.execute(
                "SELECT id, visit_date, npc_name, note, checked FROM calendar_entry WHERE id = ?",
                (entry_id,),
            ).fetchone()
        else:
            conn.execute(
                """
                INSERT INTO calendar_entry (visit_date, npc_name, note, checked)
                VALUES (?, ?, ?, ?)
                """,
                (visit_date, npc_name.strip(), note.strip(), int(checked)),
            )
            row = conn.execute(
                """
                SELECT id, visit_date, npc_name, note, checked
                FROM calendar_entry
                WHERE id = last_insert_rowid()
                """,
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


def update_calendar_entry_checked(entry_id: int, checked: bool) -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        conn.execute(
            """
            UPDATE calendar_entry
            SET checked = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (int(checked), entry_id),
        )
        row = conn.execute(
            "SELECT id, visit_date, npc_name, note, checked FROM calendar_entry WHERE id = ?",
            (entry_id,),
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


def delete_calendar_entry(entry_id: int) -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        conn.execute("DELETE FROM calendar_entry WHERE id = ?", (entry_id,))
    return {"deleted": True, "id": entry_id}


def _normalize_player_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "name": str(row["name"] or ""),
        "birthday": _normalize_month_day(str(row["birthday"] or "")),
        "is_main": bool(row["is_main"]),
        "is_sub": bool(row["is_sub"]),
    }


def list_players() -> list[dict[str, Any]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, name, birthday, is_main, is_sub
            FROM player_profile
            ORDER BY is_main DESC, id ASC
            """
        ).fetchall()
    return [_normalize_player_row(r) for r in rows]


def upsert_player(
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
        raise ValueError("플레이어 이름은 필수입니다.")

    with get_db() as conn:
        if player_id:
            exists = conn.execute(
                "SELECT id FROM player_profile WHERE id = ?",
                (player_id,),
            ).fetchone()
            if not exists:
                raise ValueError("플레이어를 찾을 수 없습니다.")

            if is_main:
                conn.execute("UPDATE player_profile SET is_main = 0 WHERE id != ?", (player_id,))
            conn.execute(
                """
                UPDATE player_profile
                SET name = ?, birthday = ?, is_main = ?, is_sub = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (clean_name, birthday_mmdd, int(is_main), int(is_sub), player_id),
            )
            row = conn.execute(
                "SELECT id, name, birthday, is_main, is_sub FROM player_profile WHERE id = ?",
                (player_id,),
            ).fetchone()
        else:
            count_row = conn.execute("SELECT COUNT(*) AS cnt FROM player_profile").fetchone()
            count = int(count_row["cnt"] or 0) if count_row else 0
            if count >= 8:
                raise ValueError("플레이어는 최대 8명까지 등록할 수 있습니다.")

            has_main_row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM player_profile WHERE is_main = 1"
            ).fetchone()
            has_main = int(has_main_row["cnt"] or 0) > 0 if has_main_row else False
            target_main = bool(is_main) or not has_main
            if target_main:
                conn.execute("UPDATE player_profile SET is_main = 0")

            conn.execute(
                """
                INSERT INTO player_profile (name, birthday, is_main, is_sub)
                VALUES (?, ?, ?, ?)
                """,
                (clean_name, birthday_mmdd, int(target_main), int(is_sub)),
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


def set_main_player(player_id: int) -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        exists = conn.execute(
            "SELECT id FROM player_profile WHERE id = ?",
            (player_id,),
        ).fetchone()
        if not exists:
            raise ValueError("플레이어를 찾을 수 없습니다.")
        conn.execute("UPDATE player_profile SET is_main = 0")
        conn.execute(
            "UPDATE player_profile SET is_main = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (player_id,),
        )
        row = conn.execute(
            "SELECT id, name, birthday, is_main, is_sub FROM player_profile WHERE id = ?",
            (player_id,),
        ).fetchone()
    if not row:
        raise RuntimeError("main player update failed")
    return _normalize_player_row(row)


def delete_player(player_id: int) -> dict[str, Any]:
    init_db()
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, is_main FROM player_profile WHERE id = ?",
            (player_id,),
        ).fetchone()
        if not row:
            raise ValueError("플레이어를 찾을 수 없습니다.")

        was_main = bool(row["is_main"])
        conn.execute("DELETE FROM player_profile WHERE id = ?", (player_id,))

        if was_main:
            next_row = conn.execute(
                "SELECT id FROM player_profile ORDER BY id ASC LIMIT 1"
            ).fetchone()
            if next_row:
                conn.execute(
                    "UPDATE player_profile SET is_main = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (int(next_row["id"]),),
                )
    return {"deleted": True, "id": player_id}
