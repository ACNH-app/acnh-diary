from __future__ import annotations

import json
import mimetypes
from pathlib import Path
import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from threading import Lock
import time
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.config import (
    BASE_DIR,
    get_supabase_asset_bucket,
    get_supabase_asset_prefix,
    get_supabase_service_role_key,
    get_supabase_url,
)
ASSET_ROOTS: tuple[tuple[Path, str], ...] = (
    (BASE_DIR / "static" / "assets" / "music", "music"),
    (BASE_DIR / "static" / "assets" / "offline" / "_url_cache", "remote-cache"),
    (BASE_DIR / "static" / "assets" / "offline" / "catalog", "catalog"),
    (BASE_DIR / "static" / "assets" / "offline" / "variations", "variations"),
    (BASE_DIR / "static" / "assets" / "offline" / "villagers", "villagers"),
    (BASE_DIR / "villagers", "villagers/raw"),
)
PROGRESS_PATH = BASE_DIR / "tmp" / "supabase_asset_upload_progress.json"
FAILED_PATH = BASE_DIR / "tmp" / "supabase_asset_upload_failed.json"
MAX_WORKERS = 8
MAX_RETRIES = 4


def _iter_files() -> list[tuple[Path, str]]:
    out: list[tuple[Path, str]] = []
    for local_root, remote_prefix in ASSET_ROOTS:
        if not local_root.exists():
            continue
        for path in local_root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(local_root).as_posix()
            out.append((path, f"{remote_prefix}/{rel}"))
    out.sort(key=lambda item: item[1])
    return out


def _load_progress() -> set[str]:
    if not PROGRESS_PATH.exists():
        return set()
    try:
        payload = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return set()
    items = payload.get("uploaded") if isinstance(payload, dict) else []
    if not isinstance(items, list):
        return set()
    return {str(x) for x in items if str(x).strip()}


def _save_progress(uploaded: set[str]) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text(
        json.dumps({"uploaded": sorted(uploaded)}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_failed() -> dict[str, str]:
    if not FAILED_PATH.exists():
        return {}
    try:
        payload = json.loads(FAILED_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    items = payload.get("failed") if isinstance(payload, dict) else {}
    if not isinstance(items, dict):
        return {}
    return {str(k): str(v) for k, v in items.items()}


def _save_failed(failed: dict[str, str]) -> None:
    FAILED_PATH.parent.mkdir(parents=True, exist_ok=True)
    FAILED_PATH.write_text(
        json.dumps({"failed": failed}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _storage_object_url(object_key: str) -> str:
    base = get_supabase_url().rstrip("/")
    bucket = quote(get_supabase_asset_bucket().strip("/"), safe="")
    prefix = get_supabase_asset_prefix().strip("/")
    key = f"{prefix}/{object_key}" if prefix else object_key
    return f"{base}/storage/v1/object/{bucket}/{quote(key, safe='/')}"


def _upload_file(local_path: Path, object_key: str) -> None:
    service_key = get_supabase_service_role_key()
    if not service_key:
        raise SystemExit("SUPABASE_SERVICE_ROLE_KEY is required")
    content_type = mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"
    body = local_path.read_bytes()
    last_error = ""
    for attempt in range(1, MAX_RETRIES + 1):
        req = Request(
            _storage_object_url(object_key),
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {service_key}",
                "apikey": service_key,
                "x-upsert": "true",
                "Content-Type": content_type,
            },
        )
        try:
            with urlopen(req, timeout=120):
                return
        except HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            last_error = f"{exc.code} {payload}"
            if exc.code not in {408, 429, 500, 502, 503, 504} or attempt >= MAX_RETRIES:
                raise RuntimeError(f"upload failed for {object_key}: {last_error}") from exc
        except Exception as exc:
            last_error = str(exc)
            if attempt >= MAX_RETRIES:
                raise RuntimeError(f"upload failed for {object_key}: {last_error}") from exc
        time.sleep(min(2 * attempt, 8))


def main() -> None:
    files = _iter_files()
    if not files:
        raise SystemExit("no asset files found to upload")
    uploaded = _load_progress()
    pending = [(local_path, object_key) for local_path, object_key in files if object_key not in uploaded]
    progress_lock = Lock()
    failed = _load_failed()
    print(f"bucket={get_supabase_asset_bucket()}")
    print(f"prefix={get_supabase_asset_prefix() or '(none)'}")
    print(f"files={len(files)}")
    print(f"already_uploaded={len(uploaded)}")
    print(f"pending={len(pending)}")
    print(f"failed_recorded={len(failed)}")
    if not pending:
        print("nothing to upload")
        return

    done_count = len(uploaded)

    def worker(local_path: Path, object_key: str) -> str:
        _upload_file(local_path, object_key)
        return object_key

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(worker, local_path, object_key): object_key
            for local_path, object_key in pending[:MAX_WORKERS]
        }
        next_index = MAX_WORKERS

        while future_map:
            done, _ = wait(set(future_map.keys()), return_when=FIRST_COMPLETED)
            for future in done:
                object_key = future_map.pop(future)
                try:
                    result_key = future.result()
                except Exception as exc:
                    with progress_lock:
                        failed[object_key] = str(exc)
                        _save_failed(failed)
                    print(f"[error] {object_key} -> {exc}")
                else:
                    with progress_lock:
                        uploaded.add(result_key)
                        failed.pop(result_key, None)
                        done_count = len(uploaded)
                        _save_progress(uploaded)
                        _save_failed(failed)
                    print(f"[{done_count}/{len(files)}] uploaded {object_key}")

                if next_index < len(pending):
                    local_path, next_object_key = pending[next_index]
                    future_map[executor.submit(worker, local_path, next_object_key)] = next_object_key
                    next_index += 1

    print(f"uploaded_total={len(uploaded)}")
    print(f"remaining={len(files) - len(uploaded)}")
    print(f"failed_total={len(failed)}")


if __name__ == "__main__":
    main()
