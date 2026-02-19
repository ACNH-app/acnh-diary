from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from app.schemas.state import (
    CatalogStateBulkIn,
    CatalogStateIn,
    CatalogStateOut,
    CatalogVariationStateBatchIn,
    CatalogVariationStateIn,
    CatalogVariationStateOut,
)


def create_catalog_router(
    *,
    get_catalog_meta_handler: Callable[..., dict[str, Any]],
    get_catalog_handler: Callable[..., dict[str, Any]],
    get_catalog_detail_handler: Callable[..., dict[str, Any]],
    get_art_guide_handler: Callable[..., dict[str, Any]],
    update_catalog_state_handler: Callable[..., CatalogStateOut],
    update_catalog_state_bulk_handler: Callable[..., dict[str, Any]],
    update_catalog_variation_state_handler: Callable[..., CatalogVariationStateOut],
    update_catalog_variation_state_batch_handler: Callable[..., dict[str, Any]],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/catalog/{catalog_type}/meta")
    def get_catalog_meta(catalog_type: str) -> dict[str, Any]:
        return get_catalog_meta_handler(catalog_type=catalog_type)

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
    ) -> dict[str, Any]:
        return get_catalog_handler(
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
    def get_catalog_detail(catalog_type: str, item_id: str) -> dict[str, Any]:
        return get_catalog_detail_handler(catalog_type=catalog_type, item_id=item_id)

    @router.get("/api/catalog/art/guide")
    def get_art_guide() -> dict[str, Any]:
        return get_art_guide_handler()

    @router.post("/api/catalog/{catalog_type}/{item_id}/state", response_model=CatalogStateOut)
    def update_catalog_state(
        catalog_type: str, item_id: str, payload: CatalogStateIn
    ) -> CatalogStateOut:
        return update_catalog_state_handler(
            catalog_type=catalog_type, item_id=item_id, payload=payload
        )

    @router.post("/api/catalog/{catalog_type}/state/bulk")
    def update_catalog_state_bulk(
        catalog_type: str,
        payload: CatalogStateBulkIn,
    ) -> dict[str, Any]:
        return update_catalog_state_bulk_handler(
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
    ) -> CatalogVariationStateOut:
        return update_catalog_variation_state_handler(
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
    ) -> dict[str, Any]:
        return update_catalog_variation_state_batch_handler(
            catalog_type=catalog_type,
            item_id=item_id,
            payload=payload,
        )

    return router
