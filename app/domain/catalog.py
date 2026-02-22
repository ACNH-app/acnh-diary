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

RECIPE_SEASON_FACET_KO_MAP = {
    "season:young_spring_bamboo": "봄: 봄의 대나무 12종",
    "season:cherry_blossom": "봄: 벚꽃 15종",
    "season:summer_shell": "여름: 여름 조개껍데기 9종",
    "season:mushroom": "가을: 버섯 12종",
    "season:maple_leaf": "가을: 단풍잎 10종",
    "season:tree_bounty": "가을: 도토리/솔방울 12종",
    "season:winter_snowflake": "겨울: 눈의 결정 26종",
    "season:christmas_ornament": "겨울: 크리스마스 오너먼트 20종",
}

RECIPE_EVENT_FACET_KO_MAP = {
    "event:bunny_day": "이벤트: 이스터 40종",
    "event:festivale": "이벤트: 카니발",
    "event:wedding_season": "이벤트: 웨딩 시즌",
    "event:halloween": "이벤트: 할로윈 18종",
    "event:turkey_day": "이벤트: 추수감사절 12종",
}

RECIPE_NPC_FACET_KO_MAP = {
    "npc:celeste": "부옥 레시피 49종",
    "npc:pascal": "머메이드 레시피 15종",
}

RECIPE_INGREDIENT_FACET_KO_MAP = {
    "ingredient:fruit": "재료: 과일",
    "ingredient:flower": "재료: 꽃",
    "ingredient:shell_non_mermaid": "재료: 조개(머메이드 제외)",
    "ingredient:vine_moss": "재료: 덩굴/빛이끼",
}

RECIPE_FACET_ORDER = [
    "season:young_spring_bamboo",
    "season:cherry_blossom",
    "season:summer_shell",
    "season:mushroom",
    "season:maple_leaf",
    "season:tree_bounty",
    "season:winter_snowflake",
    "season:christmas_ornament",
    "event:bunny_day",
    "event:festivale",
    "event:wedding_season",
    "event:halloween",
    "event:turkey_day",
    "npc:celeste",
    "npc:pascal",
    "ingredient:fruit",
    "ingredient:flower",
    "ingredient:shell_non_mermaid",
    "ingredient:vine_moss",
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
        if category in RECIPE_SEASON_FACET_KO_MAP:
            return RECIPE_SEASON_FACET_KO_MAP[category]
        if category in RECIPE_EVENT_FACET_KO_MAP:
            return RECIPE_EVENT_FACET_KO_MAP[category]
        if category in RECIPE_NPC_FACET_KO_MAP:
            return RECIPE_NPC_FACET_KO_MAP[category]
        if category in RECIPE_INGREDIENT_FACET_KO_MAP:
            return RECIPE_INGREDIENT_FACET_KO_MAP[category]
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
        preferred = [*RECIPE_CATEGORY_ORDER, *RECIPE_FACET_ORDER]
    elif catalog_type == "special_items":
        preferred = SPECIAL_SOURCE_ORDER
    else:
        return sorted(categories)

    rank = {name: i for i, name in enumerate(preferred)}
    return sorted(categories, key=lambda c: (rank.get(c, len(preferred)), c.casefold()))
