from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.core.config import get_app_timezone

MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

SEASON_KO = {
    "spring": "봄",
    "summer": "여름",
    "autumn": "가을",
    "winter": "겨울",
}


def parse_effective_now(profile: dict[str, Any]) -> datetime:
    tz = ZoneInfo(get_app_timezone())
    if bool(profile.get("time_travel_enabled")):
        raw = str(profile.get("game_datetime") or "").strip()
        if raw:
            try:
                dt = datetime.fromisoformat(raw)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=tz)
                return dt.astimezone(tz)
            except ValueError:
                pass
    return datetime.now(tz)


def season_for_month(month: int, hemisphere: str) -> str:
    north = {
        3: "spring",
        4: "spring",
        5: "spring",
        6: "summer",
        7: "summer",
        8: "summer",
        9: "autumn",
        10: "autumn",
        11: "autumn",
        12: "winter",
        1: "winter",
        2: "winter",
    }
    south = {
        3: "autumn",
        4: "autumn",
        5: "autumn",
        6: "winter",
        7: "winter",
        8: "winter",
        9: "spring",
        10: "spring",
        11: "spring",
        12: "summer",
        1: "summer",
        2: "summer",
    }
    season = (south if hemisphere == "south" else north).get(month, "spring")
    return SEASON_KO.get(season, "봄")


def zodiac_for_month_day(month: int, day: int) -> str:
    zodiacs = [
        ((1, 20), "물병자리"),
        ((2, 19), "물고기자리"),
        ((3, 21), "양자리"),
        ((4, 20), "황소자리"),
        ((5, 21), "쌍둥이자리"),
        ((6, 22), "게자리"),
        ((7, 23), "사자자리"),
        ((8, 23), "처녀자리"),
        ((9, 24), "천칭자리"),
        ((10, 24), "전갈자리"),
        ((11, 23), "사수자리"),
        ((12, 22), "염소자리"),
    ]
    prev = "염소자리"
    for (m, d), name in zodiacs:
        if (month, day) < (m, d):
            return prev
        prev = name
    return "염소자리"


def _parse_event_date(text: str) -> tuple[int, int] | None:
    src = str(text or "").strip()
    if not src:
        return None
    try:
        if re.match(r"^\d{4}-\d{2}-\d{2}$", src):
            d = datetime.strptime(src, "%Y-%m-%d")
            return d.month, d.day
    except ValueError:
        pass
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})", src, flags=re.IGNORECASE)
    if not m:
        return None
    month = MONTH_MAP.get(m.group(1).lower())
    day = int(m.group(2))
    if not month or day < 1 or day > 31:
        return None
    return month, day


def _event_next_delta_days(today_month: int, today_day: int, event_month: int, event_day: int) -> int:
    start = today_month * 32 + today_day
    target = event_month * 32 + event_day
    if target >= start:
        return target - start
    return (13 * 32 - start) + target


def upcoming_events(
    events: list[dict[str, Any]],
    now: datetime,
    hemisphere: str,
    max_count: int = 5,
) -> list[dict[str, Any]]:
    today_month = now.month
    today_day = now.day
    rows: list[dict[str, Any]] = []
    for row in events:
        name_en = str(row.get("name_en") or row.get("name") or "")
        lowered = name_en.lower()
        if "birthday" in lowered:
            continue
        if "northern hemisphere" in lowered and hemisphere == "south":
            continue
        if "southern hemisphere" in lowered and hemisphere != "south":
            continue
        dt = _parse_event_date(str(row.get("date") or ""))
        if not dt:
            continue
        month, day = dt
        rows.append(
            {
                "id": str(row.get("id") or ""),
                "name_ko": str(row.get("name_ko") or ""),
                "name_en": name_en,
                "date": str(row.get("date") or ""),
                "delta_days": _event_next_delta_days(today_month, today_day, month, day),
            }
        )
    rows.sort(key=lambda x: (int(x["delta_days"]), x["name_ko"] or x["name_en"]))
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        key = (row.get("name_ko") or row.get("name_en") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(row)
        if len(deduped) >= max_count:
            break
    return deduped


def today_nook_shopping(events: list[dict[str, Any]], now: datetime, hemisphere: str) -> list[dict[str, Any]]:
    rows = upcoming_events(events, now, hemisphere, max_count=200)
    result: list[dict[str, Any]] = []
    for row in rows:
        name_en = str(row.get("name_en") or "")
        if int(row.get("delta_days") or 9999) != 0:
            continue
        if "nook shopping" not in name_en.lower():
            continue
        result.append(row)
    return result[:6]


def seasonal_recipes_now(events: list[dict[str, Any]], now: datetime, hemisphere: str) -> list[dict[str, Any]]:
    rows = upcoming_events(events, now, hemisphere, max_count=250)
    result: list[dict[str, Any]] = []
    for row in rows:
        name_en = str(row.get("name_en") or "")
        lowered = name_en.lower()
        if "recipe" not in lowered and "diy" not in lowered:
            continue
        if int(row.get("delta_days") or 9999) > 30:
            continue
        result.append(row)
    return result[:8]


def blooming_shrubs_now(month: int, hemisphere: str) -> list[str]:
    north = {
        "동백나무": {1, 2, 3, 12},
        "철쭉": {4, 5},
        "수국": {6, 7},
        "무궁화": {7, 8, 9},
        "플루메리아": {6, 7, 8, 9},
        "올리브": {9, 10},
    }
    south = {
        "동백나무": {6, 7, 8, 9},
        "철쭉": {10, 11},
        "수국": {12, 1},
        "무궁화": {1, 2, 3},
        "플루메리아": {12, 1, 2, 3},
        "올리브": {3, 4},
    }
    src = south if hemisphere == "south" else north
    return [name for name, months in src.items() if month in months]


def catalog_progress_summary(
    load_catalog: Any,
    get_catalog_state_map: Any,
    get_catalog_variation_owned_counts: Any,
) -> list[dict[str, Any]]:
    catalog_types = [
        ("fossils", "화석"),
        ("gyroids", "토용"),
        ("furniture", "가구"),
        ("interior", "인테리어"),
        ("clothing", "옷"),
        ("items", "잡화"),
        ("tools", "도구"),
        ("photos", "사진"),
    ]
    rows: list[dict[str, Any]] = []
    for key, label in catalog_types:
        items = load_catalog(key)
        total = len(items)
        state_map = get_catalog_state_map(key)
        owned = sum(1 for v in state_map.values() if bool(v.get("owned")))
        variation_owned_count_map = get_catalog_variation_owned_counts(key)
        partial = 0
        for item in items:
            total_vari = int(item.get("variation_total") or 0)
            if total_vari <= 0:
                continue
            owned_vari = int(variation_owned_count_map.get(item["id"], 0))
            if 0 < owned_vari < total_vari:
                partial += 1
        rate = round((owned / total * 100.0), 1) if total else 0.0
        rows.append(
            {
                "catalog_type": key,
                "label": label,
                "owned": owned,
                "total": total,
                "partial": partial,
                "completion_rate": rate,
            }
        )
    return rows


def build_home_summary(profile: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    now = parse_effective_now(profile)
    hemisphere = str(profile.get("hemisphere") or "north")
    shopping_today = today_nook_shopping(events, now, hemisphere)
    recipes_now = seasonal_recipes_now(events, now, hemisphere)
    shrubs_now = blooming_shrubs_now(now.month, hemisphere)
    return {
        "effective_datetime": now.strftime("%Y-%m-%dT%H:%M"),
        "season_ko": season_for_month(now.month, hemisphere),
        "zodiac_ko": zodiac_for_month_day(now.month, now.day),
        "upcoming_events": upcoming_events(events, now, hemisphere, max_count=6),
        "nook_shopping_today": shopping_today,
        "seasonal_recipes_now": recipes_now,
        "blooming_shrubs_now": shrubs_now,
    }
