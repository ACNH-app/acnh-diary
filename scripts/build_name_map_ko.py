from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.request import urlopen

BASE = Path(__file__).resolve().parent.parent
VILLAGERS_JSON = BASE / "villagers.json"
OUT = BASE / "data" / "name_map_ko.json"

LIST_URL = "https://nookipedia.com/wiki/List_of_villager_names_in_other_languages"
ZOE_URL = "https://nookipedia.com/wiki/Zoe"


def clean_text(raw: str) -> str:
    text = re.sub(r"<[^>]+>", "", raw)
    text = html.unescape(text)
    text = " ".join(text.split())
    return text.strip()


def extract_hangul_prefix(raw: str) -> str:
    m = re.match(r"([가-힣0-9호]+)", raw)
    return m.group(1) if m else ""


def build() -> dict[str, str]:
    source = json.loads(VILLAGERS_JSON.read_text(encoding="utf-8"))
    name_map: dict[str, str] = {}

    for row in source.values():
        names = row.get("name", {})
        en = str(names.get("name-USen") or "").strip()
        ko = str(names.get("name-KRko") or "").strip()
        if en and ko:
            name_map[en] = ko

    with urlopen(LIST_URL, timeout=30) as res:
        list_html = res.read().decode("utf-8")

    rows = re.findall(r"<tr>\\s*(.*?)\\s*</tr>", list_html, flags=re.S)
    for row in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.S)
        if len(cells) < 7:
            continue

        en = clean_text(cells[0])
        if not en or en in {"English", "Name"}:
            continue

        ko = extract_hangul_prefix(clean_text(cells[6]))
        if ko:
            name_map[en] = ko

    # List page does not currently expose Zoe in that table.
    with urlopen(ZOE_URL, timeout=30) as res:
        zoe_html = res.read().decode("utf-8")
    m = re.search(r"infobox-flag-ko\"[^>]*></div>&#160;<span[^>]*>([^<]+)", zoe_html)
    if m:
        name_map["Zoe"] = m.group(1).strip()

    return {k: name_map[k] for k in sorted(name_map.keys(), key=lambda s: s.lower())}


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = build()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(result)} entries to {OUT}")


if __name__ == "__main__":
    main()
