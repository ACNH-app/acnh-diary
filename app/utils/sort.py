from __future__ import annotations

import re
from typing import Any


def _script_rank(text: str) -> int:
    if not text:
        return 3
    ch = text.strip()[:1]
    if not ch:
        return 3
    if ch.isdigit():
        return 0
    code = ord(ch)
    if 0xAC00 <= code <= 0xD7A3 or 0x1100 <= code <= 0x11FF or 0x3130 <= code <= 0x318F:
        return 1
    if ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
        return 2
    return 3


def _leading_number_parts(text: str) -> tuple[int, str] | None:
    s = (text or "").strip()
    match = re.match(r"^(\d+)(.*)$", s)
    if not match:
        return None
    return int(match.group(1)), match.group(2).strip().casefold()


def sort_catalog_items(items: list[dict[str, Any]], sort_by: str, sort_order: str) -> list[dict[str, Any]]:
    direction = -1 if sort_order == "desc" else 1

    def key_name(x: dict[str, Any]) -> Any:
        text = (x.get("name_ko") or x.get("name_en") or "").strip()
        rank = _script_rank(text)
        if rank == 0:
            parsed = _leading_number_parts(text)
            if parsed:
                number_value, rest = parsed
                return (rank, number_value, rest, text.casefold())
        return (rank, 10**12, text.casefold(), "")

    def key_category(x: dict[str, Any]) -> Any:
        return (x.get("category_ko") or x.get("category") or "").lower()

    def key_date(x: dict[str, Any]) -> Any:
        return (x.get("date") or "9999-99-99").lower()

    def key_number(x: dict[str, Any]) -> Any:
        num = int(x.get("number") or 0)
        name = (x.get("name_ko") or x.get("name_en") or "").casefold()
        return (num if num > 0 else 999999, name)

    if sort_by == "category":
        return sorted(items, key=key_category, reverse=(direction < 0))
    if sort_by == "date":
        return sorted(items, key=key_date, reverse=(direction < 0))
    if sort_by == "number":
        return sorted(items, key=key_number, reverse=(direction < 0))
    return sorted(items, key=key_name, reverse=(direction < 0))
