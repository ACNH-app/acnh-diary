from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import Any
from urllib.parse import quote

from app.core.config import CATALOG_SINGLE_PATHS, CATALOG_TYPES
from app.domain.catalog import category_ko_for, normalize_furniture_category
from app.services.mappings import (
    load_catalog_name_maps,
    load_clothing_label_theme_map,
    load_clothing_style_map,
    load_korean_name_map,
    load_personality_map,
    load_species_map,
)
from app.services.nookipedia_client import (
    fetch_nookipedia,
    load_nookipedia_catalog,
    load_nookipedia_villagers,
)
from app.services.source import extract_source_pair
from app.utils.text import normalize_name


@lru_cache(maxsize=1)
def load_villagers() -> list[dict[str, Any]]:
    ko_name_map = load_korean_name_map()
    personality_map = load_personality_map()
    species_map = load_species_map()
    rows = load_nookipedia_villagers()

    villagers: list[dict[str, Any]] = []
    for row in rows:
        name_en = str(row.get("name") or "").strip()
        if not name_en:
            continue

        nh = row.get("nh_details") or {}
        personality = str(row.get("personality") or "")
        species = str(row.get("species") or "")
        name_ko = ko_name_map.get(normalize_name(name_en), "")

        birthday_month = str(row.get("birthday_month") or "").strip()
        birthday_day = str(row.get("birthday_day") or "").strip()
        birthday = " ".join(p for p in [birthday_month, birthday_day] if p)

        villagers.append(
            {
                "id": str(row.get("id") or ""),
                "name": name_ko or name_en,
                "name_ko": name_ko,
                "name_en": name_en,
                "species": species,
                "species_ko": species_map.get(species, species),
                "personality": personality,
                "personality_ko": personality_map.get(personality, personality),
                "gender": str(row.get("gender") or ""),
                "hobby": str(nh.get("hobby") or ""),
                "birthday": birthday,
                "saying": str(row.get("quote") or ""),
                "icon_uri": str(nh.get("icon_url") or ""),
                "image_uri": str(nh.get("image_url") or row.get("image_url") or ""),
            }
        )

    villagers = [v for v in villagers if v["id"]]
    villagers.sort(key=lambda v: (v["name_ko"] or v["name_en"]).lower())
    return villagers


def _item_id(catalog_type: str, row: dict[str, Any], name_en: str) -> str:
    url = str(row.get("url") or "").strip()
    key = f"{catalog_type}:{url or name_en}".lower().encode("utf-8")
    return hashlib.sha1(key).hexdigest()[:16]


def _extract_image_url(row: dict[str, Any]) -> str:
    image_url = str(row.get("image_url") or row.get("icon_url") or "").strip()
    if image_url:
        return image_url
    variations = row.get("variations")
    if isinstance(variations, list):
        for v in variations:
            if isinstance(v, dict):
                candidate = str(v.get("image_url") or v.get("icon_url") or "").strip()
                if candidate:
                    return candidate
    return ""


def _make_catalog_item(catalog_type: str, row: dict[str, Any]) -> dict[str, Any] | None:
    if catalog_type == "events":
        name_en = str(row.get("event") or "").strip()
    else:
        name_en = str(row.get("name") or "").strip()

    if not name_en:
        return None

    name_maps = load_catalog_name_maps()
    name_ko = name_maps.get(catalog_type, {}).get(normalize_name(name_en), "")

    category = str(row.get("category") or "").strip()
    if catalog_type == "furniture":
        category = normalize_furniture_category(category)
    extra_filter = ""
    extra_filter_values: list[str] = []

    if catalog_type == "events":
        category = str(row.get("type") or "").strip()
    if catalog_type == "clothing":
        extra_filter = "style"
        extra_filter_values = [str(v) for v in (row.get("styles") or []) if str(v).strip()]

    source, source_notes = extract_source_pair(row)

    item = {
        "id": _item_id(catalog_type, row, name_en),
        "name": name_ko or name_en,
        "name_ko": name_ko,
        "name_en": name_en,
        "url": str(row.get("url") or ""),
        "image_url": _extract_image_url(row),
        "category": category,
        "category_ko": category_ko_for(catalog_type, category),
        "extra_filter": extra_filter,
        "extra_filter_values": extra_filter_values,
        "date": str(row.get("date") or "").strip(),
        "event_type": str(row.get("type") or "").strip(),
        "sell": int(row.get("sell") or 0),
        "variation_total": int(row.get("variation_total") or 0),
        "source": source,
        "source_notes": source_notes,
    }

    if catalog_type == "clothing":
        styles = [str(v) for v in (row.get("styles") or []) if str(v).strip()]
        label_themes = [str(v) for v in (row.get("label_themes") or []) if str(v).strip()]
        style_map = load_clothing_style_map()
        label_theme_map = load_clothing_label_theme_map()
        item["styles"] = styles
        item["styles_ko"] = [style_map.get(v, v) for v in styles]
        item["label_themes"] = label_themes
        item["label_themes_ko"] = [label_theme_map.get(v, v) for v in label_themes]

    return item


def _find_catalog_row(catalog_type: str, item_id: str) -> dict[str, Any] | None:
    return _catalog_row_index(catalog_type).get(item_id)


@lru_cache(maxsize=None)
def _catalog_row_index(catalog_type: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in load_nookipedia_catalog(catalog_type):
        if not isinstance(row, dict):
            continue
        if catalog_type == "events":
            name_en = str(row.get("event") or "").strip()
        else:
            name_en = str(row.get("name") or "").strip()
        if not name_en:
            continue
        index[_item_id(catalog_type, row, name_en)] = row
    return index


@lru_cache(maxsize=4096)
def _fetch_single_catalog_row(catalog_type: str, name_en: str) -> dict[str, Any] | None:
    pattern = CATALOG_SINGLE_PATHS.get(catalog_type)
    if not pattern or not name_en:
        return None
    path = pattern.format(name=quote(name_en, safe=""))
    result = fetch_nookipedia(path)
    if isinstance(result, dict):
        return result
    return None


def _build_variations(detail: dict[str, Any]) -> list[dict[str, Any]]:
    variations = detail.get("variations")
    if not isinstance(variations, list):
        return []
    rows: list[dict[str, Any]] = []
    for idx, v in enumerate(variations):
        if not isinstance(v, dict):
            continue
        rows.append(
            {
                "id": str(v.get("internal_id") or idx),
                "label": str(v.get("variation") or v.get("name") or f"variation {idx + 1}"),
                "image_url": str(v.get("image_url") or v.get("icon_url") or ""),
                "color1": str(v.get("color_1") or v.get("color1") or ""),
                "color2": str(v.get("color_2") or v.get("color2") or ""),
                "pattern": str(v.get("pattern") or ""),
                "source": str(v.get("source") or ""),
                "source_notes": str(v.get("source_notes") or ""),
                "price": int(v.get("buy") or v.get("sell") or 0),
            }
        )
    return rows


@lru_cache(maxsize=8192)
def _variation_ids_for_item(catalog_type: str, item_id: str) -> list[str]:
    base_row = _find_catalog_row(catalog_type, item_id)
    if not base_row:
        return []

    variation_ids = [v["id"] for v in _build_variations(base_row)]
    if variation_ids:
        return variation_ids

    name_en = str(base_row.get("event") or base_row.get("name") or "").strip()
    if not name_en:
        return []
    try:
        single_row = _fetch_single_catalog_row(catalog_type, name_en)
    except Exception:
        single_row = None
    if not single_row:
        return []
    return [v["id"] for v in _build_variations(single_row)]


def _raw_top_level_fields(detail: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for key in sorted(detail.keys()):
        if key == "variations":
            continue
        value = detail.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            rendered = "" if value is None else str(value)
        else:
            rendered = json.dumps(value, ensure_ascii=False)
        if rendered:
            rows.append({"key": key, "value": rendered})
    return rows


def _catalog_detail_payload(
    catalog_type: str,
    item: dict[str, Any],
    detail: dict[str, Any],
    from_single: bool,
    variation_state_map: dict[str, dict[str, bool]] | None = None,
) -> dict[str, Any]:
    category = str(detail.get("category") or item.get("category") or "")
    detail_source, detail_source_notes = extract_source_pair(detail)
    common_fields = [
        ("카테고리", category),
        ("판매가", str(detail.get("sell") or item.get("sell") or "")),
        ("출처", detail_source or str(item.get("source") or "")),
        (
            "출처 상세",
            detail_source_notes or str(item.get("source_notes") or ""),
        ),
        ("설명", str(detail.get("notes") or detail.get("description") or "")),
        ("URL", str(detail.get("url") or item.get("url") or "")),
    ]
    fields = [{"label": k, "value": v} for k, v in common_fields if v]
    variations = _build_variations(detail)
    if variation_state_map:
        variations = [{**v, **variation_state_map.get(v["id"], {"owned": False})} for v in variations]
    else:
        variations = [{**v, "owned": False} for v in variations]

    return {
        "item": item,
        "from_single_endpoint": from_single,
        "summary": {
            "name_en": str(detail.get("name") or item.get("name_en") or ""),
            "image_url": _extract_image_url(detail) or item.get("image_url") or "",
            "category": category,
            "event_type": str(detail.get("type") or item.get("event_type") or ""),
            "date": str(detail.get("date") or item.get("date") or ""),
            "variation_total": int(detail.get("variation_total") or item.get("variation_total") or 0),
        },
        "fields": fields,
        "variations": variations,
        "raw_fields": _raw_top_level_fields(detail),
    }


@lru_cache(maxsize=None)
def load_catalog(catalog_type: str) -> list[dict[str, Any]]:
    if catalog_type not in CATALOG_TYPES:
        raise KeyError(catalog_type)

    rows = load_nookipedia_catalog(catalog_type)
    items: list[dict[str, Any]] = []

    for row in rows:
        if not isinstance(row, dict):
            continue
        item = _make_catalog_item(catalog_type, row)
        if item:
            items.append(item)

    items.sort(key=lambda x: (x["name_ko"] or x["name_en"]).lower())
    return items
