from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse

from app.schemas.state import (
    CalendarCheckedIn,
    CalendarEntryIn,
    CalendarEntryOut,
    IslandCreateIn,
    IslandOut,
    IslandProfileIn,
    IslandProfileOut,
    PlayerIn,
    PlayerOut,
)


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


def create_meta_router(
    *,
    home_handler: Callable[[], FileResponse],
    nav_handler: Callable[[], dict[str, Any]],
    villager_meta_handler: Callable[[], dict[str, Any]],
    encyclopedia_monthly_targets_handler: Callable[[int], dict[str, Any]],
    islands_handler: Callable[[], list[dict[str, Any]]],
    create_island_handler: Callable[[str], dict[str, Any]],
    delete_island_handler: Callable[[int], dict[str, Any]],
    home_summary_handler: Callable[[int], dict[str, Any]],
    home_catalog_progress_handler: Callable[[int], list[dict[str, Any]]],
    home_creatures_now_handler: Callable[..., dict[str, Any]],
    island_profile_handler: Callable[[int], dict[str, Any]],
    update_island_profile_handler: Callable[..., dict[str, Any]],
    calendar_entries_handler: Callable[[int, str], list[dict[str, Any]]],
    calendar_annotations_handler: Callable[[int, str], list[dict[str, Any]]],
    calendar_entries_by_date_handler: Callable[[int, str], list[dict[str, Any]]],
    save_calendar_entry_handler: Callable[..., dict[str, Any]],
    set_calendar_entry_checked_handler: Callable[..., dict[str, Any]],
    remove_calendar_entry_handler: Callable[[int, int], dict[str, Any]],
    players_handler: Callable[[int], list[dict[str, Any]]],
    save_player_handler: Callable[..., dict[str, Any]],
    set_main_player_handler: Callable[[int, int], dict[str, Any]],
    remove_player_handler: Callable[[int, int], dict[str, Any]],
) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    def home() -> FileResponse:
        return home_handler()

    @router.get("/api/nav")
    def get_nav() -> dict[str, Any]:
        return nav_handler()

    @router.get("/api/meta")
    def get_villager_meta() -> dict[str, Any]:
        return villager_meta_handler()

    @router.get("/api/encyclopedia/monthly-targets")
    def get_encyclopedia_monthly_targets(x_island_id: str | None = Header(default=None)) -> dict[str, Any]:
        return encyclopedia_monthly_targets_handler(_resolve_island_id(x_island_id))

    @router.get("/api/islands", response_model=list[IslandOut])
    def get_islands() -> list[dict[str, Any]]:
        return islands_handler()

    @router.post("/api/islands", response_model=IslandOut)
    def create_island(payload: IslandCreateIn) -> dict[str, Any]:
        return create_island_handler(payload.name)

    @router.delete("/api/islands/{island_id}")
    def delete_island(island_id: int) -> dict[str, Any]:
        return delete_island_handler(island_id)

    @router.get("/api/home/summary")
    def get_home_summary(x_island_id: str | None = Header(default=None)) -> dict[str, Any]:
        return home_summary_handler(_resolve_island_id(x_island_id))

    @router.get("/api/home/catalog-progress")
    def get_home_catalog_progress(x_island_id: str | None = Header(default=None)) -> list[dict[str, Any]]:
        return home_catalog_progress_handler(_resolve_island_id(x_island_id))

    @router.get("/api/home/creatures-now")
    def get_home_creatures_now(
        catalog_type: str = "all",
        owned: bool | None = None,
        donated: bool | None = None,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return home_creatures_now_handler(
            _resolve_island_id(x_island_id),
            catalog_type=catalog_type,
            owned=owned,
            donated=donated,
        )

    @router.get("/api/profile", response_model=IslandProfileOut)
    def get_island_profile(x_island_id: str | None = Header(default=None)) -> dict[str, Any]:
        return island_profile_handler(_resolve_island_id(x_island_id))

    @router.post("/api/profile", response_model=IslandProfileOut)
    def update_island_profile(
        payload: IslandProfileIn,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return update_island_profile_handler(
            _resolve_island_id(x_island_id),
            payload.island_name,
            payload.nickname,
            payload.representative_fruit,
            payload.representative_flower,
            payload.birthday,
            payload.hemisphere,
            payload.time_travel_enabled,
            payload.game_datetime,
        )

    @router.get("/api/calendar", response_model=list[CalendarEntryOut])
    def get_calendar_entries(
        month: str,
        x_island_id: str | None = Header(default=None),
    ) -> list[dict[str, Any]]:
        return calendar_entries_handler(_resolve_island_id(x_island_id), month)

    @router.get("/api/calendar/annotations")
    def get_calendar_annotations(
        month: str,
        x_island_id: str | None = Header(default=None),
    ) -> list[dict[str, Any]]:
        return calendar_annotations_handler(_resolve_island_id(x_island_id), month)

    @router.get("/api/calendar/day", response_model=list[CalendarEntryOut])
    def get_calendar_entries_by_date(
        date: str,
        x_island_id: str | None = Header(default=None),
    ) -> list[dict[str, Any]]:
        return calendar_entries_by_date_handler(_resolve_island_id(x_island_id), date)

    @router.post("/api/calendar", response_model=CalendarEntryOut)
    def save_calendar_entry(
        payload: CalendarEntryIn,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return save_calendar_entry_handler(
            _resolve_island_id(x_island_id),
            payload.id,
            payload.visit_date,
            payload.npc_name,
            payload.note,
            payload.checked,
        )

    @router.post("/api/calendar/{entry_id}/checked", response_model=CalendarEntryOut)
    def set_calendar_entry_checked(
        entry_id: int,
        payload: CalendarCheckedIn,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return set_calendar_entry_checked_handler(
            _resolve_island_id(x_island_id),
            entry_id,
            payload.checked,
        )

    @router.delete("/api/calendar/{entry_id}")
    def remove_calendar_entry(
        entry_id: int,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return remove_calendar_entry_handler(_resolve_island_id(x_island_id), entry_id)

    @router.get("/api/players", response_model=list[PlayerOut])
    def get_players(x_island_id: str | None = Header(default=None)) -> list[dict[str, Any]]:
        return players_handler(_resolve_island_id(x_island_id))

    @router.post("/api/players", response_model=PlayerOut)
    def save_player(
        payload: PlayerIn,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return save_player_handler(
            _resolve_island_id(x_island_id),
            payload.id,
            payload.name,
            payload.birthday,
            payload.is_main,
            payload.is_sub,
        )

    @router.post("/api/players/{player_id}/main", response_model=PlayerOut)
    def set_main_player(
        player_id: int,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return set_main_player_handler(_resolve_island_id(x_island_id), player_id)

    @router.delete("/api/players/{player_id}")
    def remove_player(
        player_id: int,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return remove_player_handler(_resolve_island_id(x_island_id), player_id)

    return router
