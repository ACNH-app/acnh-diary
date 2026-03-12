from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST_DIR = BASE_DIR / 'data' / 'offline_asset_manifests'
OUT_DIR = BASE_DIR / 'static' / 'assets' / 'offline'
URL_CACHE_DIR = OUT_DIR / '_url_cache'
URL_MAP_PATH = MANIFEST_DIR / 'offline_url_map.json'
DOWNLOAD_REPORT_PATH = MANIFEST_DIR / 'offline_download_report.json'

UA = 'Mozilla/5.0 (ACNHDiary offline-image-downloader)'
TIMEOUT_SEC = 60
MAX_WORKERS = 12
MIN_VALID_BYTES = 256


def _safe_url(url: str) -> str:
    parts = urlsplit(url)
    safe_path = quote(unquote(parts.path), safe='/%')
    return urlunsplit((parts.scheme, parts.netloc, safe_path, parts.query, parts.fragment))


def _guess_extension(url: str, content_type: str) -> str:
    ext = Path(urlsplit(url).path).suffix.lower()
    if ext in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}:
        return ext
    guessed = mimetypes.guess_extension(content_type.split(';', 1)[0].strip()) if content_type else ''
    if guessed in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}:
        return guessed
    return '.img'


def _download_url(url: str) -> tuple[bytes, str]:
    req = Request(_safe_url(url), headers={'User-Agent': UA})
    with urlopen(req, timeout=TIMEOUT_SEC) as response:
        content_type = str(response.headers.get('Content-Type') or '').strip()
        blob = response.read()
    return blob, content_type


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8', newline='') as fp:
        return list(csv.DictReader(fp))


def _build_jobs() -> list[dict[str, str]]:
    jobs: list[dict[str, str]] = []

    for row in _read_csv(MANIFEST_DIR / 'catalog_remote_images.csv'):
        jobs.append(
            {
                'kind': 'catalog',
                'catalog_type': row['catalog_type'],
                'item_id': row['item_id'],
                'slot': 'image',
                'url': row['image_url'],
                'relative_stub': f"catalog/{row['catalog_type']}/{row['item_id']}",
            }
        )

    for row in _read_csv(MANIFEST_DIR / 'catalog_variation_remote_images.csv'):
        jobs.append(
            {
                'kind': 'variation',
                'catalog_type': row['catalog_type'],
                'item_id': row['item_id'],
                'variation_id': row['variation_id'],
                'slot': 'image',
                'url': row['image_url'],
                'relative_stub': (
                    f"variations/{row['catalog_type']}/{row['item_id']}/{row['variation_id']}"
                ),
            }
        )

    villager_rows = _read_csv(MANIFEST_DIR / 'villager_remote_images.csv')
    villager_slots = {
        'image_url': 'images',
        'icon_url': 'icons',
        'photo_url': 'photos',
        'house_exterior_url': 'house_exteriors',
        'house_interior_url': 'house_interiors',
    }
    for row in villager_rows:
        villager_id = row['villager_id']
        for key, folder in villager_slots.items():
            url = row.get(key, '').strip()
            if not url:
                continue
            jobs.append(
                {
                    'kind': 'villager',
                    'villager_id': villager_id,
                    'slot': key,
                    'url': url,
                    'relative_stub': f'villagers/{folder}/{villager_id}',
                }
            )

    return jobs


def main() -> int:
    if not MANIFEST_DIR.exists():
        raise SystemExit(f'missing manifest dir: {MANIFEST_DIR}')

    jobs = _build_jobs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    URL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    unique_urls = sorted({job['url'] for job in jobs if job['url']})
    url_results: dict[str, dict[str, str]] = {}
    result_lock = Lock()

    def worker(url: str) -> tuple[str, dict[str, str]]:
        sha = hashlib.sha256(url.encode('utf-8')).hexdigest()

        for candidate in URL_CACHE_DIR.glob(f'{sha}.*'):
            if candidate.is_file() and candidate.stat().st_size >= MIN_VALID_BYTES:
                return url, {
                    'status': 'cached',
                    'cache_path': str(candidate.relative_to(BASE_DIR)),
                    'size': str(candidate.stat().st_size),
                }

        try:
            blob, content_type = _download_url(url)
            if len(blob) < MIN_VALID_BYTES:
                return url, {
                    'status': 'too_small',
                    'error': f'bytes:{len(blob)}',
                }
            ext = _guess_extension(url, content_type)
            cache_path = URL_CACHE_DIR / f'{sha}{ext}'
            cache_path.write_bytes(blob)
            return url, {
                'status': 'downloaded',
                'cache_path': str(cache_path.relative_to(BASE_DIR)),
                'size': str(len(blob)),
                'content_type': content_type,
            }
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            return url, {
                'status': 'error',
                'error': str(exc),
            }

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(worker, url): url for url in unique_urls}
        for future in as_completed(future_map):
            url, result = future.result()
            with result_lock:
                url_results[url] = result

    mapping_rows: list[dict[str, str]] = []
    for job in jobs:
        url = job['url']
        result = url_results.get(url, {'status': 'missing_result'})
        mapping: dict[str, str] = {
            'kind': job['kind'],
            'url': url,
            'status': result['status'],
        }
        for key, value in job.items():
            if key not in {'url', 'relative_stub'}:
                mapping[key] = value

        if result.get('cache_path'):
            cache_path = BASE_DIR / result['cache_path']
            ext = cache_path.suffix
            relative_path = f"{job['relative_stub']}{ext}"
            target = OUT_DIR / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(cache_path, target)
            mapping['local_path'] = str(target.relative_to(BASE_DIR))
        if result.get('error'):
            mapping['error'] = result['error']
        mapping_rows.append(mapping)

    URL_MAP_PATH.write_text(
        json.dumps(
            {
                'generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
                'base_dir': str(BASE_DIR),
                'offline_root': str(OUT_DIR.relative_to(BASE_DIR)),
                'mappings': mapping_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )

    status_counter = {}
    for item in mapping_rows:
        status_counter[item['status']] = status_counter.get(item['status'], 0) + 1

    DOWNLOAD_REPORT_PATH.write_text(
        json.dumps(
            {
                'job_count': len(jobs),
                'unique_url_count': len(unique_urls),
                'status_counter': status_counter,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )

    print(f'jobs={len(jobs)} unique_urls={len(unique_urls)}')
    for key in sorted(status_counter):
        print(f'{key}={status_counter[key]}')
    print(f'url_map={URL_MAP_PATH}')
    print(f'report={DOWNLOAD_REPORT_PATH}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
