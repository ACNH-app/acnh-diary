from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Header, HTTPException

from app.schemas.state import (
    CatalogStateBulkIn,
    CatalogStateIn,
    CatalogStateOut,
    CatalogVariationStateBatchIn,
    CatalogVariationStateIn,
    CatalogVariationStateOut,
)


def _resolve_island_id(x_island_id: str | None) -> int:
    text = str(x_island_id or "").strip()
    if not text:
        return 1
    try:
        island_id = int(text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid island id") from exc
    if island_id <= 0:
        raise HTTPException(status_code=400, detail="invalid island id")
    return island_id


def create_catalog_router(
    *,
    get_catalog_meta_handler: Callable[..., dict[str, Any]],
    get_recipe_tags_handler: Callable[..., dict[str, Any]],
    get_catalog_handler: Callable[..., dict[str, Any]],
    get_catalog_detail_handler: Callable[..., dict[str, Any]],
    update_catalog_state_handler: Callable[..., CatalogStateOut],
    update_catalog_state_bulk_handler: Callable[..., dict[str, Any]],
    update_catalog_variation_state_handler: Callable[..., CatalogVariationStateOut],
    update_catalog_variation_state_batch_handler: Callable[..., dict[str, Any]],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/catalog/{catalog_type}/meta")
    def get_catalog_meta(catalog_type: str) -> dict[str, Any]:
        return get_catalog_meta_handler(catalog_type=catalog_type)

    @router.get("/api/catalog/{catalog_type}/tags")
    def get_recipe_tags(catalog_type: str) -> dict[str, Any]:
        return get_recipe_tags_handler(catalog_type=catalog_type)

    @router.get("/api/catalog/{catalog_type}")
    def get_catalog(
        catalog_type: str,
        q: str = "",
        category: str = "",
        style: str = "",
        label_theme: str = "",
        event_type: str = "",
        fake_state: str = "",
        owned: bool | None = None,
        variation_scope: str = "",
        sort_by: str = "name",
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 60,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return get_catalog_handler(
            island_id=_resolve_island_id(x_island_id),
            catalog_type=catalog_type,
            q=q,
            category=category,
            style=style,
            label_theme=label_theme,
            event_type=event_type,
            fake_state=fake_state,
            owned=owned,
            variation_scope=variation_scope,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )

    @router.get("/api/catalog/{catalog_type}/{item_id}/detail")
    def get_catalog_detail(
        catalog_type: str,
        item_id: str,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return get_catalog_detail_handler(
            island_id=_resolve_island_id(x_island_id),
            catalog_type=catalog_type,
            item_id=item_id,
        )

    @router.post("/api/catalog/{catalog_type}/{item_id}/state", response_model=CatalogStateOut)
    def update_catalog_state(
        catalog_type: str,
        item_id: str,
        payload: CatalogStateIn,
        x_island_id: str | None = Header(default=None),
    ) -> CatalogStateOut:
        return update_catalog_state_handler(
            island_id=_resolve_island_id(x_island_id),
            catalog_type=catalog_type,
            item_id=item_id,
            payload=payload,
        )

    @router.post("/api/catalog/{catalog_type}/state/bulk")
    def update_catalog_state_bulk(
        catalog_type: str,
        payload: CatalogStateBulkIn,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return update_catalog_state_bulk_handler(
            island_id=_resolve_island_id(x_island_id),
            catalog_type=catalog_type,
            payload=payload,
        )

    @router.post(
        "/api/catalog/{catalog_type}/{item_id}/variations/{variation_id}/state",
        response_model=CatalogVariationStateOut,
    )
    def update_catalog_variation_state(
        catalog_type: str,
        item_id: str,
        variation_id: str,
        payload: CatalogVariationStateIn,
        x_island_id: str | None = Header(default=None),
    ) -> CatalogVariationStateOut:
        return update_catalog_variation_state_handler(
            island_id=_resolve_island_id(x_island_id),
            catalog_type=catalog_type,
            item_id=item_id,
            variation_id=variation_id,
            payload=payload,
        )

    @router.post("/api/catalog/{catalog_type}/{item_id}/variations/state")
    def update_catalog_variation_state_batch(
        catalog_type: str,
        item_id: str,
        payload: CatalogVariationStateBatchIn,
        x_island_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return update_catalog_variation_state_batch_handler(
            island_id=_resolve_island_id(x_island_id),
            catalog_type=catalog_type,
            item_id=item_id,
            payload=payload,
        )

    return router
