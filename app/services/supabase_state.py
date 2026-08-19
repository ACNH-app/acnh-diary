from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import get_supabase_service_role_key, get_supabase_url


def is_supabase_state_available() -> bool:
    return bool(_rest_base_url() and get_supabase_service_role_key().strip())


def _rest_base_url() -> str:
    base = get_supabase_url().rstrip("/")
    return f"{base}/rest/v1" if base else ""


def _headers(*, prefer: str | None = None, extra: dict[str, str] | None = None) -> dict[str, str]:
    key = get_supabase_service_role_key().strip()
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    if extra:
        headers.update(extra)
    return headers


def _decode(response: bytes) -> Any:
    text = response.decode("utf-8").strip()
    if not text:
        return None
    return json.loads(text)


def request_json(
    method: str,
    table: str,
    *,
    query: dict[str, Any] | None = None,
    body: Any = None,
    prefer: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> Any:
    base = _rest_base_url()
    if not base:
        raise RuntimeError("supabase state base url is not configured")
    url = f"{base}/{table}"
    if query:
        url = f"{url}?{urlencode(query, doseq=True)}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(
        url,
        data=data,
        headers=_headers(prefer=prefer, extra=extra_headers),
        method=method,
    )
    try:
        with urlopen(req, timeout=30) as response:
            return _decode(response.read())
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"supabase state request failed: {exc.code} {detail}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"supabase state request failed: {exc}") from exc


def fetch_rows(
    table: str,
    *,
    select: str = "*",
    filters: dict[str, str] | None = None,
    order: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    query: dict[str, Any] = {"select": select}
    if filters:
        query.update(filters)
    if order:
        query["order"] = order
    if limit is not None:
        query["limit"] = str(limit)
    payload = request_json("GET", table, query=query)
    return payload if isinstance(payload, list) else []


def insert_row(table: str, row: dict[str, Any]) -> dict[str, Any]:
    payload = request_json("POST", table, body=row, prefer="return=representation")
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict):
            return first
    return {}


def upsert_rows(table: str, rows: list[dict[str, Any]], on_conflict: str) -> list[dict[str, Any]]:
    if not rows:
        return []
    payload = request_json(
        "POST",
        table,
        query={"on_conflict": on_conflict},
        body=rows,
        prefer="resolution=merge-duplicates,return=representation",
    )
    return payload if isinstance(payload, list) else []


def patch_rows(table: str, filters: dict[str, str], values: dict[str, Any]) -> list[dict[str, Any]]:
    payload = request_json(
        "PATCH",
        table,
        query={"select": "*", **filters},
        body=values,
        prefer="return=representation",
    )
    return payload if isinstance(payload, list) else []


def delete_rows(table: str, filters: dict[str, str]) -> list[dict[str, Any]]:
    payload = request_json(
        "DELETE",
        table,
        query={"select": "*", **filters},
        prefer="return=representation",
    )
    return payload if isinstance(payload, list) else []
