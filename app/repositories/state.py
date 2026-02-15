from __future__ import annotations

import sqlite3
from typing import Any

from app.core.db import get_db, init_db


def get_villager_state_map() -> dict[str, dict[str, bool]]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT villager_id, liked, on_island, former_resident FROM villager_state"
        ).fetchall()
    return {
        str(r["villager_id"]): {
            "liked": bool(r["liked"]),
            "on_island": bool(r["on_island"]),
            "former_resident": bool(r["former_resident"]),
        }
        for r in rows
    }


def with_villager_state(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state_map = get_villager_state_map()
    merged = []
    for item in items:
        s = state_map.get(
            item["id"], {"liked": False, "on_island": False, "former_resident": False}
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
