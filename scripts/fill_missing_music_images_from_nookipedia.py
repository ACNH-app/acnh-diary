from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit, quote
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = BASE_DIR / "data" / "music_image_manifest.json"
OUT_DIR = BASE_DIR / "static" / "assets" / "music"
UA = "Mozilla/5.0 (ACNHDiary image-filler)"

API = "https://nookipedia.com/w/api.php"
CATEGORY_TITLE = "Category:K.K. Slider songs"


def api_get(params: dict[str, str]) -> dict:
    q = urlencode(params)
    req = Request(f"{API}?{q}", headers={"User-Agent": UA})
    with urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def get_category_song_titles() -> set[str]:
    titles: set[str] = set()
    cmcontinue = ""
    while True:
        params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": CATEGORY_TITLE,
            "cmlimit": "500",
            "cmtype": "page",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        data = api_get(params)
        for row in (data.get("query") or {}).get("categorymembers") or []:
            t = str(row.get("title") or "").strip()
            if t:
                titles.add(t)
        cmcontinue = str(((data.get("continue") or {}).get("cmcontinue") or "")).strip()
        if not cmcontinue:
            break
    return titles


def get_page_image_url(title: str) -> str:
    data = api_get(
        {
            "action": "query",
            "format": "json",
            "prop": "pageimages",
            "piprop": "original",
            "titles": title,
        }
    )
    pages = (data.get("query") or {}).get("pages") or {}
    for page in pages.values():
        src = str((page.get("original") or {}).get("source") or "").strip()
        if src:
            return src
    return ""


def download(url: str) -> bytes:
    parts = urlsplit(url)
    safe_path = quote(parts.path, safe="/%")
    safe_url = urlunsplit((parts.scheme, parts.netloc, safe_path, parts.query, parts.fragment))
    req = Request(safe_url, headers={"User-Agent": UA})
    with urlopen(req, timeout=45) as res:
        return res.read()


def main() -> int:
    if not MANIFEST_PATH.exists():
        raise RuntimeError(f"manifest not found: {MANIFEST_PATH}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise RuntimeError("invalid manifest format")

    category_titles = get_category_song_titles()

    targets: list[tuple[str, str]] = []
    for num, row in manifest.items():
        if not isinstance(row, dict):
            continue
        status = str(row.get("status") or "")
        if status not in {"missing-folder", "error", "too-small", "missing-file"}:
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        # 카테고리 기준으로 존재하는 곡만 대상으로 한다.
        if name not in category_titles:
            continue
        targets.append((num, name))

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    still_missing = 0
    for num, name in targets:
        image_url = get_page_image_url(name)
        if not image_url:
            manifest[num]["status"] = "missing-nookipedia-image"
            still_missing += 1
            continue

        try:
            blob = download(image_url)
            if len(blob) < 512:
                manifest[num]["status"] = "missing-nookipedia-image"
                manifest[num]["error"] = f"too_small:{len(blob)}"
                still_missing += 1
                continue
            out = OUT_DIR / f"{num}.png"
            out.write_bytes(blob)
            manifest[num]["status"] = "downloaded"
            manifest[num]["source"] = "nookipedia"
            manifest[num]["image_url"] = image_url
            manifest[num].pop("error", None)
            downloaded += 1
        except Exception as exc:
            manifest[num]["status"] = "error"
            manifest[num]["error"] = str(exc)
            still_missing += 1

    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"category_titles={len(category_titles)} targets={len(targets)} downloaded={downloaded} still_missing={still_missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
