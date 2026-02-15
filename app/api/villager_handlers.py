from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.api.deps import VillagerHandlerDeps, VillagerHandlers
from app.schemas.state import VillagerStateIn, VillagerStateOut


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

        return {"count": len(villagers), "items": villagers}

    def update_villager_state(villager_id: str, payload: VillagerStateIn) -> VillagerStateOut:
        deps.init_db()
        if not any(v["id"] == villager_id for v in deps.load_villagers()):
            raise HTTPException(status_code=404, detail="주민을 찾을 수 없습니다.")

        with deps.get_db() as conn:
            existing = conn.execute(
                "SELECT liked, on_island, former_resident FROM villager_state WHERE villager_id = ?",
                (villager_id,),
            ).fetchone()

            current_liked = bool(existing["liked"]) if existing else False
            current_on_island = bool(existing["on_island"]) if existing else False
            current_former_resident = bool(existing["former_resident"]) if existing else False

            new_liked = payload.liked if payload.liked is not None else current_liked
            new_on_island = payload.on_island if payload.on_island is not None else current_on_island
            new_former_resident = (
                payload.former_resident
                if payload.former_resident is not None
                else current_former_resident
            )

            conn.execute(
                """
                INSERT INTO villager_state (villager_id, liked, on_island, former_resident)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(villager_id) DO UPDATE SET
                    liked = excluded.liked,
                    on_island = excluded.on_island,
                    former_resident = excluded.former_resident,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    villager_id,
                    int(new_liked),
                    int(new_on_island),
                    int(new_former_resident),
                ),
            )

        return VillagerStateOut(
            villager_id=villager_id,
            liked=bool(new_liked),
            on_island=bool(new_on_island),
            former_resident=bool(new_former_resident),
        )

    return VillagerHandlers(
        get_villagers=get_villagers,
        update_villager_state=update_villager_state,
    )
