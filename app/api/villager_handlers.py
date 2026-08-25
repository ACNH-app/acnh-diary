from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.api.deps import VillagerHandlerDeps, VillagerHandlers
from app.repositories.state import save_villager_island_order, save_villager_state
from app.schemas.state import VillagerIslandOrderIn, VillagerStateIn, VillagerStateOut


def create_villager_handlers(deps: VillagerHandlerDeps) -> VillagerHandlers:
    def get_villagers(
        island_id: int,
        q: str = "",
        personality: str = "",
        species: str = "",
        subtype: str = "",
        liked: bool | None = None,
        on_island: bool | None = None,
        former_resident: bool | None = None,
    ) -> dict[str, Any]:
        villagers = [
            {**villager, "subtype": str(villager.get("sub_personality") or "")}
            for villager in deps.with_villager_state(island_id, deps.load_villagers())
        ]

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
        if subtype:
            villagers = [v for v in villagers if str(v.get("sub_personality") or "") == subtype]
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

    def update_villager_state(island_id: int, villager_id: str, payload: VillagerStateIn) -> VillagerStateOut:
        if not any(v["id"] == villager_id for v in deps.load_villagers()):
            raise HTTPException(status_code=404, detail="Villager not found.")
        try:
            result = save_villager_state(
                island_id,
                villager_id,
                liked=payload.liked,
                on_island=payload.on_island,
                camping_visited=payload.camping_visited,
                former_resident=payload.former_resident,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return VillagerStateOut(
            villager_id=villager_id,
            liked=bool(result["liked"]),
            on_island=bool(result["on_island"]),
            camping_visited=bool(result["camping_visited"]),
            former_resident=bool(result["former_resident"]),
        )

    def update_island_order(island_id: int, payload: VillagerIslandOrderIn) -> dict[str, Any]:
        ordered_ids = [str(x).strip() for x in (payload.villager_ids or []) if str(x).strip()]
        if not ordered_ids:
            return {"ok": True}
        try:
            return save_villager_island_order(island_id, ordered_ids)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return VillagerHandlers(
        get_villagers=get_villagers,
        update_villager_state=update_villager_state,
        update_island_order=update_island_order,
    )
