from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.schemas.state import (
    CalendarCheckedIn,
    CalendarEntryIn,
    CalendarEntryOut,
    IslandProfileIn,
    IslandProfileOut,
    PlayerIn,
    PlayerOut,
)


def create_meta_router(
    *,
    home_handler: Callable[[], FileResponse],
    nav_handler: Callable[[], dict[str, Any]],
    villager_meta_handler: Callable[[], dict[str, Any]],
    home_summary_handler: Callable[[], dict[str, Any]],
    home_creatures_now_handler: Callable[..., dict[str, Any]],
    island_profile_handler: Callable[[], dict[str, Any]],
    update_island_profile_handler: Callable[..., dict[str, Any]],
    calendar_entries_handler: Callable[[str], list[dict[str, Any]]],
    calendar_annotations_handler: Callable[[str], list[dict[str, Any]]],
    calendar_entries_by_date_handler: Callable[[str], list[dict[str, Any]]],
    save_calendar_entry_handler: Callable[..., dict[str, Any]],
    set_calendar_entry_checked_handler: Callable[..., dict[str, Any]],
    remove_calendar_entry_handler: Callable[[int], dict[str, Any]],
    players_handler: Callable[[], list[dict[str, Any]]],
    save_player_handler: Callable[..., dict[str, Any]],
    set_main_player_handler: Callable[[int], dict[str, Any]],
    remove_player_handler: Callable[[int], dict[str, Any]],
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

    @router.get("/api/home/summary")
    def get_home_summary() -> dict[str, Any]:
        return home_summary_handler()

    @router.get("/api/home/creatures-now")
    def get_home_creatures_now(
        catalog_type: str = "all",
        owned: bool | None = None,
        donated: bool | None = None,
    ) -> dict[str, Any]:
        return home_creatures_now_handler(
            catalog_type=catalog_type,
            owned=owned,
            donated=donated,
        )

    @router.get("/api/profile", response_model=IslandProfileOut)
    def get_island_profile() -> dict[str, Any]:
        return island_profile_handler()

    @router.post("/api/profile", response_model=IslandProfileOut)
    def update_island_profile(payload: IslandProfileIn) -> dict[str, Any]:
        return update_island_profile_handler(
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
    def get_calendar_entries(month: str) -> list[dict[str, Any]]:
        return calendar_entries_handler(month)

    @router.get("/api/calendar/annotations")
    def get_calendar_annotations(month: str) -> list[dict[str, Any]]:
        return calendar_annotations_handler(month)

    @router.get("/api/calendar/day", response_model=list[CalendarEntryOut])
    def get_calendar_entries_by_date(date: str) -> list[dict[str, Any]]:
        return calendar_entries_by_date_handler(date)

    @router.post("/api/calendar", response_model=CalendarEntryOut)
    def save_calendar_entry(payload: CalendarEntryIn) -> dict[str, Any]:
        return save_calendar_entry_handler(
            payload.id,
            payload.visit_date,
            payload.npc_name,
            payload.note,
            payload.checked,
        )

    @router.post("/api/calendar/{entry_id}/checked", response_model=CalendarEntryOut)
    def set_calendar_entry_checked(entry_id: int, payload: CalendarCheckedIn) -> dict[str, Any]:
        return set_calendar_entry_checked_handler(entry_id, payload.checked)

    @router.delete("/api/calendar/{entry_id}")
    def remove_calendar_entry(entry_id: int) -> dict[str, Any]:
        return remove_calendar_entry_handler(entry_id)

    @router.get("/api/players", response_model=list[PlayerOut])
    def get_players() -> list[dict[str, Any]]:
        return players_handler()

    @router.post("/api/players", response_model=PlayerOut)
    def save_player(payload: PlayerIn) -> dict[str, Any]:
        return save_player_handler(
            payload.id,
            payload.name,
            payload.birthday,
            payload.is_main,
            payload.is_sub,
        )

    @router.post("/api/players/{player_id}/main", response_model=PlayerOut)
    def set_main_player(player_id: int) -> dict[str, Any]:
        return set_main_player_handler(player_id)

    @router.delete("/api/players/{player_id}")
    def remove_player(player_id: int) -> dict[str, Any]:
        return remove_player_handler(player_id)

    return router
