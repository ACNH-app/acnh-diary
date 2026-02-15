from __future__ import annotations

import json
import re
from pathlib import Path

from app.services.catalog_data import load_catalog, load_villagers


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "photo_name_map_ko.json"

PHOTO_PAT = re.compile(r"^(.+?)'s photo$")
POSTER_PAT = re.compile(r"^(.+?)'s poster$")

SPECIAL_POSTER_MAP = {
    "Hello Kitty poster": "헬로키티 포스터",
    "Cinnamoroll poster": "시나모롤 포스터",
    "My Melody poster": "마이멜로디 포스터",
    "Kerokerokeroppi poster": "케로케로케로피 포스터",
    "Kiki & Lala poster": "키키 & 라라 포스터",
    "Pompompurin poster": "폼폼푸린 포스터",
}

NPC_NAME_MAP = {
    "Blanca": "블랑카",
    "Blathers": "부엉",
    "Booker": "부커",
    "Brewster": "마스터",
    "C.J.": "저스틴",
    "Celeste": "부옥",
    "Chip": "칩",
    "Copper": "코퍼",
    "Cyrus": "사이러스",
    "DJ KK": "DJ 케이케이",
    "Daisy Mae": "무파니",
    "Digby": "디그비",
    "Don": "돈",
    "Flick": "레온",
    "Franklin": "프랭클린",
    "Gracie": "그레이스",
    "Grams": "그램스",
    "Gulliver": "걸리버",
    "Harriet": "해리엇",
    "Harvey": "파니엘",
    "Isabelle": "여울",
    "Jack": "잭",
    "Jingle": "징글",
    "Joan": "조앤",
    "K.K.": "케이케이",
    "Kapp'n": "갑돌",
    "Katie": "케이티",
    "Katrina": "카트리나",
    "Kicks": "패트릭",
    "Label": "케이트",
    "Leif": "레이지",
    "Leila": "레일라",
    "Leilani": "레일라니",
    "Lottie": "로티",
    "Luna": "루나",
    "Lyle": "라일",
    "Mabel": "고숙이",
    "Nat": "낫",
    "Niko": "니코",
    "Orville": "모리스",
    "Pascal": "해탈한",
    "Pavé": "파베",
    "Pelly": "펠리",
    "Pete": "피트",
    "Phineas": "피니어스",
    "Phyllis": "필리스",
    "Porter": "포터",
    "Redd": "여욱",
    "Reese": "리사",
    "Resetti": "리셋티",
    "Rover": "차둘",
    "Sable": "말숙이",
    "Saharah": "사하라",
    "Shrunk": "슈렁크",
    "Timmy": "콩돌",
    "Timmy and Tommy": "콩돌&밤돌",
    "Tom Nook": "너굴",
    "Tommy": "밤돌",
    "Tortimer": "토터머",
    "Villager": "주민",
    "Wardell": "워델",
    "Wendell": "웬델",
    "Wilbur": "로드리",
    "Wisp": "깨빈",
    "Zipper": "토빗",
}


def main() -> None:
    villagers = load_villagers()
    villager_map = {
        str(v.get("name_en") or "").strip(): str(v.get("name_ko") or "").strip()
        for v in villagers
        if str(v.get("name_en") or "").strip()
    }

    rows = load_catalog("photos")
    names = sorted({str(r.get("name_en") or "").strip() for r in rows if str(r.get("name_en") or "").strip()})

    mapped: dict[str, str] = {}
    unchanged: list[str] = []
    for name_en in names:
        if name_en in SPECIAL_POSTER_MAP:
            mapped[name_en] = SPECIAL_POSTER_MAP[name_en]
            continue

        m = PHOTO_PAT.match(name_en)
        if m:
            base = m.group(1).strip()
            base_ko = villager_map.get(base, NPC_NAME_MAP.get(base, base))
            mapped[name_en] = f"{base_ko}의 사진"
            if base_ko == base:
                unchanged.append(name_en)
            continue

        m = POSTER_PAT.match(name_en)
        if m:
            base = m.group(1).strip()
            base_ko = villager_map.get(base, NPC_NAME_MAP.get(base, base))
            mapped[name_en] = f"{base_ko}의 포스터"
            if base_ko == base:
                unchanged.append(name_en)
            continue

        mapped[name_en] = name_en
        unchanged.append(name_en)

    OUT_PATH.write_text(
        json.dumps(mapped, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"written: {OUT_PATH}")
    print(f"total: {len(mapped)}")
    print(f"base-name-unmapped: {len(unchanged)}")
    for x in unchanged[:120]:
        print(" -", x)


if __name__ == "__main__":
    main()
