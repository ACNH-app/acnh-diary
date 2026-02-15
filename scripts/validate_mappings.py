from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

NAME_MAP_PATH = DATA_DIR / "name_map_ko.json"
PERSONALITY_MAP_PATH = DATA_DIR / "personality_map_ko.json"
SPECIES_MAP_PATH = DATA_DIR / "species_map_ko.json"

NOOKIPEDIA_BASE_URL = "https://api.nookipedia.com/villagers"


def normalize_name(value: str) -> str:
    lowered = value.strip().lower()
    cleaned = lowered.replace(".", "").replace("'", "").replace("-", " ")
    return " ".join(cleaned.split())


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_nookipedia_villagers(api_key: str) -> list[dict]:
    query = urlencode({"game": "nh", "nhdetails": "true"})
    req = Request(
        f"{NOOKIPEDIA_BASE_URL}?{query}",
        headers={"X-API-KEY": api_key},
    )
    with urlopen(req, timeout=25) as res:
        return json.loads(res.read().decode("utf-8"))


def main() -> int:
    api_key = os.environ.get("NOOKIPEDIA_API_KEY", "").strip()
    if not api_key:
        print("[ERROR] NOOKIPEDIA_API_KEY is empty. Export it before running this script.")
        return 2

    name_map_raw = load_json(NAME_MAP_PATH)
    personality_map = load_json(PERSONALITY_MAP_PATH)
    species_map = load_json(SPECIES_MAP_PATH)

    name_map = {
        normalize_name(str(k)): str(v).strip()
        for k, v in name_map_raw.items()
        if str(k).strip() and str(v).strip()
    }

    villagers = fetch_nookipedia_villagers(api_key)

    personalities = sorted({str(v.get("personality") or "") for v in villagers if v.get("personality")})
    species = sorted({str(v.get("species") or "") for v in villagers if v.get("species")})

    missing_personalities = [p for p in personalities if p not in personality_map]
    missing_species = [s for s in species if s not in species_map]

    missing_names = []
    for v in villagers:
        name_en = str(v.get("name") or "").strip()
        if not name_en:
            continue
        if normalize_name(name_en) not in name_map:
            missing_names.append(name_en)

    print(f"Villagers: {len(villagers)}")
    print(f"Personality map keys: {len(personality_map)}")
    print(f"Species map keys: {len(species_map)}")
    print(f"Name map keys: {len(name_map)}")

    print("\n[Missing personalities]")
    if missing_personalities:
        for p in missing_personalities:
            print(f"- {p}")
    else:
        print("- none")

    print("\n[Missing species]")
    if missing_species:
        for s in missing_species:
            print(f"- {s}")
    else:
        print("- none")

    print("\n[Missing Korean names]")
    if missing_names:
        for n in sorted(set(missing_names)):
            print(f"- {n}")
    else:
        print("- none")

    if missing_personalities or missing_species or missing_names:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
