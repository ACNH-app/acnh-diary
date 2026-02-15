from __future__ import annotations

import hashlib
import json
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import BASE_DIR, CATALOG_TYPES, NOOKIPEDIA_BASE_URL, get_api_key

CACHE_DIR = BASE_DIR / "data" / ".cache" / "nookipedia"
DEFAULT_CACHE_TTL_SEC = 60 * 60 * 24  # 24h


def _cache_ttl_sec() -> int:
    raw = os.environ.get("NOOKIPEDIA_CACHE_TTL_SEC", str(DEFAULT_CACHE_TTL_SEC)).strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return DEFAULT_CACHE_TTL_SEC


def _cache_path(path: str, params: dict[str, Any] | None) -> Path:
    key_source = json.dumps(
        {"path": path, "params": params or {}},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(key_source).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def _load_cached(path: str, params: dict[str, Any] | None) -> Any | None:
    ttl = _cache_ttl_sec()
    if ttl <= 0:
        return None
    cache_file = _cache_path(path, params)
    if not cache_file.exists():
        return None
    try:
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return None
    fetched_at = float(payload.get("fetched_at") or 0)
    if time.time() - fetched_at > ttl:
        return None
    return payload.get("data")


def _save_cache(path: str, params: dict[str, Any] | None, data: Any) -> None:
    cache_file = _cache_path(path, params)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(
        json.dumps({"fetched_at": time.time(), "data": data}, ensure_ascii=False),
        encoding="utf-8",
    )


def fetch_nookipedia(path: str, params: dict[str, Any] | None = None) -> Any:
    cached = _load_cached(path, params)
    if cached is not None:
        return cached

    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("Nookipedia API 키가 없습니다.")

    qs = f"?{urlencode(params, doseq=True)}" if params else ""
    req = Request(
        f"{NOOKIPEDIA_BASE_URL}{path}{qs}",
        headers={"X-API-KEY": api_key},
    )

    with urlopen(req, timeout=30) as res:
        data = json.loads(res.read().decode("utf-8"))
    _save_cache(path, params, data)
    return data


@lru_cache(maxsize=1)
def load_nookipedia_villagers() -> list[dict[str, Any]]:
    return fetch_nookipedia("/villagers", {"game": "nh", "nhdetails": "true"})


@lru_cache(maxsize=None)
def load_nookipedia_catalog(catalog_type: str) -> list[dict[str, Any]]:
    cfg = CATALOG_TYPES[catalog_type]
    return fetch_nookipedia(cfg["nook_path"])
