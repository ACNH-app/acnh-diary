from __future__ import annotations

import json
from functools import lru_cache
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import (
    get_supabase_anon_key,
    get_supabase_service_role_key,
    get_supabase_url,
)

_PAGE_SIZE = 1000


def _rest_base_url() -> str:
    base = get_supabase_url().rstrip("/")
    return f"{base}/rest/v1" if base else ""


def is_supabase_content_available() -> bool:
    return bool(_rest_base_url() and _auth_key())


def _auth_key() -> str:
    return get_supabase_service_role_key().strip() or get_supabase_anon_key().strip()


def _headers() -> dict[str, str]:
    key = _auth_key()
    if not key:
        return {}
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }


def _decode_payload(raw: bytes) -> Any:
    text = raw.decode("utf-8").strip()
    if not text:
        return []
    return json.loads(text)


def _request_json(path: str, query: dict[str, Any]) -> list[dict[str, Any]]:
    base = _rest_base_url()
    headers = _headers()
    if not base or not headers:
        return []
    url = f"{base}/{path}?{urlencode(query, doseq=True)}"
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=30) as response:
            payload = _decode_payload(response.read())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []
    return payload if isinstance(payload, list) else []


def fetch_rows(
    table: str,
    select: str = "*",
    *,
    filters: dict[str, str] | None = None,
    order: str | None = None,
) -> list[dict[str, Any]]:
    if not table:
        return []
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        query: dict[str, Any] = {
            "select": select,
            "limit": str(_PAGE_SIZE),
            "offset": str(offset),
        }
        if filters:
            query.update(filters)
        if order:
            query["order"] = order
        batch = _request_json(table, query)
        if not batch:
            break
        rows.extend(row for row in batch if isinstance(row, dict))
        if len(batch) < _PAGE_SIZE:
            break
        offset += _PAGE_SIZE
    return rows


@lru_cache(maxsize=None)
def fetch_catalog_items(catalog_type: str) -> list[dict[str, Any]]:
    return fetch_rows(
        "catalog_items",
        "item_id,item_json,raw_json,source,source_ko,source_notes,source_notes_ko",
        filters={"catalog_type": f"eq.{catalog_type}"},
        order="item_id.asc",
    )


@lru_cache(maxsize=1)
def fetch_recipe_tag_links() -> list[dict[str, Any]]:
    return fetch_rows(
        "recipe_tag_links",
        "recipe_item_id,tag_key",
        order="recipe_item_id.asc,tag_key.asc",
    )


@lru_cache(maxsize=1)
def fetch_recipe_tags() -> list[dict[str, Any]]:
    return fetch_rows(
        "recipe_tags",
        "tag_key,tag_type,name_ko,name_en,sort_order",
        order="sort_order.asc,tag_key.asc",
    )


@lru_cache(maxsize=1)
def fetch_villagers() -> list[dict[str, Any]]:
    return fetch_rows(
        "villagers",
        "raw_json",
        order="villager_id.asc",
    )


@lru_cache(maxsize=None)
def fetch_catalog_variations(catalog_type: str, item_id: str) -> list[dict[str, Any]]:
    return fetch_rows(
        "catalog_variations",
        "variation_id,raw_json,label,image_url,color1,color2,pattern,source,source_ko,source_notes,source_notes_ko,price",
        filters={
            "catalog_type": f"eq.{catalog_type}",
            "item_id": f"eq.{item_id}",
        },
        order="variation_id.asc",
    )
