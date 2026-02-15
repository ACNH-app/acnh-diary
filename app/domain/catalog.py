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


def order_categories(catalog_type: str, categories: list[str]) -> list[str]:
    if catalog_type == "furniture":
        preferred = FURNITURE_CATEGORY_ORDER
    elif catalog_type == "clothing":
        preferred = CLOTHING_CATEGORY_ORDER
    else:
        return sorted(categories)

    rank = {name: i for i, name in enumerate(preferred)}
    return sorted(categories, key=lambda c: (rank.get(c, len(preferred)), c.casefold()))
