from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Header, HTTPException

from app.schemas.state import VillagerIslandOrderIn, VillagerStateIn, VillagerStateOut


def _resolve_island_id(x_island_id: str | None) -> int:
    text = str(x_island_id or "").strip()
    if not text:
        return 1
    try:
        island_id = int(text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid island id") from exc
    if island_id <= 0:
        raise HTTPException(status_code=400, detail="invalid island id")
    return island_id


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
        subtype: str = "",
        liked: bool | None = None,
        on_island: bool | None = None,
        former_resident: bool | None = None,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return get_villagers_handler(
            island_id=_resolve_island_id(x_island_id),
            q=q,
            personality=personality,
            species=species,
            subtype=subtype,
            liked=liked,
            on_island=on_island,
            former_resident=former_resident,
        )

    @router.post("/api/villagers/{villager_id}/state", response_model=VillagerStateOut)
    def update_villager_state(
        villager_id: str,
        payload: VillagerStateIn,
        x_island_id: str | None = Header(default=None),
    ) -> VillagerStateOut:
        return update_villager_state_handler(
            island_id=_resolve_island_id(x_island_id),
            villager_id=villager_id,
            payload=payload,
        )

    @router.post("/api/villagers/island-order")
    def update_island_order(
        payload: VillagerIslandOrderIn,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return update_island_order_handler(
            island_id=_resolve_island_id(x_island_id),
            payload=payload,
        )

    return router
