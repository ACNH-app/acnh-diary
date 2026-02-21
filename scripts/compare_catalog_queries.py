from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.catalog_handlers import create_catalog_handlers
from app.api.deps import CatalogHandlerDeps
from app.core.config import CATALOG_TYPES
from app.core.db import get_db, init_db
from app.domain.catalog import category_ko_for, order_categories
from app.repositories.state import (
    get_catalog_variation_state_map,
    invalidate_catalog_state_caches,
    recalc_item_owned_from_variations,
    upsert_all_variation_states,
    upsert_catalog_state,
    with_catalog_state,
    with_catalog_variation_counts,
)
from app.services.catalog_data import (
    _build_variations,
    _catalog_detail_payload,
    _catalog_row_index,
    _content_db_catalog_bundle,
    _content_db_villagers,
    _fetch_single_catalog_row,
    _find_catalog_row,
    _variation_ids_for_item,
    load_catalog,
    load_villagers,
)
from app.services.mappings import load_clothing_label_theme_map, load_clothing_style_map
from app.utils.sort import sort_catalog_items


def _clear_runtime_caches() -> None:
    for fn in (
        load_catalog,
        load_villagers,
        _catalog_row_index,
        _variation_ids_for_item,
        _content_db_catalog_bundle,
        _content_db_villagers,
    ):
        try:
            fn.cache_clear()  # type: ignore[attr-defined]
        except Exception:
            pass
    invalidate_catalog_state_caches(None)


def _set_use_content_db(enabled: bool) -> None:
    os.environ["USE_CONTENT_DB"] = "1" if enabled else "0"
    _clear_runtime_caches()


def _build_handlers() -> Any:
    deps = CatalogHandlerDeps(
        catalog_types=CATALOG_TYPES,
        load_catalog=load_catalog,
        order_categories=order_categories,
        category_ko_for=category_ko_for,
        load_clothing_style_map=load_clothing_style_map,
        load_clothing_label_theme_map=load_clothing_label_theme_map,
        with_catalog_state=with_catalog_state,
        with_catalog_variation_counts=with_catalog_variation_counts,
        sort_catalog_items=sort_catalog_items,
        find_catalog_row=_find_catalog_row,
        build_variations=_build_variations,
        fetch_single_catalog_row=_fetch_single_catalog_row,
        get_catalog_variation_state_map=get_catalog_variation_state_map,
        catalog_detail_payload=_catalog_detail_payload,
        variation_ids_for_item=_variation_ids_for_item,
        upsert_catalog_state=upsert_catalog_state,
        upsert_all_variation_states=upsert_all_variation_states,
        recalc_item_owned_from_variations=recalc_item_owned_from_variations,
        invalidate_catalog_state_caches=invalidate_catalog_state_caches,
        init_db=init_db,
        get_db=get_db,
    )
    return create_catalog_handlers(deps)


def _collect_all_ids(handlers: Any, catalog_type: str, **kwargs: Any) -> tuple[int, list[str]]:
    page = 1
    page_size = 200
    all_ids: list[str] = []
    total_count = 0
    while True:
        resp = handlers.get_catalog(
            catalog_type=catalog_type, page=page, page_size=page_size, **kwargs
        )
        if page == 1:
            total_count = int(resp.get("total_count") or resp.get("count") or 0)
        items = resp.get("items") or []
        all_ids.extend([str(x.get("id") or "") for x in items])
        if not bool(resp.get("has_more")):
            break
        page += 1
        if page > 100:
            break
    return total_count, all_ids


@dataclass
class QueryCase:
    catalog_type: str
    kwargs: dict[str, Any]


def _build_cases() -> list[QueryCase]:
    cases: list[QueryCase] = []
    for catalog_type in CATALOG_TYPES.keys():
        cases.append(QueryCase(catalog_type, {"sort_by": "name", "sort_order": "asc"}))
        cases.append(QueryCase(catalog_type, {"sort_by": "name", "sort_order": "desc"}))
        cases.append(QueryCase(catalog_type, {"sort_by": "number", "sort_order": "asc"}))

        items = load_catalog(catalog_type)
        if items:
            first = items[0]
            q_name = str(first.get("name_ko") or first.get("name_en") or "")[:2].strip()
            if q_name:
                cases.append(QueryCase(catalog_type, {"q": q_name, "sort_by": "name"}))
            category = str(first.get("category") or "").strip()
            if category:
                cases.append(QueryCase(catalog_type, {"category": category, "sort_by": "name"}))

        if catalog_type == "clothing":
            styles = sorted({s for x in items for s in x.get("styles", [])})
            if styles:
                cases.append(QueryCase(catalog_type, {"style": styles[0], "sort_by": "name"}))
            themes = sorted({t for x in items for t in x.get("label_themes", [])})
            if themes:
                cases.append(QueryCase(catalog_type, {"label_theme": themes[0], "sort_by": "name"}))
        elif catalog_type == "events":
            event_types = sorted({str(x.get("event_type") or "") for x in items if x.get("event_type")})
            if event_types:
                cases.append(QueryCase(catalog_type, {"event_type": event_types[0], "sort_by": "date"}))
            cases.append(QueryCase(catalog_type, {"sort_by": "date", "sort_order": "asc"}))
        elif catalog_type == "art":
            cases.append(QueryCase(catalog_type, {"fake_state": "has_fake", "sort_by": "name"}))
            cases.append(QueryCase(catalog_type, {"fake_state": "genuine_only", "sort_by": "name"}))
        elif catalog_type == "special_items":
            categories = sorted({str(x.get("category") or "") for x in items if x.get("category")})
            if categories:
                cases.append(QueryCase(catalog_type, {"category": categories[0], "sort_by": "name"}))
                if len(categories) > 1:
                    cases.append(QueryCase(catalog_type, {"category": categories[1], "sort_by": "name"}))
    return cases


def main() -> int:
    if not Path(ROOT / "content.db").exists():
        print("ERROR: content.db가 없습니다. 먼저 빌드하세요.")
        return 1

    _set_use_content_db(False)
    handlers_source = _build_handlers()
    cases = _build_cases()

    _set_use_content_db(True)
    handlers_db = _build_handlers()

    mismatches: list[str] = []
    for idx, case in enumerate(cases, 1):
        src_count, src_ids = _collect_all_ids(handlers_source, case.catalog_type, **case.kwargs)
        db_count, db_ids = _collect_all_ids(handlers_db, case.catalog_type, **case.kwargs)
        if src_count != db_count or src_ids != db_ids:
            mismatches.append(
                f"[{idx}] {case.catalog_type} {case.kwargs} "
                f"count(source={src_count},db={db_count}) ids_equal={src_ids == db_ids}"
            )

    print(f"cases={len(cases)}")
    if mismatches:
        print(f"mismatches={len(mismatches)}")
        for row in mismatches[:50]:
            print(row)
        return 2
    print("mismatches=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
