from __future__ import annotations

import re
from datetime import datetime
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
from app.services.home_summary import parse_effective_now
from app.services.calendar_annotations import build_calendar_annotations
from app.services.catalog_data import _find_catalog_row


def create_meta_handlers(deps: MetaHandlerDeps) -> MetaHandlers:
    def _to_minutes(hour12: int, ampm: str) -> int:
        hour = int(hour12) % 12
        if str(ampm).strip().upper() == "PM":
            hour += 12
        return hour * 60

    def _time_text_matches_now(time_text: str, now: datetime) -> bool:
        raw = str(time_text or "").strip()
        if not raw:
            return False
        norm = raw.lower()
        if norm in {"all day", "all-day", "all_day"}:
            return True
        if norm in {"na", "none", "-", "n/a"}:
            return False

        current_min = now.hour * 60 + now.minute
        parts = [p.strip() for p in re.split(r"[,&/;]", raw) if p.strip()]
        if not parts:
            parts = [raw]

        for part in parts:
            m = re.search(
                r"(\d{1,2})\s*(AM|PM)\s*[–-]\s*(\d{1,2})\s*(AM|PM)",
                part,
                flags=re.IGNORECASE,
            )
            if not m:
                continue
            start_min = _to_minutes(int(m.group(1)), m.group(2))
            end_min = _to_minutes(int(m.group(3)), m.group(4))
            if start_min == end_min:
                return True
            if start_min < end_min:
                if start_min <= current_min < end_min:
                    return True
            else:
                if current_min >= start_min or current_min < end_min:
                    return True
        return False

    def _critter_rows_now(
        catalog_type: str,
        hemisphere: str,
        now: datetime,
        owned: bool | None,
        donated: bool | None,
    ) -> list[dict[str, Any]]:
        rows = deps.load_catalog(catalog_type)
        state_map = get_catalog_state_map(catalog_type)
        month = int(now.month)
        region_key = "south" if hemisphere == "south" else "north"
        out: list[dict[str, Any]] = []

        for item in rows:
            item_id = str(item.get("id") or "").strip()
            if not item_id:
                continue
            raw = _find_catalog_row(catalog_type, item_id) or {}
            region = raw.get(region_key) if isinstance(raw, dict) else {}
            if not isinstance(region, dict):
                continue

            months_array = region.get("months_array") if isinstance(region.get("months_array"), list) else []
            month_enabled = month in {int(x) for x in months_array if str(x).isdigit()}
            times_by_month = region.get("times_by_month") if isinstance(region.get("times_by_month"), dict) else {}
            month_time = str(times_by_month.get(str(month)) or "").strip()
            if not month_time and month_enabled:
                month_time = str(region.get("time") or region.get("times") or "").strip()

            available_now = month_enabled and _time_text_matches_now(month_time or "All day", now)
            if not available_now:
                continue

            s = state_map.get(item_id, {"owned": False, "donated": False})
            owned_bool = bool(s.get("owned"))
            donated_bool = bool(s.get("donated"))
            if owned is not None and owned_bool is not owned:
                continue
            if donated is not None and donated_bool is not donated:
                continue

            size = "-"
            if catalog_type in {"fish", "sea"}:
                size = str(raw.get("shadow_size") or raw.get("shadow") or "-").strip() or "-"
            elif str(raw.get("size") or "").strip():
                size = str(raw.get("size")).strip()

            location = str(raw.get("location") or raw.get("spawn_location") or "-").strip() or "-"
            months_text = str(region.get("months") or "-").strip() or "-"

            out.append(
                {
                    "id": item_id,
                    "catalog_type": catalog_type,
                    "number": int(item.get("number") or 0),
                    "name_ko": str(item.get("name_ko") or item.get("name") or "").strip(),
                    "name_en": str(item.get("name_en") or "").strip(),
                    "icon_url": str(item.get("image_url") or "").strip(),
                    "size": size,
                    "location": location,
                    "time": month_time or "All day",
                    "months": months_text,
                    "owned": owned_bool,
                    "donated": donated_bool,
                }
            )
        out.sort(key=lambda x: (int(x.get("number") or 0), str(x.get("name_ko") or x.get("name_en") or "")))
        return out

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

    def get_home_creatures_now(
        catalog_type: str = "all",
        owned: bool | None = None,
        donated: bool | None = None,
    ) -> dict[str, Any]:
        profile = deps.get_island_profile()
        now = parse_effective_now(profile)
        hemisphere = str(profile.get("hemisphere") or "north").strip().lower()
        if hemisphere not in {"north", "south"}:
            hemisphere = "north"

        type_key = str(catalog_type or "all").strip().lower()
        type_list = ["bugs", "fish", "sea"] if type_key == "all" else [type_key]
        if any(t not in {"bugs", "fish", "sea"} for t in type_list):
            raise HTTPException(status_code=400, detail="catalog_type은 all/bugs/fish/sea 중 하나여야 합니다.")

        items: list[dict[str, Any]] = []
        counts: dict[str, int] = {"bugs": 0, "fish": 0, "sea": 0}
        for t in type_list:
            rows = _critter_rows_now(t, hemisphere, now, owned, donated)
            counts[t] = len(rows)
            items.extend(rows)

        if type_key == "all":
            items.sort(
                key=lambda x: (
                    {"bugs": 0, "fish": 1, "sea": 2}.get(str(x.get("catalog_type")), 9),
                    int(x.get("number") or 0),
                    str(x.get("name_ko") or x.get("name_en") or ""),
                )
            )

        return {
            "effective_datetime": now.strftime("%Y-%m-%dT%H:%M"),
            "hemisphere": hemisphere,
            "catalog_type": type_key,
            "count": len(items),
            "counts_by_type": counts,
            "items": items,
        }

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
        get_home_creatures_now=get_home_creatures_now,
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
