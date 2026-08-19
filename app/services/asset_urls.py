from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlsplit

from app.core.config import get_supabase_asset_public_base_url, use_supabase_assets

_STATIC_PREFIX_MAP: tuple[tuple[str, str], ...] = (
    ("/static/assets/music/", "music/"),
    ("/static/assets/offline/_url_cache/", "remote-cache/"),
    ("/static/assets/offline/catalog/", "catalog/"),
    ("/static/assets/offline/variations/", "variations/"),
    ("/static/assets/offline/villagers/", "villagers/"),
    ("/villagers/", "villagers/raw/"),
)


def _join_public_base(base: str, suffix: str) -> str:
    clean_suffix = str(suffix or "").lstrip("/")
    if not base:
        return ""
    return f"{base.rstrip('/')}/{clean_suffix}" if clean_suffix else base.rstrip("/")


def _remote_cache_object_key(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    ext = Path(urlsplit(url).path).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
        ext = ".img"
    return f"remote-cache/{digest}{ext}"


def _local_asset_object_key(url: str) -> str:
    normalized = str(url or "").strip()
    for prefix, object_prefix in _STATIC_PREFIX_MAP:
        if normalized.startswith(prefix):
            suffix = normalized[len(prefix) :].lstrip("/")
            return f"{object_prefix}{suffix}"
    return ""


def resolve_public_asset_url(url: str) -> str:
    raw = str(url or "").strip()
    if not raw:
        return ""
    if raw.startswith("//"):
        raw = f"https:{raw}"
    if not use_supabase_assets():
        return raw

    public_base = get_supabase_asset_public_base_url()
    if not public_base:
        return raw

    local_key = _local_asset_object_key(raw)
    if local_key:
        return _join_public_base(public_base, local_key)

    if raw.startswith("http://") or raw.startswith("https://"):
        return _join_public_base(public_base, _remote_cache_object_key(raw))

    return raw
