from __future__ import annotations

from typing import Any

FROM_MAP_KO = {
    "nook's cranny": "너굴상점",
    "nook shopping": "너굴 쇼핑",
    "nook stop": "너굴포트",
    "diy recipe": "DIY 레시피 제작",
    "diy recipes": "DIY 레시피 제작",
    "balloon": "풍선 선물",
    "balloon presents": "풍선 선물",
    "saharah": "러그 상인 사하라",
    "redd": "여욱이 상점",
    "redd's raffle": "여욱이 제비뽑기",
    "gulliver": "걸리버 이벤트",
    "gullivarr": "해적 걸리버 이벤트",
    "wisp": "유령 부옥 이벤트",
    "fishing tourney": "낚시대회",
    "bug-off": "곤충채집대회",
    "toy day": "토이데이 이벤트",
    "wedding season": "결혼 시즌 이벤트",
    "festivale": "카니발 이벤트",
    "turkey day": "추수감사절 이벤트",
    "happy home paradise": "해피홈 파라다이스",
    "all villagers": "모든 성격 주민",
    "big sister villagers": "단순활발 주민",
    "cranky villagers": "무뚝뚝 주민",
    "dj kk concert": "K.K. 공연",
    "group stretching": "단체 체조",
    "hip reaction collection": "힙 리액션 컬렉션",
    "jack": "잭",
    "jock villagers": "운동광 주민",
    "lazy villagers": "먹보 주민",
    "new reactions notebook": "새 리액션 노트",
    "normal villagers": "친절함 주민",
    "peppy villagers": "아이돌 주민",
    "smug villagers": "느끼함 주민",
    "snooty villagers": "성숙함 주민",
    "viva festivale reaction set": "비바 카니발 리액션 세트",
}

NOTE_MAP_KO = {
    "available from": "해당 경로에서 획득할 수 있습니다.",
    "customizable": "리폼 가능한 아이템입니다.",
    "not for sale": "상점 구매가 불가능한 아이템입니다.",
    "seasonal item": "시즌 한정 아이템입니다.",
    "event item": "이벤트 한정 아이템입니다.",
    "received after doing your 50th group stretch": "단체 체조를 50회 달성하면 획득합니다.",
    "requires a high level of friendship": "주민과의 친밀도가 높아야 획득할 수 있습니다.",
}


def _translate_from_to_ko(value: str) -> str:
    text = value.strip()
    lowered = text.lower()
    if not text:
        return ""
    for en, ko in FROM_MAP_KO.items():
        if en in lowered:
            return ko
    return text


def translate_source_value_to_ko(value: Any) -> str:
    if isinstance(value, list):
        translated = []
        for x in value:
            s = str(x).strip()
            if not s:
                continue
            translated.append(_translate_from_to_ko(s))
        return ", ".join(dict.fromkeys(translated))
    if value is None:
        return ""
    return _translate_from_to_ko(str(value).strip())


def _translate_note_to_ko(value: str) -> str:
    text = value.strip()
    lowered = text.lower()
    if not text:
        return ""
    for en, ko in NOTE_MAP_KO.items():
        if en in lowered:
            return ko
    return f"상세 조건: {text}"


def _parse_availability(value: Any) -> tuple[list[str], list[str]]:
    froms: list[str] = []
    notes: list[str] = []

    if isinstance(value, dict):
        from_value = value.get("from")
        note_value = value.get("note")
        if isinstance(from_value, list):
            froms.extend([str(v).strip() for v in from_value if str(v).strip()])
        elif from_value is not None:
            s = str(from_value).strip()
            if s:
                froms.append(s)

        if isinstance(note_value, list):
            notes.extend([str(v).strip() for v in note_value if str(v).strip()])
        elif note_value is not None:
            s = str(note_value).strip()
            if s:
                notes.append(s)

    elif isinstance(value, list):
        for x in value:
            f, n = _parse_availability(x)
            froms.extend(f)
            notes.extend(n)
    elif isinstance(value, str):
        s = value.strip()
        if s:
            froms.append(s)

    return froms, notes


def extract_source_pair(row: dict[str, Any]) -> tuple[str, str]:
    row_froms, row_notes = _parse_availability(row.get("availability"))
    source = ", ".join(dict.fromkeys([_translate_from_to_ko(x) for x in row_froms if x]))
    source_notes = " / ".join(
        dict.fromkeys([_translate_note_to_ko(x) for x in row_notes if x])
    )

    if not source:
        source = translate_source_value_to_ko(row.get("source"))
    if not source_notes:
        raw_note = str(
            row.get("source_notes")
            or row.get("source_note")
            or row.get("availability_notes")
            or ""
        ).strip()
        source_notes = _translate_note_to_ko(raw_note) if raw_note else ""

    if source or source_notes:
        return source, source_notes

    variations = row.get("variations")
    if not isinstance(variations, list):
        return "", ""

    sources: list[str] = []
    notes: list[str] = []
    for variation in variations:
        if not isinstance(variation, dict):
            continue
        v_froms, v_notes = _parse_availability(variation.get("availability"))
        s = ", ".join(dict.fromkeys([_translate_from_to_ko(x) for x in v_froms if x]))
        if not s:
            s = translate_source_value_to_ko(variation.get("source"))
        n = " / ".join(dict.fromkeys([_translate_note_to_ko(x) for x in v_notes if x]))
        if not n:
            raw_note = str(
                variation.get("source_notes")
                or variation.get("source_note")
                or variation.get("availability_notes")
                or ""
            ).strip()
            n = _translate_note_to_ko(raw_note) if raw_note else ""
        if s:
            sources.append(s)
        if n:
            notes.append(n)

    source_joined = ", ".join(dict.fromkeys(sources)) if sources else ""
    notes_joined = " / ".join(dict.fromkeys(notes)) if notes else ""
    return source_joined, notes_joined
