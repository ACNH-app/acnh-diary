from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from app.schemas.state import VillagerIslandOrderIn, VillagerStateIn, VillagerStateOut


def create_villager_router(
    *,
    get_villagers_handler: Callable[..., dict[str, Any]],
    update_villager_state_handler: Callable[..., VillagerStateOut],
    update_island_order_handler: Callable[..., dict[str, Any]],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/villagers")
    def get_villagers(
        q: str = "",
        personality: str = "",
        species: str = "",
        liked: bool | None = None,
        on_island: bool | None = None,
        former_resident: bool | None = None,
    ) -> dict[str, Any]:
        return get_villagers_handler(
            q=q,
            personality=personality,
            species=species,
            liked=liked,
            on_island=on_island,
            former_resident=former_resident,
        )

    @router.post("/api/villagers/{villager_id}/state", response_model=VillagerStateOut)
    def update_villager_state(villager_id: str, payload: VillagerStateIn) -> VillagerStateOut:
        return update_villager_state_handler(villager_id=villager_id, payload=payload)

    @router.post("/api/villagers/island-order")
    def update_island_order(payload: VillagerIslandOrderIn) -> dict[str, Any]:
        return update_island_order_handler(payload=payload)

    return router
