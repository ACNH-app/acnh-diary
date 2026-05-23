from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = ROOT / "data" / "acnhapi" / "villagers.json"
NAME_MAP_PATH = ROOT / "data" / "name_map_ko.json"
PERSONALITY_MAP_PATH = ROOT / "data" / "personality_map_ko.json"
SPECIES_MAP_PATH = ROOT / "data" / "species_map_ko.json"
SAYING_MAP_PATH = ROOT / "data" / "villager_saying_map_ko.json"
OUT_PATH = ROOT / "docs" / "villager-tracker" / "data" / "villagers.json"

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_birthday_parts(text: str) -> tuple[int | None, int | None]:
    parts = str(text or "").replace(",", "").split()
    if len(parts) < 2:
        return None, None
    month = MONTHS.get(parts[0])
    day_text = parts[1].lower().replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")
    try:
        day = int(day_text)
    except ValueError:
        return month, None
    return month, day


def main() -> None:
    source = load_json(SOURCE_PATH)
    name_map = load_json(NAME_MAP_PATH)
    personality_map = load_json(PERSONALITY_MAP_PATH)
    species_map = load_json(SPECIES_MAP_PATH)
    saying_map = load_json(SAYING_MAP_PATH)

    villagers: list[dict] = []

    for key, row in source.items():
        name_obj = row.get("name") or {}
        name_en = str(name_obj.get("name-USen") or "").strip()
        if not name_en:
            continue

        name_ko = str(name_obj.get("name-KRko") or "").strip() or str(name_map.get(name_en) or "").strip()
        personality = str(row.get("personality") or "").strip()
        species = str(row.get("species") or "").strip()
        birthday_text = str(row.get("birthday-string") or "").strip()
        birthday_month, birthday_day = parse_birthday_parts(birthday_text)

        villagers.append(
            {
                "id": int(row.get("id") or 0),
                "key": key,
                "fileName": str(row.get("file-name") or key).strip(),
                "nameKo": name_ko or name_en,
                "nameEn": name_en,
                "personality": personality,
                "personalityKo": str(personality_map.get(personality) or personality).strip(),
                "species": species,
                "speciesKo": str(species_map.get(species) or species).strip(),
                "gender": str(row.get("gender") or "").strip(),
                "hobby": str(row.get("hobby") or "").strip(),
                "subtype": str(row.get("subtype") or "").strip(),
                "birthdayText": birthday_text,
                "birthdayMonth": birthday_month,
                "birthdayDay": birthday_day,
                "catchphraseEn": str(row.get("catch-phrase") or "").strip(),
                "catchphraseKo": str(((row.get("catch-translations") or {}).get("catch-KRko")) or "").strip(),
                "sayingEn": str(row.get("saying") or "").strip(),
                "sayingKo": str(saying_map.get(name_en) or "").strip(),
                "bubbleColor": str(row.get("bubble-color") or "").strip(),
                "textColor": str(row.get("text-color") or "").strip(),
                "iconUri": str(row.get("icon_uri") or "").strip(),
                "imageUri": str(row.get("image_uri") or "").strip(),
                "imagePath": f"./assets/villagers/{str(row.get('file-name') or key).strip()}.png",
            }
        )

    villagers.sort(key=lambda item: ((item["nameKo"] or item["nameEn"]).lower(), item["id"]))

    payload = {
        "generatedAt": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "count": len(villagers),
        "items": villagers,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(villagers)} villagers to {OUT_PATH}")


if __name__ == "__main__":
    main()
