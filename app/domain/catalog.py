from __future__ import annotations

from app.core.config import DEFAULT_CLOTHING_CATEGORY_MAP

FURNITURE_CATEGORY_KO_MAP = {
    "Housewares": "가구",
    "Miscellaneous": "잡화",
    "Wall-mounted": "벽걸이",
    "Ceiling decor": "천장",
}

FURNITURE_CATEGORY_ORDER = [
    "Housewares",
    "Miscellaneous",
    "Wall-mounted",
    "Ceiling decor",
]

RECIPE_CATEGORY_KO_MAP = {
    "Tools": "도구",
    "Housewares": "가구",
    "Miscellaneous": "잡화",
    "Wall-mounted": "벽걸이",
    "Ceiling Decor": "천장",
    "Ceiling decor": "천장",
    "Interior": "벽지/바닥/러그",
    "Equipment": "의류",
    "Other": "기타",
    "Savory": "푸드",
    "Sweet": "디저트",
}

RECIPE_CATEGORY_ORDER = [
    "Tools",
    "Housewares",
    "Miscellaneous",
    "Wall-mounted",
    "Ceiling Decor",
    "Interior",
    "Equipment",
    "Other",
    "Savory",
    "Sweet",
]

SPECIAL_SOURCE_KO_MAP = {
    "gulliver": "죠니",
    "gullivarr": "해적 죠니",
    "flick_bug_off": "레온(곤충대회)",
    "flick": "레온",
    "cj_fishing_tourney": "저스틴(낚시대회)",
    "cj": "저스틴",
    "recycle_box": "재활용함",
    "mom": "엄마",
    "birthday": "생일",
    "jingle": "루돌",
    "festivale": "카니발",
    "wedding_season": "웨딩 시즌",
    "pascal": "해탈한",
    "halloween": "할로윈",
    "turkey_day": "추수감사절",
    "fireworks": "불꽃놀이",
    "other": "기타",
}

SPECIAL_SOURCE_ORDER = [
    "gulliver",
    "gullivarr",
    "flick_bug_off",
    "flick",
    "cj_fishing_tourney",
    "cj",
    "recycle_box",
    "mom",
    "birthday",
    "jingle",
    "festivale",
    "wedding_season",
    "pascal",
    "halloween",
    "turkey_day",
    "fireworks",
    "other",
]

CLOTHING_CATEGORY_ORDER = [
    "Tops",
    "Bottoms",
    "Dress-Up",
    "Headwear",
    "Accessories",
    "Socks",
    "Shoes",
    "Bags",
    "Umbrellas",
]


def category_ko_for(catalog_type: str, category: str) -> str:
    if catalog_type == "clothing":
        return DEFAULT_CLOTHING_CATEGORY_MAP.get(category, category)
    if catalog_type == "furniture":
        return FURNITURE_CATEGORY_KO_MAP.get(category, category)
    if catalog_type == "recipes":
        return RECIPE_CATEGORY_KO_MAP.get(category, category)
    if catalog_type == "special_items":
        return SPECIAL_SOURCE_KO_MAP.get(category, category)
    return category


def normalize_furniture_category(category: str) -> str:
    raw = (category or "").strip()
    key = raw.lower().replace("_", " ").replace("-", " ")
    key = " ".join(key.split())

    if key in {"housewares", "houseware"}:
        return "Housewares"
    if key in {"miscellaneous", "misc"}:
        return "Miscellaneous"
    if key in {"wall mounted", "wallmounted", "wall mount"}:
        return "Wall-mounted"
    if key in {"ceiling decor", "ceiling decoration", "ceiling"}:
        return "Ceiling decor"
    return raw


def normalize_recipe_category(category: str) -> str:
    raw = (category or "").strip()
    key = raw.lower().replace("_", " ").replace("-", " ")
    key = " ".join(key.split())

    if key in {"ceiling decor", "ceiling decoration", "ceiling"}:
        return "Ceiling Decor"
    if key in {"wallpaper", "walls", "wall"}:
        return "Interior"
    if key in {"floors", "floor", "flooring"}:
        return "Interior"
    if key in {"rugs", "rug"}:
        return "Interior"
    return raw


def order_categories(catalog_type: str, categories: list[str]) -> list[str]:
    if catalog_type == "furniture":
        preferred = FURNITURE_CATEGORY_ORDER
    elif catalog_type == "clothing":
        preferred = CLOTHING_CATEGORY_ORDER
    elif catalog_type == "recipes":
        preferred = RECIPE_CATEGORY_ORDER
    elif catalog_type == "special_items":
        preferred = SPECIAL_SOURCE_ORDER
    else:
        return sorted(categories)

    rank = {name: i for i, name in enumerate(preferred)}
    return sorted(categories, key=lambda c: (rank.get(c, len(preferred)), c.casefold()))
