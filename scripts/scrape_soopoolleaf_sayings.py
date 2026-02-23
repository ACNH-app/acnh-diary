from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://animalcrossing.soopoolleaf.com"
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.content_db import get_content_db

DEFAULT_OUT = ROOT / "data" / "villager_saying_map_ko.json"
ACNHAPI_VILLAGERS_JSON = ROOT / "data" / "acnhapi" / "villagers.json"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def fetch_text(url: str, timeout: float = 20.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_tags(raw: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def try_extract_cell(html_text: str, label: str) -> str:
    # Table forms: <th>좋아하는 말</th><td>...</td>
    pat = re.compile(
        rf"<th[^>]*>\s*{re.escape(label)}\s*</th>\s*<td[^>]*>(.*?)</td>",
        re.I | re.S,
    )
    m = pat.search(html_text)
    if m:
        return strip_tags(m.group(1))
    # Div forms: label then sibling value
    pat2 = re.compile(
        rf"{re.escape(label)}\s*</[^>]+>\s*<[^>]+>\s*(.*?)\s*</[^>]+>",
        re.I | re.S,
    )
    m2 = pat2.search(html_text)
    if m2:
        return strip_tags(m2.group(1))
    # Text fallback
    text = strip_tags(html_text)
    m3 = re.search(rf"{re.escape(label)}\s*[:：]\s*([^\n]+)", text)
    if m3:
        return re.sub(r"\s+", " ", m3.group(1)).strip()
    return ""


def extract_name_and_saying(html_text: str) -> tuple[str, str]:
    # soopoolleaf 주민 상세 고정 셀 우선
    m_like = re.search(
        r'<td[^>]*id=["\']id_LikePh["\'][^>]*>(.*?)</td>',
        html_text,
        flags=re.I | re.S,
    )
    saying = strip_tags(m_like.group(1)) if m_like else ""

    m_name = re.search(
        r'<td[^>]*id=["\']id_Name["\'][^>]*>(.*?)</td>',
        html_text,
        flags=re.I | re.S,
    )
    name = strip_tags(m_name.group(1)) if m_name else ""

    if name and saying:
        return name, saying

    name = try_extract_cell(html_text, "이름")
    if not saying:
        saying = try_extract_cell(html_text, "좋아하는 말")

    # Name fallback: title
    if not name:
        m = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.I | re.S)
        if m:
            title = strip_tags(m.group(1))
            # "1호 | ..." 형태일 수 있어 앞 토큰만 우선 사용
            name = re.split(r"\||\-", title)[0].strip()

    return name, saying


def extract_acna_urls(html_text: str) -> set[str]:
    out: set[str] = set()
    for m in re.finditer(r"(https://animalcrossing\.soopoolleaf\.com)?(/ko/acna/[A-Za-z0-9_%.\-]+/?)", html_text):
        path = m.group(2)
        out.add(urllib.parse.urljoin(BASE, path))
    return out


def gather_from_sitemaps(verbose: bool = False) -> set[str]:
    candidates = [
        f"{BASE}/sitemap.xml",
        f"{BASE}/sitemap_index.xml",
    ]
    out: set[str] = set()
    for url in candidates:
        try:
            xml = fetch_text(url, timeout=12.0)
        except Exception:
            continue
        locs = re.findall(r"<loc>(.*?)</loc>", xml, flags=re.I | re.S)
        if verbose:
            print(f"[sitemap] {url}: {len(locs)} locs")
        for loc in locs:
            loc = html.unescape(loc.strip())
            if "/ko/acna/" in loc:
                out.add(loc)
            elif loc.endswith(".xml"):
                try:
                    subxml = fetch_text(loc, timeout=12.0)
                except Exception:
                    continue
                for sub in re.findall(r"<loc>(.*?)</loc>", subxml, flags=re.I | re.S):
                    sub = html.unescape(sub.strip())
                    if "/ko/acna/" in sub:
                        out.add(sub)
    return out


def gather_category_urls(verbose: bool = False) -> list[str]:
    roots = [
        f"{BASE}/ko/acnh/animalsearch/",
        f"{BASE}/ko/acnh/animalsearch/?soopoolleaf=all",
    ]
    cats: set[str] = set()
    for root in roots:
        try:
            txt = fetch_text(root)
        except Exception:
            continue
        for href in re.findall(r'href="([^"]+)"', txt, flags=re.I):
            if "Category=" not in href:
                continue
            full = urllib.parse.urljoin(root, href)
            if "/ko/acnh/animalsearch/" in full:
                cats.add(full)
    out = sorted(cats)
    if verbose:
        print(f"[categories] found {len(out)}")
    return out


def gather_acna_urls_from_categories(verbose: bool = False) -> set[str]:
    out: set[str] = set()
    categories = gather_category_urls(verbose=verbose)
    for idx, cat_url in enumerate(categories, start=1):
        try:
            txt = fetch_text(cat_url)
        except Exception:
            continue
        out |= extract_acna_urls(txt)
        if verbose and idx % 5 == 0:
            print(f"[categories] {idx}/{len(categories)} -> urls: {len(out)}")
        time.sleep(0.08)
    return out


def slug_candidates_from_name(name_en: str) -> list[str]:
    base = name_en.strip()
    if not base:
        return []
    normalized = (
        base.replace("é", "e")
        .replace("É", "E")
        .replace("á", "a")
        .replace("Á", "A")
        .replace("í", "i")
        .replace("Í", "I")
        .replace("ó", "o")
        .replace("Ó", "O")
        .replace("ú", "u")
        .replace("Ú", "U")
    )
    s1 = re.sub(r"\s+", "_", normalized)
    variants = {
        s1,
        s1.replace("'", ""),
        s1.replace("'", "_"),
        s1.replace(".", ""),
        s1.replace("&", "and"),
        s1.replace("&", ""),
    }
    # clean double underscores
    cleaned = {re.sub(r"_+", "_", v).strip("_") for v in variants}
    return [v for v in cleaned if v]


def build_slug_name_map(verbose: bool = False) -> dict[str, str]:
    out: dict[str, str] = {}
    if not ACNHAPI_VILLAGERS_JSON.exists():
        return out
    data = json.loads(ACNHAPI_VILLAGERS_JSON.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        for row in data.values():
            if not isinstance(row, dict):
                continue
            name_obj = row.get("name") or {}
            if not isinstance(name_obj, dict):
                continue
            name_en = str(name_obj.get("name-USen") or name_obj.get("name-EUen") or "").strip()
            name_ko = str(name_obj.get("name-KRko") or "").strip()
            if not (name_en and name_ko):
                continue
            for slug in slug_candidates_from_name(name_en):
                out.setdefault(slug, name_ko)

    # DB에만 있는 주민(예: DLC/특수)도 보강
    try:
        with get_content_db() as conn:
            rows = conn.execute("SELECT name_en, name_ko FROM villagers").fetchall()
        for r in rows:
            name_en = str(r["name_en"] or "").strip()
            name_ko = str(r["name_ko"] or "").strip()
            if not (name_en and name_ko):
                continue
            for slug in slug_candidates_from_name(name_en):
                out.setdefault(slug, name_ko)
    except Exception:
        pass

    if verbose:
        print(f"[slug-map] size={len(out)}")
    return out


def build_en_name_map_ko() -> dict[str, str]:
    out: dict[str, str] = {}
    if ACNHAPI_VILLAGERS_JSON.exists():
        data = json.loads(ACNHAPI_VILLAGERS_JSON.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for row in data.values():
                if not isinstance(row, dict):
                    continue
                name_obj = row.get("name") or {}
                if not isinstance(name_obj, dict):
                    continue
                name_en = str(name_obj.get("name-USen") or name_obj.get("name-EUen") or "").strip()
                name_ko = str(name_obj.get("name-KRko") or "").strip()
                if name_en and name_ko:
                    out[name_en.lower()] = name_ko
    try:
        with get_content_db() as conn:
            rows = conn.execute("SELECT name_en, name_ko FROM villagers").fetchall()
        for r in rows:
            name_en = str(r["name_en"] or "").strip()
            name_ko = str(r["name_ko"] or "").strip()
            if name_en and name_ko:
                out.setdefault(name_en.lower(), name_ko)
    except Exception:
        pass
    return out


def gather_acna_urls_from_slug_map(slug_map: dict[str, str], verbose: bool = False) -> set[str]:
    out: set[str] = set()
    for idx, slug in enumerate(sorted(slug_map.keys()), start=1):
        out.add(f"{BASE}/ko/acna/{slug}/")
        if verbose and idx % 100 == 0:
            print(f"[names] {idx}/{len(slug_map)} -> url candidates: {len(out)}")
    return out


def scrape_sayings(
    acna_urls: list[str],
    slug_name_map: dict[str, str],
    en_name_map_ko: dict[str, str],
    verbose: bool = False,
) -> dict[str, str]:
    out: dict[str, str] = {}
    lower_slug_name_map = {k.lower(): v for k, v in slug_name_map.items()}
    saying_only = 0
    parse_fail = 0
    for idx, url in enumerate(acna_urls, start=1):
        try:
            html_text = fetch_text(url)
        except urllib.error.HTTPError:
            continue
        except Exception:
            continue
        m_slug = re.search(r"/ko/acna/([A-Za-z0-9_%.\-]+)/?", url)
        slug = urllib.parse.unquote(m_slug.group(1)) if m_slug else ""
        canonical_name = slug_name_map.get(slug, "") or lower_slug_name_map.get(slug.lower(), "")
        name, saying = extract_name_and_saying(html_text)
        if not canonical_name:
            if name and re.search(r"[가-힣]", name):
                canonical_name = name
            else:
                canonical_name = en_name_map_ko.get(name.lower(), "") if name else ""
        if canonical_name and saying:
            out[canonical_name] = saying
        elif saying and not name:
            saying_only += 1
        else:
            parse_fail += 1
        if verbose and idx % 50 == 0:
            print(
                f"[scrape] {idx}/{len(acna_urls)} -> sayings: {len(out)} "
                f"(saying_only={saying_only}, parse_fail={parse_fail})"
            )
        time.sleep(0.05)
    if verbose:
        print(f"[scrape] done -> sayings={len(out)}, saying_only={saying_only}, parse_fail={parse_fail}")
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape villager saying(좋아하는 말) from soopoolleaf.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output json path")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verbose = bool(args.verbose)

    slug_name_map = build_slug_name_map(verbose=verbose)
    en_name_map_ko = build_en_name_map_ko()
    urls: set[str] = set()
    urls |= gather_acna_urls_from_slug_map(slug_name_map, verbose=verbose)
    # 백업 경로: 사이트 내 acna URL이 정적으로 존재하면 추가로 수집
    urls |= gather_acna_urls_from_categories(verbose=verbose)

    acna_urls = sorted(urls)
    if verbose:
        print(f"[urls] total candidates: {len(acna_urls)}")
    if not acna_urls:
        print("No acna URL candidates found.")
        return 2

    sayings = scrape_sayings(
        acna_urls,
        slug_name_map=slug_name_map,
        en_name_map_ko=en_name_map_ko,
        verbose=verbose,
    )
    # 주민명(한글) 키만 유지
    sayings = {k: v for k, v in sayings.items() if k and re.search(r"[가-힣]", k)}
    sayings = dict(sorted(sayings.items(), key=lambda kv: kv[0]))
    if verbose:
        try:
            with get_content_db() as conn:
                rows = conn.execute("SELECT name_ko FROM villagers WHERE name_ko <> ''").fetchall()
            all_names = {str(r["name_ko"]).strip() for r in rows if str(r["name_ko"]).strip()}
            missing = sorted(all_names - set(sayings.keys()))
            print(f"[missing] {len(missing)} villagers")
            if missing:
                print("[missing-list]", ", ".join(missing))
        except Exception:
            pass
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(sayings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"saved: {args.out} ({len(sayings)} sayings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
