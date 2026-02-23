from __future__ import annotations

from typing import Any

FROM_MAP_KO = {
    "able sisters, hospital": "에이블 시스터즈(병원)",
    "able sisters, apparel shop": "에이블 시스터즈(의류점)",
    "kicks, able sisters": "신발가게 킥스, 에이블 시스터즈",
    "leif, school": "레온(학교)",
    "paradise planning office": "파라다이스 플래닝 사무소",
    "hotel souvenir shop": "호텔 기념품점",
    "custom fencing in a flash": "뚝딱! 울타리 리폼 BOOK",
    "pretty good tools recipes": "언제나 쓸 수 있는 도구 레시피",
    "test your diy skills": "도전! DIY 레시피",
    "wildest dreams diy": "무엇이든 뚝딱?! DIY 레시피",
    "diy for beginners": "첫 DIY 레시피",
    "farway museum": "파어웨어 박물관",
    "nook inc.": "너굴 주식회사",
    "starting item": "초기 지급 아이템",
    "message bottle": "메시지 보틀",
    "big sister villager": "단순활발 주민",
    "cranky villager": "무뚝뚝 주민",
    "jock villager": "운동광 주민",
    "lazy villager": "먹보 주민",
    "normal villager": "친절함 주민",
    "peppy villager": "아이돌 주민",
    "smug villager": "느끼함 주민",
    "snooty villager": "성숙함 주민",
    "apparel shop": "의류점",
    "able sisters": "에이블 시스터즈",
    "katrina": "점쟁이 카트리나",
    "kicks": "신발가게 킥스",
    "leif": "늘봉",
    "nooklink": "너굴링크",
    "bunny day": "이스터 이벤트",
    "egg bottle": "이스터 병편지",
    "wilbur": "모리",
    "kapp'n": "갑돌",
    "café": "카페",
    "cafe": "카페",
    "bank of nook": "너굴 은행",
    "may day": "메이데이",
    "joan": "무주니",
    "restaurant": "레스토랑",
    "hospital": "병원",
    "school": "학교",
    "axe": "도끼",
    "nook's cranny": "너굴상점",
    "nook shopping": "너굴 쇼핑",
    "nook stop": "너굴포트",
    "diy recipe": "요리도 DIY! 레시피＋",
    "diy recipes": "요리도 DIY! 레시피＋",
    "balloon": "풍선 선물",
    "balloon presents": "풍선 선물",
    "saharah": "러그 상인 사하라",
    "redd": "여욱이 상점",
    "redd's raffle": "여욱이 제비뽑기",
    "gulliver": "죠니",
    "gullivarr": "해적 죠니",
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
    "dj kk concert": "케이케이 공연",
    "group stretching": "단체 체조",
    "hip reaction collection": "힙 리액션 컬렉션",
    "jack": "펌킹",
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
    "any villager": "모든 주민",
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
    "posters": "파니엘의 섬 포토스튜디오에서 촬영하기",
    "trade in 3 of the bug": "곤충 포인트 3개 교환",
    "trade in 3 of the fish": "물고기 포인트 3개 교환",
    "from the \"redeem nook miles\" section": "너굴 마일 교환에서 획득",
    "summer": "여름",
    "seasonal": "계절 한정",
    "winter": "겨울",
    "spring": "봄",
    "fall": "가을",
    "from the chef": "요리사에게서 획득",
    "sanrio": "산리오 콜라보",
    "mailbox": "우편함",
    "picking": "채집",
    "harv's island": "파니엘의 섬",
    "daily selection": "일일 진열",
    "fireworks show": "불꽃놀이 축제",
    "wedding season": "결혼 시즌",
    "on boat tours": "보트 투어에서 획득",
    "on boat tours or on the main archipelago island": "보트 투어 또는 군도 본섬에서 획득",
    "''super mario bros.'' 35th anniversary": "슈퍼 마리오 브라더스 35주년",
    "bug-off": "곤충채집대회",
    "fishing tourney": "낚시대회",
    "after being planted": "식재 후 획득",
    "''splatoon''": "스플래툰 콜라보",
    "''the legend of zelda''": "젤다의 전설 콜라보",
    "resident services tent": "주민서비스 텐트",
    "bunny day": "이스터 이벤트",
    "lego": "레고 콜라보",
    "festive season": "축제 시즌",
    "festivale": "카니발 이벤트",
    "novelty": "노벨티",
    "''pocket camp''": "포켓캠프 연동",
    "mushroom season": "버섯 시즌",
    "reward for making a perfect snow person during winter": "겨울에 완벽한 눈사람 제작 보상",
    "special": "특수",
    "[[summer]]": "여름",
    "after completing 4 hotel rooms": "호텔 객실 4개 완성 후",
    "october": "10월",
    "maple leaf season": "단풍 시즌",
    "redeeming nook points": "너굴 포인트 교환",
    "turkey day": "추수감사절",
    "[[winter]]": "겨울",
    "from franklin or nook's cranny": "프랭클린 또는 너굴상점에서 획득",
    "obtained during the main storyline during the villager house development quest": "주민 집 개발 메인 스토리 진행 중 획득",
    "toy day": "토이데이",
    "shaking": "흔들기",
    "chopping with an axe": "도끼로 벌목",
    "slumber island": "꿈섬",
    "catching a salmon": "연어 낚시",
    "doctor exam": "병원 진찰",
    "international museum day": "박물관의 날",
    "mailed to the player": "우편으로 수령",
    "sent in the mail after purchasing turnips": "무 구매 후 우편 수령",
    "trading": "교환",
    "trading 3 other eggs": "다른 알 3개 교환",
    "happy home paradise": "해피홈 파라다이스",
    "collect enough earth eggs": "땅알 수집 보상",
    "collect enough leaf eggs": "잎알 수집 보상",
    "collect enough sky eggs": "하늘알 수집 보상",
    "collect enough stone eggs": "돌알 수집 보상",
    "collect enough water eggs": "물알 수집 보상",
    "collect enough wood eggs": "나무알 수집 보상",
    "trade candy or a lollipop with a villager": "주민에게 사탕/막대사탕 교환",
    "[[countdown]]": "카운트다운",
    "don't return it in time": "제시간 내 미반납",
    "used for apparel shop": "의류점 사용 아이템",
    "catch all types of trash": "모든 쓰레기 낚시 보상",
    "catching a squid": "오징어 낚시",
    "catching an anchovy": "멸치 낚시",
    "helping him 30 times": "30회 도움 보상",
    "jingle": "루돌",
    "obtained as a reward for gifting candy on halloween": "할로윈 사탕 선물 보상",
    "obtained as a reward for gifting candy on halloween.": "할로윈 사탕 선물 보상",
    "obtained as a reward for gifting candy or lollipop on halloween.": "할로윈 사탕/막대사탕 선물 보상",
    "obtained during bunny day": "이스터 기간 획득",
    "obtained through tom nook's diy workshop at the beginning of the game": "게임 초반 너굴 DIY 워크숍에서 획득",
    "only on the day of a [[fireworks show]]": "불꽃놀이 당일 한정",
    "pavé / 상세 조건: [[festivale]]": "베르리나(카니발)",
    "received via mail": "우편 수령",
    "reward for gifting lollipop on halloween": "할로윈 막대사탕 선물 보상",
    "reward for gifting lollipop on halloween.": "할로윈 막대사탕 선물 보상",
    "reward for making a perfect snowboy during winter": "겨울 완벽한 눈사람 보상",
    "while performing the quest for gullivarrr": "해적 죠니 퀘스트 진행 중",
    "from the teacher": "선생님에게서 획득",
    "cherry blossom season": "벚꽃 시즌",
    "valentine's day": "발렌타인데이",
    "on mystery islands": "마일섬에서 획득",
    "on beaches": "해변에서 획득",
    "gulliver": "죠니 관련",
    "gullivarrr": "해적 죠니 관련",
    "available at the start": "초기 상태에서 획득 가능",
    "after completing all 8 hotel rooms": "호텔 객실 8개 완성 후",
    "after wrapping bells": "벨 포장 후",
    "give candy or a lollipop": "사탕 또는 막대사탕 전달",
    "only available as a work clothes for paradise planning": "파라다이스 플래닝 작업복 전용",
    "learn all 18 egg clothing recipes": "알 의상 레시피 18종 습득 후",
    "music festival": "음악제",
    "small": "소형",
    "ground": "지면",
    "complete his vacation home": "해당 주민 별장 완성 후",
    "day after gulliver visits": "죠니 방문 다음날",
    "day after gullivarrr visits": "해적 죠니 방문 다음날",
    "day after gulliver/gullivarrr visits": "죠니/해적 죠니 방문 다음날",
    "nintendo switch 2 edition": "닌텐도 스위치 2 에디션",
    "after being buried on shining soil": "빛나는 땅 매설 후",
    "after being used": "사용 후",
    "after wrapping a item": "아이템 포장 후",
    "at five stars - on cliffs": "섬 평점 5성, 절벽에서 획득",
    "available after unlocking the axe in the story": "스토리에서 도끼 해금 후",
    "available after unlocking the shovel in the story": "스토리에서 삽 해금 후",
    "breaking 100 axes": "도끼 100개 파손 달성",
    "catch 15 trash": "쓰레기 15개 낚시",
    "catch 3 empty cans": "빈 캔 3개 낚시",
    "catch a boot": "장화 낚시",
    "catch an empty can": "빈 캔 낚시",
    "catching 3 old tires": "낡은 타이어 3개 낚시",
    "completing the bug critterpedia": "곤충 도감 완성",
    "completing the fish critterpedia": "물고기 도감 완성",
    "countdown": "카운트다운",
    "earning ": "마일리지 달성 보상",
    "frequent-flyer program": "마일리지 프로그램",
    "expired": "기간 만료",
    "large fish": "대형 물고기",
    "medium fish": "중형 물고기",
    "march 10 to march 17 - shamrock day": "3월 10일~3월 17일 성 패트릭의 날",
    "obtained after completing his diy workshop at the beginning of the game": "게임 초반 DIY 워크숍 완료 후 획득",
    "obtained after the 7th photoshoot": "7회차 촬영 후 획득",
    "obtained during the main storyline after the player completes the villager house development quest": "주민 집 개발 퀘스트 완료 후 메인 스토리에서 획득",
    "obtained during the main storyline during the customization workshop": "리폼 워크숍 진행 중 메인 스토리에서 획득",
    "obtained from tom nook after completing his diy workshop at the beginning of the game": "게임 초반 DIY 워크숍 완료 후 너굴에게서 획득",
    "only if island's native fruit is cherries": "섬 고유 과일이 체리일 때만",
    "only if island's native fruit is apples": "섬 고유 과일이 사과일 때만",
    "only if island's native fruit is oranges": "섬 고유 과일이 오렌지일 때만",
    "only if island's native fruit is peaches": "섬 고유 과일이 복숭아일 때만",
    "only if island's native fruit is pears": "섬 고유 과일이 배일 때만",
    "receive 5-star island evaluation": "섬 평점 5성 달성 보상",
    "redeemed nook points": "너굴 포인트 교환",
}

NPC_SOURCE_MAP_KO = {
    "blathers": "부엉",
    "brewster": "마스터",
    "c.j.": "저스틴",
    "celeste": "부옥",
    "cornimer": "콘키",
    "cyrus": "리포",
    "daisy mae": "무파니",
    "dodo airlines": "도도항공",
    "flick": "레온",
    "franklin": "칠면조 프랭클린",
    "happy home academy": "해피홈 아카데미",
    "harvey": "파니엘",
    "isabelle": "여울",
    "jingle": "루돌",
    "label": "케이트",
    "lloid": "토용이",
    "lottie": "니코",
    "luna": "몽셰르",
    "mabel": "고순",
    "mom": "엄마",
    "niko": "니코",
    "nintendo": "닌텐도",
    "pascal": "해탈한",
    "pavé": "베르리나",
    "reese": "리포",
    "resetti": "리셋씨",
    "rover": "모리",
    "snowboy": "완벽한 눈사람",
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


def _availability_pairs(value: Any) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []

    if isinstance(value, dict):
        froms: list[str] = []
        notes: list[str] = []
        from_value = value.get("from")
        note_value = value.get("note")

        if isinstance(from_value, list):
            froms = [str(v).strip() for v in from_value if str(v).strip()]
        elif from_value is not None:
            s = str(from_value).strip()
            if s:
                froms = [s]

        if isinstance(note_value, list):
            notes = [str(v).strip() for v in note_value if str(v).strip()]
        elif note_value is not None:
            s = str(note_value).strip()
            if s:
                notes = [s]

        if froms:
            if notes and len(notes) == len(froms):
                out.extend(list(zip(froms, notes)))
            elif notes:
                joined_note = " / ".join(dict.fromkeys(notes))
                out.extend([(f, joined_note) for f in froms])
            else:
                out.extend([(f, "") for f in froms])
        elif notes:
            out.extend([("", n) for n in notes])

    elif isinstance(value, list):
        for x in value:
            out.extend(_availability_pairs(x))
    elif isinstance(value, str):
        s = value.strip()
        if s:
            out.append((s, ""))

    return out


def extract_source_pairs(row: dict[str, Any]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def push_pair(source_raw: str, note_raw: str) -> None:
        src = _translate_from_to_ko(source_raw) if source_raw else ""
        note = _translate_note_to_ko(note_raw) if note_raw else ""
        key = (src, note)
        if (not src and not note) or key in seen:
            return
        seen.add(key)
        pairs.append(key)

    for src_raw, note_raw in _availability_pairs(row.get("availability")):
        push_pair(src_raw, note_raw)

    if not pairs:
        source_text = translate_source_value_to_ko(row.get("source"))
        raw_note = str(
            row.get("source_notes")
            or row.get("source_note")
            or row.get("availability_notes")
            or ""
        ).strip()
        note_text = _translate_note_to_ko(raw_note) if raw_note else ""
        source_parts = [
            p.strip()
            for p in str(source_text or "").split(",")
            if p and p.strip()
        ]
        if source_parts:
            for part in source_parts:
                key = (part, note_text)
                if key not in seen:
                    seen.add(key)
                    pairs.append(key)
        elif note_text:
            key = ("", note_text)
            if key not in seen:
                seen.add(key)
                pairs.append(key)

    if pairs:
        return pairs

    variations = row.get("variations")
    if not isinstance(variations, list):
        return []

    for variation in variations:
        if not isinstance(variation, dict):
            continue
        for src_raw, note_raw in _availability_pairs(variation.get("availability")):
            push_pair(src_raw, note_raw)
        source_text = translate_source_value_to_ko(variation.get("source"))
        raw_note = str(
            variation.get("source_notes")
            or variation.get("source_note")
            or variation.get("availability_notes")
            or ""
        ).strip()
        note_text = _translate_note_to_ko(raw_note) if raw_note else ""
        source_parts = [
            p.strip()
            for p in str(source_text or "").split(",")
            if p and p.strip()
        ]
        for part in source_parts:
            key = (part, note_text)
            if key not in seen:
                seen.add(key)
                pairs.append(key)

    return pairs


def extract_source_pair(row: dict[str, Any]) -> tuple[str, str]:
    pairs = extract_source_pairs(row)
    if pairs:
        source = ", ".join(dict.fromkeys([src for src, _ in pairs if src]))
        source_notes = " / ".join(dict.fromkeys([note for _, note in pairs if note]))
        return source, source_notes

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
