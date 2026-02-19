from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from typing import Any
from urllib.parse import quote

from app.core.config import BASE_DIR, CATALOG_SINGLE_PATHS, CATALOG_TYPES
from app.domain.catalog import category_ko_for, normalize_furniture_category, normalize_recipe_category
from app.services.mappings import (
    load_catalog_name_maps,
    load_clothing_label_theme_map,
    load_clothing_style_map,
    load_event_country_map,
    load_korean_name_map,
    load_local_villager_catchphrase_ko_map,
    load_local_music_name_ko_map,
    load_personality_map,
    load_species_map,
    load_villager_saying_map,
)
from app.services.nookipedia_client import (
    fetch_nookipedia,
    load_nookipedia_catalog,
    load_nookipedia_villagers,
)
from app.services.source import extract_source_pair, translate_source_value_to_ko
from app.utils.text import normalize_name

REACTIONS_DATA_PATH = BASE_DIR / "data" / "norviah-animal-crossing" / "reactions.json"
REACTIONS_DATA_PATH_ALT = BASE_DIR / "data" / "norviah-animal-crossing" / "Reactions.json"
REACTIONS_TRANSLATION_PATH = (
    BASE_DIR / "data" / "norviah-animal-crossing" / "Reactions-translation.json"
)
RECIPES_DATA_PATH = BASE_DIR / "data" / "norviah-animal-crossing" / "recipes.json"


@lru_cache(maxsize=1)
def load_local_reactions() -> list[dict[str, Any]]:
    path = REACTIONS_DATA_PATH if REACTIONS_DATA_PATH.exists() else REACTIONS_DATA_PATH_ALT
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return payload if isinstance(payload, list) else []


@lru_cache(maxsize=1)
def load_local_reaction_translation_map() -> dict[str, str]:
    if not REACTIONS_TRANSLATION_PATH.exists():
        return {}
    try:
        payload = json.loads(REACTIONS_TRANSLATION_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, list):
        return {}
    out: dict[str, str] = {}
    for row in payload:
        if not isinstance(row, dict):
            continue
        name_en = str(row.get("name") or "").strip()
        name_ko = str(row.get("korean") or row.get("ko") or "").strip()
        if name_en and name_ko:
            out[normalize_name(name_en)] = name_ko
    return out


@lru_cache(maxsize=1)
def load_local_recipes_by_name() -> dict[str, dict[str, Any]]:
    if not RECIPES_DATA_PATH.exists():
        return {}
    try:
        payload = json.loads(RECIPES_DATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in payload:
        if not isinstance(row, dict):
            continue
        name_en = str(row.get("name") or "").strip()
        if not name_en:
            continue
        out[normalize_name(name_en)] = row
    return out


@lru_cache(maxsize=1)
def load_villagers() -> list[dict[str, Any]]:
    ko_name_map = load_korean_name_map()
    saying_ko_map = load_villager_saying_map()
    catchphrase_ko_map = load_local_villager_catchphrase_ko_map()
    music_ko_map = load_local_music_name_ko_map()
    personality_map = load_personality_map()
    species_map = load_species_map()
    rows = load_nookipedia_villagers()
    try:
        rows_ko = load_nookipedia_villagers("ko")
    except Exception:
        rows_ko = []

    rows_ko_by_id: dict[str, dict[str, Any]] = {}
    for row_ko in rows_ko:
        row_id = str((row_ko or {}).get("id") or "").strip()
        if row_id:
            rows_ko_by_id[row_id] = row_ko

    villagers: list[dict[str, Any]] = []
    for row in rows:
        name_en = str(row.get("name") or "").strip()
        if not name_en:
            continue

        row_id = str(row.get("id") or "").strip()
        row_ko = rows_ko_by_id.get(row_id, {})
        nh = row.get("nh_details") or {}
        personality = str(row.get("personality") or "")
        species = str(row.get("species") or "")
        name_ko = ko_name_map.get(normalize_name(name_en), "")
        saying_ko = str((row_ko or {}).get("quote") or "").strip()
        if not saying_ko:
            saying_ko = saying_ko_map.get(normalize_name(name_en), "")
        catchphrase_ko = str((row_ko or {}).get("phrase") or "").strip()
        if not catchphrase_ko:
            catchphrase_ko = catchphrase_ko_map.get(normalize_name(name_en), "")
        favorite_colors = [str(v).strip() for v in (nh.get("fav_colors") or []) if str(v).strip()]
        favorite_styles = [str(v).strip() for v in (nh.get("fav_styles") or []) if str(v).strip()]
        prev_phrases = [str(v).strip() for v in (row.get("prev_phrases") or []) if str(v).strip()]
        appearances = [str(v).strip() for v in (row.get("appearances") or []) if str(v).strip()]
        house_music = str(nh.get("house_music") or "").strip()
        house_music_ko = music_ko_map.get(normalize_name(house_music), "")

        birthday_month = str(row.get("birthday_month") or "").strip()
        birthday_day = str(row.get("birthday_day") or "").strip()
        birthday = " ".join(p for p in [birthday_month, birthday_day] if p)

        villagers.append(
            {
                "id": row_id,
                "name": name_ko or name_en,
                "name_ko": name_ko,
                "name_en": name_en,
                "species": species,
                "species_ko": species_map.get(species, species),
                "personality": personality,
                "personality_ko": personality_map.get(personality, personality),
                "sub_personality": str(nh.get("sub-personality") or ""),
                "gender": str(row.get("gender") or ""),
                "hobby": str(nh.get("hobby") or ""),
                "sign": str(row.get("sign") or ""),
                "debut": str(row.get("debut") or ""),
                "title_color": str(row.get("title_color") or ""),
                "text_color": str(row.get("text_color") or ""),
                "birthday": birthday,
                "birthday_month": birthday_month,
                "birthday_day": birthday_day,
                "phrase": str(row.get("phrase") or ""),
                "prev_phrases": prev_phrases,
                "catchphrase": str(nh.get("catchphrase") or row.get("phrase") or ""),
                "catchphrase_ko": catchphrase_ko,
                "saying": str(row.get("quote") or ""),
                "saying_ko": saying_ko,
                "favorite_colors": favorite_colors,
                "favorite_styles": favorite_styles,
                "default_clothing": str(nh.get("clothing") or row.get("clothing") or ""),
                "default_clothing_variation": str(nh.get("clothing_variation") or ""),
                "default_umbrella": str(nh.get("umbrella") or ""),
                "islander": bool(row.get("islander")),
                "appearances": appearances,
                "photo_url": str(nh.get("photo_url") or ""),
                "house_exterior_url": str(nh.get("house_exterior_url") or ""),
                "house_interior_url": str(nh.get("house_interior_url") or ""),
                "house_wallpaper": str(nh.get("house_wallpaper") or ""),
                "house_flooring": str(nh.get("house_flooring") or ""),
                "house_music": house_music,
                "house_music_ko": house_music_ko,
                "house_music_note": str(nh.get("house_music_note") or ""),
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
    image_url = str(
        row.get("image_url")
        or row.get("icon_url")
        or row.get("image")
        or row.get("real_image_url")
        or row.get("real_art_url")
        or row.get("fake_image_url")
        or row.get("texture_url")
        or row.get("highResTexture")
        or ""
    ).strip()
    if image_url.startswith("//"):
        image_url = f"https:{image_url}"
    if image_url:
        return image_url
    real_info = row.get("real_info")
    if isinstance(real_info, dict):
        nested = str(real_info.get("image_url") or real_info.get("texture_url") or "").strip()
        if nested.startswith("//"):
            nested = f"https:{nested}"
        if nested:
            return nested
    fake_info = row.get("fake_info")
    if isinstance(fake_info, dict):
        nested = str(fake_info.get("image_url") or fake_info.get("texture_url") or "").strip()
        if nested.startswith("//"):
            nested = f"https:{nested}"
        if nested:
            return nested
    variations = row.get("variations")
    if isinstance(variations, list):
        for v in variations:
            if isinstance(v, dict):
                candidate = str(v.get("image_url") or v.get("icon_url") or "").strip()
                if candidate:
                    return candidate
    return ""


def _first_non_empty(row: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _first_bool(row: dict[str, Any], keys: list[str], default: bool = False) -> bool:
    for key in keys:
        value = row.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            norm = value.strip().lower()
            if norm in {"true", "1", "yes", "y"}:
                return True
            if norm in {"false", "0", "no", "n"}:
                return False
    return default


def _art_auth_state(row: dict[str, Any]) -> str:
    has_fake = _first_bool(row, ["has_fake", "fake_available", "is_fake_available"], False)
    return "has_fake" if has_fake else "genuine_only"


def _art_real_info(row: dict[str, Any]) -> dict[str, Any]:
    info = row.get("real_info")
    return info if isinstance(info, dict) else {}


def _art_fake_info(row: dict[str, Any]) -> dict[str, Any]:
    info = row.get("fake_info")
    return info if isinstance(info, dict) else {}


def _event_origin_key(name_en: str) -> str:
    src = str(name_en or "").strip()
    patterns = [
        r"^(.+?) Nook Shopping event (?:begins|ends)(?: \((?:Northern|Southern) Hemisphere\))?$",
        r"^(.+?) Able Sisters event (?:begins|ends)$",
        r"^(.+?) event (?:begins|ends)$",
        r"^(.+?) preparation days (?:begin|end)$",
        r"^(.+?) \((?:Northern|Southern) Hemisphere\)$",
        r"^(.+?) (?:begins|ends)$",
    ]
    for p in patterns:
        m = re.match(p, src)
        if m:
            return str(m.group(1)).strip()
    return src


def _make_catalog_item(catalog_type: str, row: dict[str, Any]) -> dict[str, Any] | None:
    if catalog_type == "events":
        name_en = str(row.get("event") or "").strip()
    else:
        name_en = str(row.get("name") or "").strip()

    if not name_en:
        return None

    name_maps = load_catalog_name_maps()
    name_ko = name_maps.get(catalog_type, {}).get(normalize_name(name_en), "")

    local_recipe_row: dict[str, Any] | None = None
    if catalog_type == "recipes":
        local_recipe_row = load_local_recipes_by_name().get(normalize_name(name_en))

    category = str(row.get("category") or "").strip()
    if catalog_type == "recipes" and not category and isinstance(local_recipe_row, dict):
        category = str(local_recipe_row.get("category") or "").strip()
    if catalog_type == "furniture":
        category = normalize_furniture_category(category)
    if catalog_type == "recipes":
        category = normalize_recipe_category(category)
    extra_filter = ""
    extra_filter_values: list[str] = []

    if catalog_type == "events":
        category = str(row.get("type") or "").strip()
    if catalog_type == "art":
        category = str(row.get("category") or "Artwork").strip()
    if catalog_type == "clothing":
        extra_filter = "style"
        extra_filter_values = [str(v) for v in (row.get("styles") or []) if str(v).strip()]

    source, source_notes = extract_source_pair(row)
    if catalog_type == "recipes" and not source and isinstance(local_recipe_row, dict):
        source, source_notes = extract_source_pair(local_recipe_row)

    if catalog_type == "reactions":
        trans = row.get("translations") if isinstance(row.get("translations"), dict) else {}
        kr_name = str(trans.get("kRko") or "").strip()
        if not kr_name:
            kr_name = load_local_reaction_translation_map().get(normalize_name(name_en), "")
        if kr_name:
            name_ko = kr_name
        if not category:
            category = "Reactions"
        source_notes_raw = row.get("sourceNotes")
        if isinstance(source_notes_raw, list):
            source_notes_raw = " / ".join(str(x).strip() for x in source_notes_raw if str(x).strip())
        row = {
            **row,
            "source_notes": str(source_notes_raw or "").strip(),
            "version": str(row.get("versionAdded") or "").strip(),
            "event_type": str(row.get("seasonEvent") or "").strip(),
        }

    local_number_value = 0
    if catalog_type == "recipes" and isinstance(local_recipe_row, dict):
        local_number_value = (
            local_recipe_row.get("number")
            or local_recipe_row.get("serial_id")
            or local_recipe_row.get("serialId")
            or local_recipe_row.get("internal_id")
            or local_recipe_row.get("internalId")
            or 0
        )

    number_value = (
        row.get("number")
        or row.get("serial_id")
        or row.get("serialId")
        or row.get("internal_id")
        or row.get("internalId")
        or local_number_value
        or 0
    )

    item = {
        "id": _item_id(catalog_type, row, name_en),
        "name": name_ko or name_en,
        "name_ko": name_ko,
        "name_en": name_en,
        "number": int(number_value or 0),
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
    elif catalog_type == "events":
        origin_key = _event_origin_key(name_en)
        event_country_map = load_event_country_map()
        item["event_country_ko"] = str(event_country_map.get(origin_key, "")).strip()
    elif catalog_type == "reactions":
        item["event_type"] = str(row.get("seasonEvent") or "").strip()
        item["date"] = str(row.get("version") or row.get("versionAdded") or "").strip()
        item["icon_filename"] = str(row.get("iconFilename") or "").strip()
        item["season_event_exclusive"] = bool(row.get("seasonEventExclusive"))
        item["reaction_source"] = translate_source_value_to_ko(row.get("source"))
    elif catalog_type == "art":
        has_fake = _first_bool(row, ["has_fake", "fake_available", "is_fake_available"], False)
        real_info = _art_real_info(row)
        fake_info = _art_fake_info(row)
        item["has_fake"] = has_fake
        item["authenticity"] = _art_auth_state(row)
        item["authenticity_ko"] = "가품 있음" if has_fake else "진품만"
        item["real_image_url"] = _first_non_empty(
            real_info,
            [
                "texture_url",
                "real_image_url",
                "real_art_url",
                "real_url",
                "genuine_image_url",
                "image_url",
                "image",
                "highResTexture",
            ],
        )
        item["fake_image_url"] = _first_non_empty(
            fake_info,
            ["texture_url", "fake_image_url", "fake_art_url", "forgery_image_url", "image_url"],
        )
        item["real_description"] = _first_non_empty(
            real_info,
            [
                "real_description",
                "real_art_description",
                "genuine_description",
                "description_real",
                "description",
            ],
        )
        item["fake_description"] = _first_non_empty(
            fake_info,
            [
                "fake_description",
                "fake_art_description",
                "forgery_description",
                "description_fake",
                "description",
            ],
        )
        # 미술품 목록은 아이콘보다 텍스처가 고화질이라 우선 사용한다.
        item["image_url"] = (
            _first_non_empty(real_info, ["texture_url", "image_url"])
            or _first_non_empty(fake_info, ["texture_url", "image_url"])
            or item["real_image_url"]
            or item["fake_image_url"]
            or item["image_url"]
        )
        # 목록 응답에 이미지가 누락되는 경우 single endpoint로 보완한다.
        if not item["image_url"]:
            try:
                single_row = _fetch_single_catalog_row(catalog_type, name_en)
            except Exception:
                single_row = None
            if isinstance(single_row, dict):
                item["image_url"] = _extract_image_url(single_row)
                if not item["real_image_url"]:
                    item["real_image_url"] = _first_non_empty(
                        single_row,
                        [
                            "real_image_url",
                            "real_art_url",
                            "real_url",
                            "genuine_image_url",
                            "image_url",
                            "image",
                            "texture_url",
                            "highResTexture",
                        ],
                    )
                if not item["fake_image_url"]:
                    item["fake_image_url"] = _first_non_empty(
                        single_row,
                        ["fake_image_url", "fake_art_url", "forgery_image_url", "fake_texture_url"],
                    )

    return item


def _find_catalog_row(catalog_type: str, item_id: str) -> dict[str, Any] | None:
    return _catalog_row_index(catalog_type).get(item_id)


@lru_cache(maxsize=None)
def _catalog_row_index(catalog_type: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    rows = load_local_reactions() if catalog_type == "reactions" else load_nookipedia_catalog(catalog_type)
    for row in rows:
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
    variation_state_map: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    category = str(detail.get("category") or item.get("category") or "")
    # summary 블록에서 art 관련 필드를 공통으로 참조하므로 기본값을 먼저 둔다.
    real_info: dict[str, Any] = {}
    fake_info: dict[str, Any] = {}
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

    if catalog_type == "art":
        real_info = _art_real_info(detail)
        fake_info = _art_fake_info(detail)
        has_fake = _first_bool(detail, ["has_fake", "fake_available", "is_fake_available"], False)
        real_desc = _first_non_empty(
            real_info,
            [
                "real_description",
                "real_art_description",
                "genuine_description",
                "description_real",
                "description",
            ],
        )
        fake_desc = _first_non_empty(
            fake_info,
            [
                "fake_description",
                "fake_art_description",
                "forgery_description",
                "description_fake",
                "description",
            ],
        )
        museum_desc = _first_non_empty(detail, ["museum_desc", "museum_description", "art_name"])
        fields.extend(
            [
                {"label": "진품/가품", "value": "가품 있음" if has_fake else "진품만"},
                {"label": "박물관 설명", "value": museum_desc},
                {"label": "진품 특징", "value": real_desc},
                {"label": "가품 특징", "value": fake_desc},
            ]
        )

    variations = _build_variations(detail)
    if variation_state_map:
        variations = [
            {**v, **variation_state_map.get(v["id"], {"owned": False, "quantity": 0})}
            for v in variations
        ]
    else:
        variations = [{**v, "owned": False, "quantity": 0} for v in variations]

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
            "art_has_fake": _first_bool(
                detail, ["has_fake", "fake_available", "is_fake_available"], False
            ),
            "art_real_image_url": _first_non_empty(
                real_info,
                [
                    "texture_url",
                    "real_image_url",
                    "real_art_url",
                    "real_url",
                    "genuine_image_url",
                    "image_url",
                    "image",
                    "highResTexture",
                ],
            ),
            "art_fake_image_url": _first_non_empty(
                fake_info,
                ["texture_url", "fake_image_url", "fake_art_url", "forgery_image_url", "image_url"],
            ),
        },
        "fields": fields,
        "variations": variations,
        "raw_fields": _raw_top_level_fields(detail),
    }


@lru_cache(maxsize=None)
def load_catalog(catalog_type: str) -> list[dict[str, Any]]:
    if catalog_type not in CATALOG_TYPES:
        raise KeyError(catalog_type)

    rows = load_local_reactions() if catalog_type == "reactions" else load_nookipedia_catalog(catalog_type)
    items: list[dict[str, Any]] = []

    for row in rows:
        if not isinstance(row, dict):
            continue
        item = _make_catalog_item(catalog_type, row)
        if item:
            items.append(item)

    items.sort(key=lambda x: (x["name_ko"] or x["name_en"]).lower())
    return items
