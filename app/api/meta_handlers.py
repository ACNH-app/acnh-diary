from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from fastapi.responses import FileResponse

from app.api.deps import MetaHandlerDeps, MetaHandlers
from app.repositories.state import (
    get_catalog_state_map,
    get_catalog_variation_owned_counts,
)
from app.services.home_summary import build_home_summary
from app.services.home_summary import catalog_progress_summary
from app.services.calendar_annotations import build_calendar_annotations


def create_meta_handlers(deps: MetaHandlerDeps) -> MetaHandlers:
    def home() -> FileResponse:
        return FileResponse(deps.base_dir / "static" / "index.html")

    def get_nav() -> dict[str, Any]:
        return {
            "modes": [
                {"key": "home", "label": "홈"},
                {"key": "villagers", "label": "주민"},
                *[
                    {"key": key, "label": cfg["label"]}
                    for key, cfg in deps.catalog_types.items()
                ],
            ]
        }

    def get_villager_meta() -> dict[str, Any]:
        villagers = deps.load_villagers()
        personality_map = deps.load_personality_map()
        species_map = deps.load_species_map()
        personalities = sorted({v["personality"] for v in villagers})
        species = sorted({v["species"] for v in villagers})
        return {
            "personalities": [
                {"en": p, "ko": personality_map.get(p, p)} for p in personalities
            ],
            "species": [{"en": s, "ko": species_map.get(s, s)} for s in species],
        }

    def get_home_summary() -> dict[str, Any]:
        profile = deps.get_island_profile()
        events = deps.load_catalog("events")
        base = build_home_summary(profile, events)
        base["catalog_progress"] = catalog_progress_summary(
            deps.load_catalog,
            get_catalog_state_map,
            get_catalog_variation_owned_counts,
        )
        return base

    def get_island_profile() -> dict[str, Any]:
        return deps.get_island_profile()

    def update_island_profile(
        island_name: str,
        nickname: str,
        representative_fruit: str,
        representative_flower: str,
        birthday: str,
        hemisphere: str,
        time_travel_enabled: bool,
        game_datetime: str,
    ) -> dict[str, Any]:
        return deps.upsert_island_profile(
            island_name,
            nickname,
            representative_fruit,
            representative_flower,
            birthday,
            hemisphere,
            time_travel_enabled,
            game_datetime,
        )

    def get_calendar_entries(month: str) -> list[dict[str, Any]]:
        return deps.list_calendar_entries(month)

    def get_calendar_annotations(month: str) -> list[dict[str, Any]]:
        profile = deps.get_island_profile()
        hemi = str(profile.get("hemisphere") or "north")
        villagers = deps.load_villagers()
        events = deps.load_catalog("events")
        return build_calendar_annotations(
            month=month,
            hemisphere=hemi,
            villagers=villagers,
            events=events,
        )

    def get_calendar_entries_by_date(visit_date: str) -> list[dict[str, Any]]:
        return deps.list_calendar_entries_by_date(visit_date)

    def save_calendar_entry(
        entry_id: int | None,
        visit_date: str,
        npc_name: str,
        note: str,
        checked: bool,
    ) -> dict[str, Any]:
        return deps.upsert_calendar_entry(visit_date, npc_name, note, checked, entry_id)

    def set_calendar_entry_checked(entry_id: int, checked: bool) -> dict[str, Any]:
        return deps.update_calendar_entry_checked(entry_id, checked)

    def remove_calendar_entry(entry_id: int) -> dict[str, Any]:
        return deps.delete_calendar_entry(entry_id)

    def get_players() -> list[dict[str, Any]]:
        return deps.list_players()

    def save_player(
        player_id: int | None,
        name: str,
        birthday: str,
        is_main: bool,
        is_sub: bool,
    ) -> dict[str, Any]:
        try:
            return deps.upsert_player(name, birthday, is_main, is_sub, player_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def set_main_player(player_id: int) -> dict[str, Any]:
        try:
            return deps.set_main_player(player_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    def remove_player(player_id: int) -> dict[str, Any]:
        try:
            return deps.delete_player(player_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return MetaHandlers(
        home=home,
        get_nav=get_nav,
        get_villager_meta=get_villager_meta,
        get_home_summary=get_home_summary,
        get_island_profile=get_island_profile,
        update_island_profile=update_island_profile,
        get_calendar_entries=get_calendar_entries,
        get_calendar_annotations=get_calendar_annotations,
        get_calendar_entries_by_date=get_calendar_entries_by_date,
        save_calendar_entry=save_calendar_entry,
        set_calendar_entry_checked=set_calendar_entry_checked,
        remove_calendar_entry=remove_calendar_entry,
        get_players=get_players,
        save_player=save_player,
        set_main_player=set_main_player,
        remove_player=remove_player,
    )
