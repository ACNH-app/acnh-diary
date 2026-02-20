from __future__ import annotations

import os
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent

NAME_MAP_PATH = BASE_DIR / "data" / "name_map_ko.json"
VILLAGER_SAYING_MAP_PATH = BASE_DIR / "data" / "villager_saying_map_ko.json"
PERSONALITY_MAP_PATH = BASE_DIR / "data" / "personality_map_ko.json"
SPECIES_MAP_PATH = BASE_DIR / "data" / "species_map_ko.json"

CLOTHING_NAME_MAP_PATH = BASE_DIR / "data" / "clothing_name_map_ko.json"
CLOTHING_CATEGORY_MAP_PATH = BASE_DIR / "data" / "clothing_category_map_ko.json"
CLOTHING_STYLE_MAP_PATH = BASE_DIR / "data" / "clothing_style_map_ko.json"
CLOTHING_LABEL_THEME_MAP_PATH = BASE_DIR / "data" / "clothing_label_theme_map_ko.json"

FURNITURE_NAME_MAP_PATH = BASE_DIR / "data" / "furniture_name_map_ko.json"
ITEMS_NAME_MAP_PATH = BASE_DIR / "data" / "items_name_map_ko.json"
TOOLS_NAME_MAP_PATH = BASE_DIR / "data" / "tools_name_map_ko.json"
INTERIOR_NAME_MAP_PATH = BASE_DIR / "data" / "interior_name_map_ko.json"
GYROID_NAME_MAP_PATH = BASE_DIR / "data" / "gyroid_name_map_ko.json"
FOSSIL_NAME_MAP_PATH = BASE_DIR / "data" / "fossil_name_map_ko.json"
BUG_NAME_MAP_PATH = BASE_DIR / "data" / "bug_name_map_ko.json"
FISH_NAME_MAP_PATH = BASE_DIR / "data" / "fish_name_map_ko.json"
SEA_NAME_MAP_PATH = BASE_DIR / "data" / "sea_name_map_ko.json"
RECIPE_NAME_MAP_PATH = BASE_DIR / "data" / "recipe_name_map_ko.json"
EVENT_NAME_MAP_PATH = BASE_DIR / "data" / "event_name_map_ko.json"
EVENT_COUNTRY_MAP_PATH = BASE_DIR / "data" / "event_country_map_ko.json"
PHOTO_NAME_MAP_PATH = BASE_DIR / "data" / "photo_name_map_ko.json"
ART_NAME_MAP_PATH = BASE_DIR / "data" / "art_name_map_ko.json"
REACTION_NAME_MAP_PATH = BASE_DIR / "data" / "reaction_name_map_ko.json"
MUSIC_NAME_MAP_PATH = BASE_DIR / "data" / "music_name_map_ko.json"

DB_PATH = BASE_DIR / "app.db"
NOOKIPEDIA_BASE_URL = "https://api.nookipedia.com"

_DOTENV_CACHE: dict[str, str] | None = None


def _load_dotenv() -> dict[str, str]:
    global _DOTENV_CACHE
    if _DOTENV_CACHE is not None:
        return _DOTENV_CACHE

    result: dict[str, str] = {}
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        _DOTENV_CACHE = result
        return result

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value

    _DOTENV_CACHE = result
    return result


def _env(key: str, default: str = "") -> str:
    val = os.environ.get(key, "").strip()
    if val:
        return val
    return str(_load_dotenv().get(key, default)).strip()


def get_api_key() -> str:
    return _env("NOOKIPEDIA_API_KEY", "")


def get_db_path() -> Path:
    raw = _env("DB_PATH", str(DB_PATH))
    return Path(raw).expanduser()


def get_cors_origins() -> list[str]:
    raw = _env("CORS_ORIGINS", "*")
    if not raw:
        return ["*"]
    return [x.strip() for x in raw.split(",") if x.strip()]


def get_app_timezone() -> str:
    return _env("APP_TIMEZONE", "Asia/Seoul")


DEFAULT_PERSONALITY_MAP = {
    "Cranky": "무뚝뚝",
    "Jock": "운동광",
    "Lazy": "먹보",
    "Normal": "친절함",
    "Peppy": "아이돌",
    "Smug": "느끼함",
    "Snooty": "성숙함",
    "Big sister": "단순활발",
    "Sisterly": "단순활발",
    "Uchi": "단순활발",
}

DEFAULT_SPECIES_MAP = {
    "Alligator": "악어",
    "Anteater": "개미핥기",
    "Bear": "곰",
    "Bear cub": "아기곰",
    "Bird": "새",
    "Bull": "황소",
    "Cat": "고양이",
    "Chicken": "닭",
    "Cow": "소",
    "Cub": "아기곰",
    "Deer": "사슴",
    "Dog": "개",
    "Duck": "오리",
    "Eagle": "독수리",
    "Elephant": "코끼리",
    "Frog": "개구리",
    "Goat": "염소",
    "Gorilla": "고릴라",
    "Hamster": "햄스터",
    "Hippo": "하마",
    "Horse": "말",
    "Kangaroo": "캥거루",
    "Koala": "코알라",
    "Lion": "사자",
    "Monkey": "원숭이",
    "Mouse": "쥐",
    "Octopus": "문어",
    "Ostrich": "타조",
    "Penguin": "펭귄",
    "Pig": "돼지",
    "Rabbit": "토끼",
    "Rhinoceros": "코뿔소",
    "Rhino": "코뿔소",
    "Sheep": "양",
    "Squirrel": "다람쥐",
    "Tiger": "호랑이",
    "Wolf": "늑대",
}

DEFAULT_CLOTHING_CATEGORY_MAP = {
    "Accessories": "액세서리",
    "Bags": "가방",
    "Bottoms": "하의",
    "Dress-Up": "원피스/코스튬",
    "Headwear": "모자",
    "Other": "기타",
    "Shoes": "신발",
    "Socks": "양말",
    "Tops": "상의",
    "Umbrellas": "우산",
}

DEFAULT_CLOTHING_STYLE_MAP = {
    "Active": "활동적",
    "Cool": "쿨",
    "Cute": "큐트",
    "Elegant": "엘레강트",
    "Gorgeous": "고저스",
    "Simple": "심플",
}

DEFAULT_CLOTHING_LABEL_THEME_MAP = {
    "Comfy": "편안한",
    "Everyday": "일상",
    "Fairy tale": "동화",
    "Formal": "포멀",
    "Goth": "고스",
    "Outdoorsy": "아웃도어",
    "Party": "파티",
    "Sporty": "스포티",
    "Theatrical": "연극",
    "Vacation": "휴양",
    "Work": "워크",
}

CATALOG_TYPES: dict[str, dict[str, Any]] = {
    "clothing": {
        "label": "옷",
        "nook_path": "/nh/clothing",
        "name_map_path": CLOTHING_NAME_MAP_PATH,
        "status_label": "보유",
    },
    "furniture": {
        "label": "가구",
        "nook_path": "/nh/furniture",
        "name_map_path": FURNITURE_NAME_MAP_PATH,
        "status_label": "보유",
    },
    "items": {
        "label": "잡화",
        "nook_path": "/nh/items",
        "name_map_path": ITEMS_NAME_MAP_PATH,
        "status_label": "보유",
    },
    "tools": {
        "label": "도구",
        "nook_path": "/nh/tools",
        "name_map_path": TOOLS_NAME_MAP_PATH,
        "status_label": "보유",
    },
    "interior": {
        "label": "인테리어",
        "nook_path": "/nh/interior",
        "name_map_path": INTERIOR_NAME_MAP_PATH,
        "status_label": "보유",
    },
    "gyroids": {
        "label": "토용",
        "nook_path": "/nh/gyroids",
        "name_map_path": GYROID_NAME_MAP_PATH,
        "status_label": "보유",
    },
    "fossils": {
        "label": "화석",
        "nook_path": "/nh/fossils/individuals",
        "name_map_path": FOSSIL_NAME_MAP_PATH,
        "status_label": "보유",
    },
    "bugs": {
        "label": "곤충",
        "nook_path": "/nh/bugs",
        "name_map_path": BUG_NAME_MAP_PATH,
        "status_label": "보유",
    },
    "fish": {
        "label": "물고기",
        "nook_path": "/nh/fish",
        "name_map_path": FISH_NAME_MAP_PATH,
        "status_label": "보유",
    },
    "sea": {
        "label": "해산물",
        "nook_path": "/nh/sea",
        "name_map_path": SEA_NAME_MAP_PATH,
        "status_label": "보유",
    },
    "recipes": {
        "label": "레시피",
        "nook_path": "/nh/recipes",
        "name_map_path": RECIPE_NAME_MAP_PATH,
        "status_label": "보유",
    },
    "events": {
        "label": "이벤트",
        "nook_path": "/nh/events",
        "name_map_path": EVENT_NAME_MAP_PATH,
        "status_label": "완료",
    },
    "photos": {
        "label": "사진",
        "nook_path": "/nh/photos",
        "name_map_path": PHOTO_NAME_MAP_PATH,
        "status_label": "보유",
    },
    "art": {
        "label": "미술품",
        "nook_path": "/nh/art",
        "name_map_path": ART_NAME_MAP_PATH,
        "status_label": "기증",
    },
    "reactions": {
        "label": "리액션",
        "nook_path": "",
        "name_map_path": REACTION_NAME_MAP_PATH,
        "status_label": "습득",
    },
    "music": {
        "label": "음악",
        "nook_path": "",
        "name_map_path": MUSIC_NAME_MAP_PATH,
        "status_label": "보유",
    },
}

CATALOG_SINGLE_PATHS: dict[str, str] = {
    "clothing": "/nh/clothing/{name}",
    "furniture": "/nh/furniture/{name}",
    "items": "/nh/items/{name}",
    "tools": "/nh/tools/{name}",
    "interior": "/nh/interior/{name}",
    "gyroids": "/nh/gyroids/{name}",
    "fossils": "/nh/fossils/all/{name}",
    "bugs": "/nh/bugs/{name}",
    "fish": "/nh/fish/{name}",
    "sea": "/nh/sea/{name}",
    "recipes": "/nh/recipes/{name}",
    "events": "/nh/events/{name}",
    "photos": "/nh/photos/{name}",
    "art": "/nh/art/{name}",
}
