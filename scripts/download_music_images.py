from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent.parent
ACNH_MUSIC_PATH = BASE_DIR / "data" / "acnhapi" / "music.json"
NORVIAH_MUSIC_PATH = BASE_DIR / "data" / "norviah-animal-crossing" / "Music.json"
OUT_DIR = BASE_DIR / "static" / "assets" / "music"
MANIFEST_PATH = BASE_DIR / "data" / "music_image_manifest.json"

UA = "Mozilla/5.0 (ACNHDiary local-cache)"


def get_bytes(url: str) -> bytes:
    # 일부 download_url 경로에 공백/비ASCII가 포함되어 있어 안전하게 인코딩한다.
    parts = urlsplit(url)
    safe_path = quote(parts.path, safe="/%")
    safe_url = urlunsplit((parts.scheme, parts.netloc, safe_path, parts.query, parts.fragment))
    req = Request(safe_url, headers={"User-Agent": UA})
    with urlopen(req, timeout=45) as res:
        return res.read()


def load_target_tracks() -> list[tuple[int, str]]:
    ac = json.loads(ACNH_MUSIC_PATH.read_text(encoding="utf-8"))
    targets: list[tuple[int, str]] = []
    seen_names: set[str] = set()

    # 1~95 (acnhapi)
    for row in ac.values():
        if not isinstance(row, dict):
            continue
        rid = int(row.get("id") or 0)
        name_obj = row.get("name") if isinstance(row.get("name"), dict) else {}
        name_en = str(name_obj.get("name-USen") or name_obj.get("name-EUen") or "").strip()
        if rid <= 0 or not name_en:
            continue
        targets.append((rid, name_en))
        seen_names.add(name_en.strip().lower())

    # 96~110 (norviah 누락곡 보강)
    extra_payload = json.loads(NORVIAH_MUSIC_PATH.read_text(encoding="utf-8"))
    if isinstance(extra_payload, list):
        special_name_map = {
            "はずれ01": "Extra Song 1",
            "はずれ02": "Extra Song 2",
            "はずれ03": "Extra Song 3",
        }
        next_number = max((n for n, _ in targets), default=0)
        for row in extra_payload:
            if not isinstance(row, dict):
                continue
            raw_name_en = str(row.get("USen") or "").strip()
            if not raw_name_en:
                continue
            name_en = special_name_map.get(raw_name_en, raw_name_en)
            key = name_en.lower()
            if key in seen_names:
                continue
            seen_names.add(key)
            next_number += 1
            targets.append((next_number, name_en))

    targets.sort(key=lambda x: x[0])
    return targets


def resolve_album_download_url(folder_name: str) -> str:
    folder_name = str(folder_name or "").strip()
    if not folder_name:
        return ""
    raw_path = f"images/Music/{folder_name}/Album Image.png"
    encoded = quote(raw_path, safe="/")
    return f"https://raw.githubusercontent.com/Norviah/acnh-images/master/{encoded}"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = load_target_tracks()

    alt_name_map = {
        "extra song 1": "はずれ01",
        "extra song 2": "はずれ02",
        "extra song 3": "はずれ03",
    }

    manifest: dict[str, dict] = {}
    downloaded = 0
    skipped = 0
    missing = 0

    for num, name in targets:
        key = name.strip().lower()
        candidate_folders = [name]
        if key in alt_name_map:
            candidate_folders.append(alt_name_map[key])

        out_path = OUT_DIR / f"{num}.png"
        rel_path = f"/static/assets/music/{num}.png"
        if out_path.exists() and out_path.stat().st_size > 512:
            manifest[str(num)] = {"name": name, "path": rel_path, "status": "cached"}
            skipped += 1
            continue

        try:
            got = False
            for folder_name in candidate_folders:
                dl = resolve_album_download_url(folder_name)
                if not dl:
                    continue
                try:
                    blob = get_bytes(dl)
                except HTTPError as e:
                    if int(getattr(e, "code", 0) or 0) == 404:
                        continue
                    raise
                if len(blob) < 512:
                    continue
                out_path.write_bytes(blob)
                manifest[str(num)] = {
                    "name": name,
                    "path": rel_path,
                    "status": "downloaded",
                    "folder": folder_name,
                }
                downloaded += 1
                got = True
                break
            if not got:
                manifest[str(num)] = {"name": name, "path": rel_path, "status": "missing-folder"}
                missing += 1
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            manifest[str(num)] = {
                "name": name,
                "path": rel_path,
                "status": "error",
                "error": str(exc),
            }
            missing += 1

    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"targets={len(targets)} downloaded={downloaded} cached={skipped} missing={missing}")
    print(f"manifest={MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
