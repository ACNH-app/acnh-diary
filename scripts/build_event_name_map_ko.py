from __future__ import annotations

import json
import re
from pathlib import Path

from app.services.catalog_data import load_catalog, load_villagers


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "event_name_map_ko.json"


TERM_MAP = {
    "acorn and pine cone": "도토리/솔방울",
    "cherry blossom": "벚꽃",
    "maple leaf": "단풍잎",
    "mushroom": "버섯",
    "ornament": "오너먼트",
    "snowflake": "눈꽃",
    "summer shell": "여름 조개",
    "young spring bamboo": "봄 대나무",
    "fall": "가을",
    "spring": "봄",
    "summer": "여름",
    "winter": "겨울",
    "festive": "연말",
}

TITLE_MAP = {
    "April Fools' Day": "만우절",
    "Big Game Celebration": "빅 게임 기념",
    "Carnival of Venice": "베네치아 카니발",
    "Cheese Rolling": "치즈 굴리기",
    "Children's Day": "어린이날",
    "Chuseok": "추석",
    "Cowboy Festival": "카우보이 축제",
    "Cowherd & Weaver Girl Day": "칠석",
    "Dano Festival": "단오",
    "Day of the Dead": "죽은 자의 날",
    "Dragon Boat Festival": "용선절",
    "Father's Day": "아버지의 날",
    "Grape Harvest Festival": "포도 수확 축제",
    "Groundhog Day": "그라운드호그 데이",
    "Hinamatsuri": "히나마츠리",
    "International Children's Day": "국제 어린이날",
    "Lantern Festival": "원소절",
    "Le 14 juillet": "바스티유 데이",
    "Lunar New Year": "음력 설",
    "Marine Day": "바다의 날",
    "Moon-Viewing Day": "달맞이날",
    "Mother's Day": "어머니의 날",
    "Nanakusa Gayu": "나나쿠사가유",
    "Nature Day": "네이처 데이",
    "New Year's Day": "새해",
    "New Year's Eve": "새해 전야",
    "Nochevieja": "노체비에하",
    "Nook Friday": "너굴 프라이데이",
    "Obon": "오봉",
    "Prom": "프롬",
    "Seollal": "설날",
    "Setsubun": "세츠분",
    "Shamrock Day": "성 패트릭의 날",
    "Shichi-Go-San": "시치고산",
    "Shōgatsu": "쇼가쓰",
    "Silvester": "실베스터",
    "Singmogil": "식목일",
    "Summer Solstice": "하지",
    "Tanabata": "칠석",
    "Tomato Festival": "토마토 축제",
    "Valentine's Day": "발렌타인데이",
    "Wedding Season": "웨딩 시즌",
    "Winter Solstice": "동지",
    "Ōmisoka": "오미소카",
    "π Day": "파이의 날",
    "Bug-Off": "곤충채집대회",
    "Bunny Day": "이스터",
    "Festivale": "카니발",
    "Fireworks Show": "불꽃놀이",
    "Fishing Tourney": "낚시대회",
    "Countdown": "카운트다운",
    "Halloween": "핼러윈",
    "Toy Day": "토이 데이",
    "Turkey Day": "칠면조 데이",
}


def _hemi_ko(text: str) -> str:
    if "Northern Hemisphere" in text:
        return "북반구"
    if "Southern Hemisphere" in text:
        return "남반구"
    return ""


def _ko_term(term: str) -> str:
    t = term.strip()
    return TERM_MAP.get(t.lower(), t)


def translate_event(name_en: str, villager_map: dict[str, str]) -> str:
    src = str(name_en or "").strip()
    if not src:
        return ""

    m = re.match(r"^(.*)'s birthday$", src)
    if m:
        en = m.group(1).strip()
        return f"{villager_map.get(en, en)} 생일"

    m = re.match(r"^(.+?) recipes become available \((Northern Hemisphere|Southern Hemisphere)\)$", src)
    if m:
        term = _ko_term(m.group(1).strip())
        hemi = _hemi_ko(m.group(2))
        return f"{term} 레시피 시작 ({hemi})"

    m = re.match(r"^Last day (.+?) recipes are available(?: \((Northern Hemisphere|Southern Hemisphere)\))?$", src)
    if m:
        term = _ko_term(m.group(1).strip())
        hemi = _hemi_ko(m.group(2) or "")
        return f"{term} 레시피 종료 ({hemi})" if hemi else f"{term} 레시피 종료"

    m = re.match(r"^First day of (fall|spring|summer|winter) \((Northern Hemisphere|Southern Hemisphere)\)$", src)
    if m:
        season_ko = _ko_term(m.group(1))
        hemi_ko = _hemi_ko(m.group(2))
        return f"{season_ko} 시작 ({hemi_ko})"

    m = re.match(r"^Last day of (fall|spring|summer|winter) \((Northern Hemisphere|Southern Hemisphere)\)$", src)
    if m:
        season_ko = _ko_term(m.group(1))
        hemi_ko = _hemi_ko(m.group(2))
        return f"{season_ko} 종료 ({hemi_ko})"

    m = re.match(
        r"^First day of the (fall|spring|summer|winter|festive) shopping season(?: \((Northern Hemisphere|Southern Hemisphere)\))?$",
        src,
    )
    if m:
        hemi = _hemi_ko(m.group(2) or "")
        season_ko = _ko_term(m.group(1))
        base = f"{season_ko} 쇼핑 시즌 시작"
        return f"{base} ({hemi})" if hemi else base

    m = re.match(
        r"^Last day of the (fall|spring|summer|winter|festive) shopping season(?: \((Northern Hemisphere|Southern Hemisphere)\))?$",
        src,
    )
    if m:
        hemi = _hemi_ko(m.group(2) or "")
        season_ko = _ko_term(m.group(1))
        base = f"{season_ko} 쇼핑 시즌 종료"
        return f"{base} ({hemi})" if hemi else base

    m = re.match(r"^(.+?) Nook Shopping event (begins|ends)(?: \((Northern Hemisphere|Southern Hemisphere)\))?$", src)
    if m:
        title = TITLE_MAP.get(m.group(1).strip(), m.group(1).strip())
        action = "시작" if m.group(2) == "begins" else "종료"
        hemi = _hemi_ko(m.group(3) or "")
        base = f"너굴 쇼핑 {title} {action}"
        return f"{base} ({hemi})" if hemi else base

    m = re.match(r"^(.+?) Able Sisters event (begins|ends)$", src)
    if m:
        title = TITLE_MAP.get(m.group(1).strip(), m.group(1).strip())
        action = "시작" if m.group(2) == "begins" else "종료"
        return f"에이블 시스터즈 {title} {action}"

    m = re.match(r"^(.+?) event (begins|ends)$", src)
    if m:
        title = TITLE_MAP.get(m.group(1).strip(), m.group(1).strip())
        action = "시작" if m.group(2) == "begins" else "종료"
        return f"{title} 이벤트 {action}"

    m = re.match(r"^(.+?) preparation days (begin|end)$", src)
    if m:
        title = TITLE_MAP.get(m.group(1).strip(), m.group(1).strip())
        action = "시작" if m.group(2) == "begin" else "종료"
        return f"{title} 준비 기간 {action}"

    m = re.match(r"^(.+?) begins$", src)
    if m:
        title = TITLE_MAP.get(m.group(1).strip(), m.group(1).strip())
        return f"{title} 시작"

    m = re.match(r"^(.+?) ends$", src)
    if m:
        title = TITLE_MAP.get(m.group(1).strip(), m.group(1).strip())
        return f"{title} 종료"

    m = re.match(r"^(.+?) recipes become available$", src)
    if m:
        term = _ko_term(m.group(1).strip())
        return f"{term} 레시피 시작"

    m = re.match(r"^Bug-Off \((Northern Hemisphere|Southern Hemisphere)\)$", src)
    if m:
        return f"곤충채집대회 ({_hemi_ko(m.group(1))})"

    m = re.match(r"^Heavy snowstorm \((Northern Hemisphere|Southern Hemisphere)\)$", src)
    if m:
        return f"폭설 ({_hemi_ko(m.group(1))})"

    m = re.match(r"^(Summer|Winter) Solstice Nook Shopping event (begins|ends) \((Northern Hemisphere|Southern Hemisphere)\)$", src)
    if m:
        title = "하지" if m.group(1) == "Summer" else "동지"
        action = "시작" if m.group(2) == "begins" else "종료"
        return f"너굴 쇼핑 {title} {action} ({_hemi_ko(m.group(3))})"

    if src in TITLE_MAP:
        return TITLE_MAP[src]

    return src


def main() -> None:
    villagers = load_villagers()
    villager_map = {str(v.get("name_en") or "").strip(): str(v.get("name_ko") or "").strip() for v in villagers}

    rows = load_catalog("events")
    names = sorted({str(r.get("name_en") or "").strip() for r in rows if str(r.get("name_en") or "").strip()})
    mapped = {name: translate_event(name, villager_map) for name in names}
    OUT_PATH.write_text(json.dumps(mapped, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    unchanged = [k for k, v in mapped.items() if k == v]
    print(f"written: {OUT_PATH}")
    print(f"total: {len(mapped)}")
    print(f"unchanged: {len(unchanged)}")
    for x in unchanged[:80]:
        print(" -", x)


if __name__ == "__main__":
    main()
