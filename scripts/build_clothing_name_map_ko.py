from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.request import urlopen

URL = "https://nookipedia.com/wiki/Clothing/New_Horizons/Names_in_other_languages"
OUT = Path(__file__).resolve().parent.parent / "data" / "clothing_name_map_ko.json"


def clean(raw: str) -> str:
    txt = re.sub(r"<[^>]+>", "", raw)
    txt = html.unescape(txt)
    txt = " ".join(txt.split())
    return txt.strip()


def main() -> None:
    with urlopen(URL, timeout=30) as res:
        page = res.read().decode("utf-8")

    rows = re.findall(r"<tr>\\s*(.*?)\\s*</tr>", page, flags=re.S)
    name_map: dict[str, str] = {}
    for row in rows:
        en_m = re.search(r'<td class="field_English">(.*?)</td>', row, flags=re.S)
        ko_m = re.search(r'<td class="field_Korean">(.*?)</td>', row, flags=re.S)
        if not en_m or not ko_m:
            continue
        en = clean(en_m.group(1))
        ko = clean(ko_m.group(1))
        if en and ko:
            name_map[en] = ko

    ordered = {k: name_map[k] for k in sorted(name_map.keys(), key=lambda s: s.lower())}
    OUT.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(ordered)} entries to {OUT}")


if __name__ == "__main__":
    main()
