from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class MetaHandlerDeps:
    base_dir: Path
    catalog_types: dict[str, dict[str, Any]]
    load_villagers: Callable[[], list[dict[str, Any]]]
    load_personality_map: Callable[[], dict[str, str]]
    load_species_map: Callable[[], dict[str, str]]
    load_catalog: Callable[[str], list[dict[str, Any]]]
    get_island_profile: Callable[[], dict[str, Any]]
    upsert_island_profile: Callable[..., dict[str, Any]]
    list_calendar_entries: Callable[[str], list[dict[str, Any]]]
    list_calendar_entries_by_date: Callable[[str], list[dict[str, Any]]]
    upsert_calendar_entry: Callable[..., dict[str, Any]]
    update_calendar_entry_checked: Callable[..., dict[str, Any]]
    delete_calendar_entry: Callable[[int], dict[str, Any]]
    list_players: Callable[[], list[dict[str, Any]]]
    upsert_player: Callable[..., dict[str, Any]]
    set_main_player: Callable[[int], dict[str, Any]]
    delete_player: Callable[[int], dict[str, Any]]


@dataclass(frozen=True)
class VillagerHandlerDeps:
    load_villagers: Callable[[], list[dict[str, Any]]]
    with_villager_state: Callable[[list[dict[str, Any]]], list[dict[str, Any]]]
    init_db: Callable[[], None]
    get_db: Callable[..., Any]


@dataclass(frozen=True)
class CatalogHandlerDeps:
    catalog_types: dict[str, dict[str, Any]]
    load_catalog: Callable[[str], list[dict[str, Any]]]
    order_categories: Callable[[str, list[str]], list[str]]
    category_ko_for: Callable[[str, str], str]
    load_clothing_style_map: Callable[[], dict[str, str]]
    load_clothing_label_theme_map: Callable[[], dict[str, str]]
    with_catalog_state: Callable[[str, list[dict[str, Any]]], list[dict[str, Any]]]
    with_catalog_variation_counts: Callable[[str, list[dict[str, Any]]], list[dict[str, Any]]]
    sort_catalog_items: Callable[[list[dict[str, Any]], str, str], list[dict[str, Any]]]
    find_catalog_row: Callable[[str, str], dict[str, Any] | None]
    build_variations: Callable[[dict[str, Any]], list[dict[str, Any]]]
    fetch_single_catalog_row: Callable[[str, str], dict[str, Any] | None]
    get_catalog_variation_state_map: Callable[[str, str], dict[str, dict[str, Any]]]
    catalog_detail_payload: Callable[..., dict[str, Any]]
    variation_ids_for_item: Callable[[str, str], list[str]]
    upsert_catalog_state: Callable[..., None]
    upsert_all_variation_states: Callable[..., None]
    recalc_item_owned_from_variations: Callable[..., bool]
    invalidate_catalog_state_caches: Callable[[str | None], None]
    init_db: Callable[[], None]
    get_db: Callable[..., Any]
    load_recipe_tags: Callable[[], list[dict[str, Any]]]


@dataclass(frozen=True)
class AppHandlerDeps:
    meta: MetaHandlerDeps
    villagers: VillagerHandlerDeps
    catalog: CatalogHandlerDeps


@dataclass(frozen=True)
class MetaHandlers:
    home: Callable[[], Any]
    get_nav: Callable[[], dict[str, Any]]
    get_villager_meta: Callable[[], dict[str, Any]]
    get_home_summary: Callable[[], dict[str, Any]]
    get_island_profile: Callable[[], dict[str, Any]]
    update_island_profile: Callable[..., dict[str, Any]]
    get_calendar_entries: Callable[[str], list[dict[str, Any]]]
    get_calendar_annotations: Callable[[str], list[dict[str, Any]]]
    get_calendar_entries_by_date: Callable[[str], list[dict[str, Any]]]
    save_calendar_entry: Callable[..., dict[str, Any]]
    set_calendar_entry_checked: Callable[..., dict[str, Any]]
    remove_calendar_entry: Callable[[int], dict[str, Any]]
    get_players: Callable[[], list[dict[str, Any]]]
    save_player: Callable[..., dict[str, Any]]
    set_main_player: Callable[[int], dict[str, Any]]
    remove_player: Callable[[int], dict[str, Any]]


@dataclass(frozen=True)
class VillagerHandlers:
    get_villagers: Callable[..., dict[str, Any]]
    update_villager_state: Callable[..., Any]
    update_island_order: Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class CatalogHandlers:
    get_catalog_meta: Callable[..., dict[str, Any]]
    get_catalog: Callable[..., dict[str, Any]]
    get_catalog_detail: Callable[..., dict[str, Any]]
    update_catalog_state: Callable[..., Any]
    update_catalog_state_bulk: Callable[..., dict[str, Any]]
    update_catalog_variation_state: Callable[..., Any]
    update_catalog_variation_state_batch: Callable[..., dict[str, Any]]
    get_art_guide: Callable[..., dict[str, Any]]
    get_recipe_tags: Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class AppHandlers:
    meta: MetaHandlers
    villagers: VillagerHandlers
    catalog: CatalogHandlers
