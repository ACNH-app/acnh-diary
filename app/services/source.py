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
}

NOTE_MAP_KO = {
    "available from": "해당 경로에서 획득할 수 있습니다.",
    "customizable": "리폼 가능한 아이템입니다.",
    "not for sale": "상점 구매가 불가능한 아이템입니다.",
    "seasonal item": "시즌 한정 아이템입니다.",
    "event item": "이벤트 한정 아이템입니다.",
}


def _stringify_source(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(x).strip() for x in value if str(x).strip())
    if isinstance(value, str):
        return value.strip()
    return str(value).strip() if value is not None else ""


def _translate_from_to_ko(value: str) -> str:
    text = value.strip()
    lowered = text.lower()
    if not text:
        return ""
    for en, ko in FROM_MAP_KO.items():
        if en in lowered:
            return ko
    return text


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
        source = _translate_from_to_ko(_stringify_source(row.get("source")))
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
            s = _translate_from_to_ko(_stringify_source(variation.get("source")))
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
