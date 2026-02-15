from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

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


def _parse_month_key(month: str) -> tuple[int, int] | None:
    m = re.match(r"^(\d{4})-(\d{2})$", str(month or "").strip())
    if not m:
        return None
    year = int(m.group(1))
    mon = int(m.group(2))
    if mon < 1 or mon > 12:
        return None
    return year, mon


def _parse_ymd(text: str) -> tuple[int, int, int] | None:
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", str(text or "").strip())
    if not m:
        return None
    y = int(m.group(1))
    mo = int(m.group(2))
    d = int(m.group(3))
    if mo < 1 or mo > 12 or d < 1 or d > 31:
        return None
    return y, mo, d


def _parse_month_day_text(text: str) -> tuple[int, int] | None:
    m = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})",
        str(text or "").strip(),
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    month = MONTH_MAP.get(m.group(1).lower())
    day = int(m.group(2))
    if not month or day < 1 or day > 31:
        return None
    return month, day


def _easter_sunday(year: int) -> date:
    # Gregorian computus
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _normalize_movable_event_date(name_en: str, year: int) -> tuple[int, int, int] | None:
    easter = _easter_sunday(year)
    mapping: dict[str, date] = {
        "Festivale": easter - timedelta(days=48),
        "Festivale preparation days begin": easter - timedelta(days=55),
        "Festivale preparation days end": easter - timedelta(days=49),
        "Bunny Day": easter,
        "Bunny Day preparation days begin": easter - timedelta(days=7),
        "Bunny Day preparation days end": easter - timedelta(days=1),
    }
    d = mapping.get(name_en)
    if not d:
        return None
    return d.year, d.month, d.day


def build_calendar_annotations(
    *,
    month: str,
    hemisphere: str,
    villagers: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    month_key = _parse_month_key(month)
    if not month_key:
        return []
    year, target_month = month_key
    hemi = "south" if hemisphere == "south" else "north"

    rows: list[dict[str, Any]] = []

    for villager in villagers:
        md = _parse_month_day_text(str(villager.get("birthday") or ""))
        if not md:
            continue
        mon, day = md
        if mon != target_month:
            continue
        name = str(villager.get("name_ko") or villager.get("name_en") or "").strip()
        if not name:
            continue
        rows.append(
            {
                "date": f"{year}-{target_month:02d}-{day:02d}",
                "type": "birthday",
                "label": f"{name} 생일",
                "name": name,
            }
        )

    seen_events: set[tuple[str, str]] = set()
    for event in events:
        if str(event.get("event_type") or "") != "Event":
            continue
        name_en = str(event.get("name_en") or event.get("name") or "").strip()
        dt = _parse_ymd(str(event.get("date") or ""))
        if not dt:
            continue
        y, mon, day = dt
        normalized = _normalize_movable_event_date(name_en, y)
        if normalized:
            y, mon, day = normalized
        if y != year or mon != target_month:
            continue

        lowered = name_en.lower()
        if "birthday" in lowered:
            continue
        if "northern hemisphere" in lowered and hemi == "south":
            continue
        if "southern hemisphere" in lowered and hemi != "south":
            continue

        label = str(event.get("name_ko") or name_en).strip()
        if not label:
            continue
        key = (f"{year}-{mon:02d}-{day:02d}", label.lower())
        if key in seen_events:
            continue
        seen_events.add(key)
        rows.append(
            {
                "date": f"{year}-{mon:02d}-{day:02d}",
                "type": "event",
                "label": label,
                "name": label,
            }
        )

    rows.sort(key=lambda x: (str(x.get("date") or ""), str(x.get("type") or ""), str(x.get("label") or "")))
    return rows
