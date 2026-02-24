from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.api.deps import VillagerHandlerDeps, VillagerHandlers
from app.schemas.state import VillagerIslandOrderIn, VillagerStateIn, VillagerStateOut


def create_villager_handlers(deps: VillagerHandlerDeps) -> VillagerHandlers:
    def get_villagers(
        q: str = "",
        personality: str = "",
        species: str = "",
        liked: bool | None = None,
        on_island: bool | None = None,
        former_resident: bool | None = None,
    ) -> dict[str, Any]:
        villagers = deps.with_villager_state(deps.load_villagers())

        q_norm = q.strip().lower()
        if q_norm:
            villagers = [
                v
                for v in villagers
                if q_norm in v["name"].lower()
                or q_norm in v["name_ko"].lower()
                or q_norm in v["name_en"].lower()
            ]

        if personality:
            villagers = [v for v in villagers if v["personality"] == personality]
        if species:
            villagers = [v for v in villagers if v["species"] == species]
        if liked is not None:
            villagers = [v for v in villagers if v["liked"] is liked]
        if on_island is not None:
            villagers = [v for v in villagers if v["on_island"] is on_island]
        if former_resident is not None:
            villagers = [v for v in villagers if v["former_resident"] is former_resident]

        if on_island is True:
            villagers.sort(
                key=lambda v: (
                    int(v.get("island_order") or 0) if int(v.get("island_order") or 0) > 0 else 10_000_000,
                    str(v.get("name_ko") or v.get("name_en") or ""),
                )
            )

        return {"count": len(villagers), "items": villagers}

    def update_villager_state(villager_id: str, payload: VillagerStateIn) -> VillagerStateOut:
        deps.init_db()
        if not any(v["id"] == villager_id for v in deps.load_villagers()):
            raise HTTPException(status_code=404, detail="주민을 찾을 수 없습니다.")

        with deps.get_db() as conn:
            existing = conn.execute(
                "SELECT liked, on_island, camping_visited, former_resident, island_order FROM villager_state WHERE villager_id = ?",
                (villager_id,),
            ).fetchone()

            current_liked = bool(existing["liked"]) if existing else False
            current_on_island = bool(existing["on_island"]) if existing else False
            current_camping_visited = bool(existing["camping_visited"]) if existing else False
            current_former_resident = bool(existing["former_resident"]) if existing else False
            current_island_order = int(existing["island_order"] or 0) if existing else 0

            new_liked = payload.liked if payload.liked is not None else current_liked
            new_on_island = payload.on_island if payload.on_island is not None else current_on_island
            new_camping_visited = (
                payload.camping_visited
                if payload.camping_visited is not None
                else current_camping_visited
            )
            new_former_resident = (
                payload.former_resident
                if payload.former_resident is not None
                else current_former_resident
            )

            # 우리 섬 주민은 최대 10명까지만 허용
            if new_on_island and not current_on_island:
                row = conn.execute(
                    """
                    SELECT COUNT(*) AS cnt
                    FROM villager_state
                    WHERE on_island = 1 AND villager_id != ?
                    """,
                    (villager_id,),
                ).fetchone()
                on_island_count = int(row["cnt"] or 0) if row else 0
                if on_island_count >= 10:
                    raise HTTPException(status_code=400, detail="현재 섬 주민은 최대 10명까지 등록할 수 있습니다.")
                max_row = conn.execute(
                    "SELECT COALESCE(MAX(island_order), 0) AS max_order FROM villager_state WHERE on_island = 1"
                ).fetchone()
                next_order = int(max_row["max_order"] or 0) + 1
            elif not new_on_island:
                next_order = 0
            else:
                next_order = current_island_order or 0

            conn.execute(
                """
                INSERT INTO villager_state (villager_id, liked, on_island, camping_visited, former_resident, island_order)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(villager_id) DO UPDATE SET
                    liked = excluded.liked,
                    on_island = excluded.on_island,
                    camping_visited = excluded.camping_visited,
                    former_resident = excluded.former_resident,
                    island_order = excluded.island_order,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    villager_id,
                    int(new_liked),
                    int(new_on_island),
                    int(new_camping_visited),
                    int(new_former_resident),
                    int(next_order),
                ),
            )

        return VillagerStateOut(
            villager_id=villager_id,
            liked=bool(new_liked),
            on_island=bool(new_on_island),
            camping_visited=bool(new_camping_visited),
            former_resident=bool(new_former_resident),
        )

    def update_island_order(payload: VillagerIslandOrderIn) -> dict[str, Any]:
        deps.init_db()
        ordered_ids = [str(x).strip() for x in (payload.villager_ids or []) if str(x).strip()]
        if not ordered_ids:
            return {"ok": True}

        with deps.get_db() as conn:
            existing_rows = conn.execute(
                "SELECT villager_id FROM villager_state WHERE on_island = 1 ORDER BY island_order ASC, updated_at ASC"
            ).fetchall()
            existing_ids = [str(r["villager_id"]) for r in existing_rows]
            if set(existing_ids) != set(ordered_ids):
                raise HTTPException(status_code=400, detail="섬 주민 목록이 일치하지 않아 순서를 저장할 수 없습니다.")
            for idx, villager_id in enumerate(ordered_ids, start=1):
                conn.execute(
                    "UPDATE villager_state SET island_order = ?, updated_at = CURRENT_TIMESTAMP WHERE villager_id = ?",
                    (idx, villager_id),
                )

        return {"ok": True, "count": len(ordered_ids)}

    return VillagerHandlers(
        get_villagers=get_villagers,
        update_villager_state=update_villager_state,
        update_island_order=update_island_order,
    )
