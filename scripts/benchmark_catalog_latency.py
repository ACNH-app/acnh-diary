from __future__ import annotations

import os
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

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


@dataclass
class BenchCase:
    name: str
    fn: Callable[[], Any]


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * 0.95))
    return ordered[max(0, min(idx, len(ordered) - 1))]


def _timeit(fn: Callable[[], Any], repeats: int = 5) -> list[float]:
    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    return samples


def _build_cases(handlers: Any) -> list[BenchCase]:
    cases: list[BenchCase] = [
        BenchCase(
            name="catalog:recipes:list",
            fn=lambda: handlers.get_catalog(
                catalog_type="recipes",
                page=1,
                page_size=60,
                sort_by="number",
                sort_order="asc",
            ),
        ),
        BenchCase(
            name="catalog:furniture:list",
            fn=lambda: handlers.get_catalog(
                catalog_type="furniture",
                page=1,
                page_size=60,
                sort_by="name",
                sort_order="asc",
            ),
        ),
        BenchCase(
            name="catalog:clothing:list",
            fn=lambda: handlers.get_catalog(
                catalog_type="clothing",
                page=1,
                page_size=60,
                sort_by="name",
                sort_order="asc",
            ),
        ),
        BenchCase(
            name="catalog:special_items:list",
            fn=lambda: handlers.get_catalog(
                catalog_type="special_items",
                page=1,
                page_size=60,
                sort_by="name",
                sort_order="asc",
            ),
        ),
        BenchCase(
            name="catalog:recipes:owned_false",
            fn=lambda: handlers.get_catalog(
                catalog_type="recipes",
                page=1,
                page_size=60,
                owned=False,
                sort_by="number",
                sort_order="asc",
            ),
        ),
    ]

    for ctype in ("furniture", "clothing", "recipes", "art"):
        items = load_catalog(ctype)
        if not items:
            continue
        sample_id = str(items[0].get("id") or "")
        if not sample_id:
            continue
        cases.append(
            BenchCase(
                name=f"catalog:{ctype}:detail",
                fn=lambda ct=ctype, iid=sample_id: handlers.get_catalog_detail(ct, iid),
            )
        )
    return cases


def run_mode(enabled: bool) -> tuple[str, list[tuple[str, float, float]]]:
    mode = "content_db" if enabled else "source_loader"
    _set_use_content_db(enabled)
    handlers = _build_handlers()
    cases = _build_cases(handlers)
    rows: list[tuple[str, float, float]] = []
    for case in cases:
        samples = _timeit(case.fn, repeats=5)
        rows.append((case.name, statistics.mean(samples), _p95(samples)))
    return mode, rows


def main() -> int:
    results: list[tuple[str, list[tuple[str, float, float]]]] = []

    # source_loader는 로컬 캐시/데이터 상황에 따라 실패할 수 있어 best-effort로 측정한다.
    try:
        results.append(run_mode(False))
    except Exception as exc:
        print(f"[WARN] source_loader 벤치마크 생략: {exc}")

    results.append(run_mode(True))

    for mode, rows in results:
        print(f"\n== {mode} ==")
        for name, avg_ms, p95_ms in rows:
            print(f"{name:32} avg={avg_ms:8.2f}ms p95={p95_ms:8.2f}ms")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
