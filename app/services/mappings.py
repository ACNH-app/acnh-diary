from __future__ import annotations

import html
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import (
    ART_NAME_MAP_PATH,
    BASE_DIR,
    CATALOG_TYPES,
    CLOTHING_CATEGORY_MAP_PATH,
    CLOTHING_LABEL_THEME_MAP_PATH,
    CLOTHING_STYLE_MAP_PATH,
    EVENT_COUNTRY_MAP_PATH,
    FOSSIL_NAME_MAP_PATH,
    FURNITURE_NAME_MAP_PATH,
    NAME_MAP_PATH,
    PERSONALITY_MAP_PATH,
    SPECIES_MAP_PATH,
    VILLAGER_SAYING_MAP_PATH,
)
from app.utils.text import normalize_name


def load_json_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        source = json.load(f)
    return {
        html.unescape(str(k)).strip(): html.unescape(str(v)).strip()
        for k, v in source.items()
        if html.unescape(str(k)).strip()
    }


def ensure_map_file(path: Path, default_map: dict[str, str]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(default_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def build_local_name_maps() -> None:
    local_base = BASE_DIR / "data" / "acnhapi"

    def add_name(target: dict[str, str], name_obj: Any) -> None:
        if not isinstance(name_obj, dict):
            return
        en = str(name_obj.get("name-USen") or name_obj.get("name-EUen") or "").strip()
        ko = str(name_obj.get("name-KRko") or "").strip()
        if en and ko:
            target[en] = ko

    if local_base.exists():
        furniture_map: dict[str, str] = {}
        for fn in ["houseware.json", "misc.json", "wallmounted.json"]:
            path = local_base / fn
            if not path.exists():
                continue
            try:
                source = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(source, dict):
                continue
            for variants in source.values():
                if isinstance(variants, list) and variants:
                    add_name(furniture_map, (variants[0] or {}).get("name"))

        fossils_map: dict[str, str] = {}
        fossils_path = local_base / "fossils.json"
        if fossils_path.exists():
            try:
                fossils = json.loads(fossils_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                fossils = {}
            if isinstance(fossils, dict):
                for row in fossils.values():
                    if isinstance(row, dict):
                        add_name(fossils_map, row.get("name"))

        def write_if_missing_or_empty(path: Path, data: dict[str, str]) -> None:
            if not data:
                return
            if path.exists():
                try:
                    existing = load_json_map(path)
                except json.JSONDecodeError:
                    existing = {}
                if existing:
                    return
            ensure_map_file(path, data)
            if path.exists() and load_json_map(path) != data:
                path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

        write_if_missing_or_empty(FURNITURE_NAME_MAP_PATH, furniture_map)
        write_if_missing_or_empty(FOSSIL_NAME_MAP_PATH, fossils_map)


def ensure_art_name_map_from_furniture() -> None:
    if not FURNITURE_NAME_MAP_PATH.exists():
        return
    try:
        furniture_map = load_json_map(FURNITURE_NAME_MAP_PATH)
    except Exception:
        furniture_map = {}
    if not furniture_map:
        return

    try:
        art_map = load_json_map(ART_NAME_MAP_PATH)
    except Exception:
        art_map = {}

    # 미술품 전용 맵이 비어 있으면, 기존 가구 한글 맵을 기본값으로 채운다.
    if art_map:
        return
    ART_NAME_MAP_PATH.write_text(
        json.dumps(furniture_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _normalize_name_map(path: Path) -> dict[str, str]:
    source = load_json_map(path)
    return {
        normalize_name(name_en): name_ko
        for name_en, name_ko in source.items()
        if name_ko.strip()
    }


@lru_cache(maxsize=1)
def load_korean_name_map() -> dict[str, str]:
    return _normalize_name_map(NAME_MAP_PATH)


@lru_cache(maxsize=1)
def load_personality_map() -> dict[str, str]:
    return load_json_map(PERSONALITY_MAP_PATH)


@lru_cache(maxsize=1)
def load_species_map() -> dict[str, str]:
    return load_json_map(SPECIES_MAP_PATH)


@lru_cache(maxsize=1)
def load_villager_saying_map() -> dict[str, str]:
    return _normalize_name_map(VILLAGER_SAYING_MAP_PATH)


@lru_cache(maxsize=1)
def load_clothing_category_map() -> dict[str, str]:
    return load_json_map(CLOTHING_CATEGORY_MAP_PATH)


@lru_cache(maxsize=1)
def load_clothing_style_map() -> dict[str, str]:
    return load_json_map(CLOTHING_STYLE_MAP_PATH)


@lru_cache(maxsize=1)
def load_clothing_label_theme_map() -> dict[str, str]:
    return load_json_map(CLOTHING_LABEL_THEME_MAP_PATH)


@lru_cache(maxsize=1)
def load_catalog_name_maps() -> dict[str, dict[str, str]]:
    maps: dict[str, dict[str, str]] = {}
    for catalog_type, cfg in CATALOG_TYPES.items():
        path = cfg["name_map_path"]
        maps[catalog_type] = _normalize_name_map(path)
    return maps


@lru_cache(maxsize=1)
def load_event_country_map() -> dict[str, str]:
    return load_json_map(EVENT_COUNTRY_MAP_PATH)


@lru_cache(maxsize=1)
def load_local_villager_catchphrase_ko_map() -> dict[str, str]:
    path = BASE_DIR / "data" / "acnhapi" / "villagers.json"
    if not path.exists():
        return {}
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(source, dict):
        return {}

    mapped: dict[str, str] = {}
    for row in source.values():
        if not isinstance(row, dict):
            continue
        name_obj = row.get("name") or {}
        catch_obj = row.get("catch-translations") or {}
        if not isinstance(name_obj, dict) or not isinstance(catch_obj, dict):
            continue

        name_en = str(name_obj.get("name-USen") or name_obj.get("name-EUen") or "").strip()
        catch_ko = str(catch_obj.get("catch-KRko") or "").strip()
        if name_en and catch_ko:
            mapped[normalize_name(name_en)] = catch_ko
    return mapped


@lru_cache(maxsize=1)
def load_local_music_name_ko_map() -> dict[str, str]:
    path = BASE_DIR / "data" / "acnhapi" / "music.json"
    if not path.exists():
        return {}
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(source, dict):
        return {}

    mapped: dict[str, str] = {}
    for row in source.values():
        if not isinstance(row, dict):
            continue
        name_obj = row.get("name") or {}
        if not isinstance(name_obj, dict):
            continue
        name_en = str(name_obj.get("name-USen") or name_obj.get("name-EUen") or "").strip()
        name_ko = str(name_obj.get("name-KRko") or "").strip()
        if name_en and name_ko:
            mapped[normalize_name(name_en)] = name_ko
    return mapped
