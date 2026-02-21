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
    "festive wrapping paper": "축제 포장지",
    "golden watering can": "황금 물뿌리개",
    "any villager": "아무 주민",
    "archipelago": "군도",
    "boat tour": "보트 투어",
    "bells": "벨",
    "birthday": "생일",
    "ground": "지면",
    "rock": "바위",
    "tree": "나무",
    "breeding": "교배",
    "catching": "포획",
    "cooking": "요리",
    "crafting": "제작",
    "diving": "잠수",
    "dig spot": "땅파기 지점",
    "fishing": "낚시",
    "friendship": "친밀도",
    "island evaluation": "섬 평가",
    "lost item": "분실물",
    "money tree": "돈나무",
    "quest item": "퀘스트 아이템",
    "recycle box": "재활용함",
    "slumber island": "꿈섬",
    "turnips": "무",
    "unobtainable": "획득 불가",
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

NPC_SOURCE_MAP_KO = {
    "blathers": "부엉",
    "brewster": "마스터",
    "c.j.": "저스틴",
    "celeste": "부옥",
    "cornimer": "콘키",
    "cyrus": "리사이클 상점 리포",
    "daisy mae": "무파니",
    "dodo airlines": "도도항공",
    "flick": "레온",
    "franklin": "칠면조 프랭클린",
    "happy home academy": "해피홈 아카데미",
    "harvey": "파니엘",
    "isabelle": "여울",
    "jingle": "징글",
    "label": "케이트",
    "lloid": "토용이",
    "lottie": "니코",
    "luna": "몽셰르",
    "mabel": "고순",
    "mom": "엄마",
    "niko": "니코",
    "nintendo": "닌텐도",
    "pascal": "해탈한",
    "pavé": "무지개새",
    "reese": "리포",
    "resetti": "리셋씨",
    "rover": "모리",
    "snowboy": "눈사람",
    "timmy": "콩돌",
    "tom nook": "너굴",
    "tommy": "밤돌",
    "wardell": "워델",
    "zipper": "토빗",
}

TOKEN_MAP_KO = {
    "apple": "사과",
    "bamboo": "대나무",
    "beach": "해변",
    "black": "검은",
    "blue": "파란",
    "bokjumeoni": "복주머니",
    "camellia": "동백",
    "carrot": "당근",
    "cedar": "삼나무",
    "cherry": "체리",
    "coconut": "코코넛",
    "communicator": "통신기",
    "communicator part": "통신기 부품",
    "cosmos": "코스모스",
    "envelope": "봉투",
    "festive": "축제",
    "firework": "불꽃",
    "fountain": "분수",
    "gold": "황금",
    "golden": "황금",
    "green": "초록",
    "hibiscus": "무궁화",
    "holly": "호랑가시나무",
    "hydrangea": "수국",
    "hyacinth": "히아신스",
    "jolly": "유쾌한",
    "lily": "백합",
    "lucky": "행운",
    "mum": "국화",
    "orange": "주황",
    "otoshidama": "오토시다마",
    "olive": "올리브",
    "pansy": "팬지",
    "part": "부품",
    "peach": "복숭아",
    "pear": "배",
    "pink": "분홍",
    "plumeria": "플루메리아",
    "potato": "감자",
    "pumpkin": "호박",
    "pouch": "주머니",
    "purple": "보라",
    "red": "빨간",
    "ripe": "익은",
    "rose": "장미",
    "sapling": "묘목",
    "seed": "씨앗",
    "shoot": "죽순",
    "start": "모종",
    "sugarcane": "사탕수수",
    "tea": "차",
    "tomato": "토마토",
    "treasure": "보물",
    "trawler": "트롤러",
    "tulip": "튤립",
    "watering": "물뿌리개",
    "wheat": "밀",
    "white": "하얀",
    "windflower": "아네모네",
    "wrapping": "포장",
    "yellow": "노란",
    "azalea": "철쭉",
}


def _translate_compound_to_ko(value: str) -> str:
    text = value.strip().lower()
    if not text:
        return ""
    if text in TOKEN_MAP_KO:
        return TOKEN_MAP_KO[text]
    parts = [p for p in text.replace("_", "-").replace(" ", "-").split("-") if p]
    if not parts:
        return ""
    mapped = [TOKEN_MAP_KO.get(p, p) for p in parts]
    return " ".join(mapped)


def _fallback_translate_from_to_ko(value: str) -> str:
    raw = value.strip()
    lowered = raw.lower()
    if not raw:
        return ""

    if lowered in NPC_SOURCE_MAP_KO:
        return NPC_SOURCE_MAP_KO[lowered]

    # "ripe orange-pumpkin plant" 같은 패턴
    if lowered.startswith("ripe ") and lowered.endswith(" plant"):
        inner = lowered[len("ripe ") : -len(" plant")].strip()
        inner_ko = _translate_compound_to_ko(inner)
        return f"익은 {inner_ko} 식물" if inner_ko else "익은 식물"

    suffix_map = {
        " plant": "식물",
        " bag": "씨앗 봉지",
        " start": "모종",
        " tree": "나무",
        " sapling": "묘목",
        " shoot": "죽순",
        " envelope": "봉투",
    }
    for suffix_en, suffix_ko in suffix_map.items():
        if lowered.endswith(suffix_en):
            head = lowered[: -len(suffix_en)].strip()
            head_ko = _translate_compound_to_ko(head)
            return f"{head_ko} {suffix_ko}".strip() if head_ko else suffix_ko

    compound = _translate_compound_to_ko(lowered)
    if compound and compound != lowered:
        return compound

    return raw


def _translate_from_to_ko(value: str) -> str:
    text = value.strip()
    lowered = text.lower()
    if not text:
        return ""
    for en, ko in FROM_MAP_KO.items():
        if en in lowered:
            return ko
    return _fallback_translate_from_to_ko(text)


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
    text = str(value).strip()
    if not text:
        return ""
    # "A, B, C" 형태의 원문은 각각 번역한 뒤 다시 결합한다.
    if "," in text:
        parts = [p.strip() for p in text.split(",") if p.strip()]
        translated = [_translate_from_to_ko(p) for p in parts]
        return ", ".join(dict.fromkeys(translated))
    return _translate_from_to_ko(text)


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
