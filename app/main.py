from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.catalog import create_catalog_router
from app.api.deps import AppHandlerDeps, CatalogHandlerDeps, MetaHandlerDeps, VillagerHandlerDeps
from app.api.handlers import create_handlers
from app.api.meta import create_meta_router
from app.api.villagers import create_villager_router
from app.core.config import (
    BASE_DIR,
    CATALOG_TYPES,
    CLOTHING_CATEGORY_MAP_PATH,
    CLOTHING_LABEL_THEME_MAP_PATH,
    CLOTHING_NAME_MAP_PATH,
    CLOTHING_STYLE_MAP_PATH,
    DEFAULT_CLOTHING_CATEGORY_MAP,
    DEFAULT_CLOTHING_LABEL_THEME_MAP,
    DEFAULT_CLOTHING_STYLE_MAP,
    DEFAULT_PERSONALITY_MAP,
    DEFAULT_SPECIES_MAP,
    EVENT_NAME_MAP_PATH,
    FOSSIL_NAME_MAP_PATH,
    FURNITURE_NAME_MAP_PATH,
    GYROID_NAME_MAP_PATH,
    INTERIOR_NAME_MAP_PATH,
    ITEMS_NAME_MAP_PATH,
    NAME_MAP_PATH,
    PERSONALITY_MAP_PATH,
    SPECIES_MAP_PATH,
    TOOLS_NAME_MAP_PATH,
    get_api_key,
    get_cors_origins,
)
from app.core.db import get_db, init_db
from app.domain.catalog import category_ko_for, order_categories
from app.repositories.state import (
    get_catalog_variation_state_map,
    recalc_item_owned_from_variations,
    upsert_all_variation_states,
    upsert_catalog_state,
    with_catalog_state,
    with_catalog_variation_counts,
    with_villager_state,
)
from app.services.catalog_data import (
    _build_variations,
    _catalog_detail_payload,
    _fetch_single_catalog_row,
    _find_catalog_row,
    _variation_ids_for_item,
    load_catalog,
    load_villagers,
)
from app.services.mappings import (
    build_local_name_maps,
    ensure_map_file,
    load_catalog_name_maps,
    load_clothing_category_map,
    load_clothing_label_theme_map,
    load_clothing_style_map,
    load_korean_name_map,
    load_personality_map,
    load_species_map,
)
from app.utils.sort import sort_catalog_items


def _should_prewarm_on_startup() -> bool:
    raw = os.environ.get("PREWARM_ON_STARTUP", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


app = FastAPI(title="ACNH Manager Prototype", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.on_event("startup")
def on_startup() -> None:
    ensure_map_file(NAME_MAP_PATH, {})
    ensure_map_file(PERSONALITY_MAP_PATH, DEFAULT_PERSONALITY_MAP)
    ensure_map_file(SPECIES_MAP_PATH, DEFAULT_SPECIES_MAP)

    ensure_map_file(CLOTHING_NAME_MAP_PATH, {})
    ensure_map_file(CLOTHING_CATEGORY_MAP_PATH, DEFAULT_CLOTHING_CATEGORY_MAP)
    ensure_map_file(CLOTHING_STYLE_MAP_PATH, DEFAULT_CLOTHING_STYLE_MAP)
    ensure_map_file(CLOTHING_LABEL_THEME_MAP_PATH, DEFAULT_CLOTHING_LABEL_THEME_MAP)

    ensure_map_file(FURNITURE_NAME_MAP_PATH, {})
    ensure_map_file(ITEMS_NAME_MAP_PATH, {})
    ensure_map_file(TOOLS_NAME_MAP_PATH, {})
    ensure_map_file(INTERIOR_NAME_MAP_PATH, {})
    ensure_map_file(GYROID_NAME_MAP_PATH, {})
    ensure_map_file(FOSSIL_NAME_MAP_PATH, {})
    ensure_map_file(EVENT_NAME_MAP_PATH, {})
    build_local_name_maps()

    if not get_api_key():
        raise RuntimeError("NOOKIPEDIA_API_KEY 환경변수를 설정하세요.")

    init_db()
    load_korean_name_map()
    load_personality_map()
    load_species_map()
    load_catalog_name_maps()
    load_clothing_category_map()
    load_clothing_style_map()
    load_clothing_label_theme_map()

    # 첫 요청 지연을 줄이기 위해 목록 데이터를 메모리 캐시에 미리 적재한다.
    # (시작 시간은 늘어나지만, 첫 API 호출은 빨라짐)
    if _should_prewarm_on_startup():
        try:
            load_villagers()
            for catalog_type in CATALOG_TYPES.keys():
                load_catalog(catalog_type)
        except Exception:
            # 프리워밍 실패는 앱 기동 실패로 취급하지 않는다.
            pass


handlers = create_handlers(
    AppHandlerDeps(
        meta=MetaHandlerDeps(
            base_dir=BASE_DIR,
            catalog_types=CATALOG_TYPES,
            load_villagers=load_villagers,
            load_personality_map=load_personality_map,
            load_species_map=load_species_map,
        ),
        villagers=VillagerHandlerDeps(
            load_villagers=load_villagers,
            with_villager_state=with_villager_state,
            init_db=init_db,
            get_db=get_db,
        ),
        catalog=CatalogHandlerDeps(
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
            init_db=init_db,
            get_db=get_db,
        ),
    )
)


app.include_router(
    create_meta_router(
        home_handler=handlers.meta.home,
        nav_handler=handlers.meta.get_nav,
        villager_meta_handler=handlers.meta.get_villager_meta,
    )
)
app.include_router(
    create_villager_router(
        get_villagers_handler=handlers.villagers.get_villagers,
        update_villager_state_handler=handlers.villagers.update_villager_state,
    )
)
app.include_router(
    create_catalog_router(
        get_catalog_meta_handler=handlers.catalog.get_catalog_meta,
        get_catalog_handler=handlers.catalog.get_catalog,
        get_catalog_detail_handler=handlers.catalog.get_catalog_detail,
        update_catalog_state_handler=handlers.catalog.update_catalog_state,
        update_catalog_variation_state_handler=handlers.catalog.update_catalog_variation_state,
        update_catalog_variation_state_batch_handler=handlers.catalog.update_catalog_variation_state_batch,
    )
)
