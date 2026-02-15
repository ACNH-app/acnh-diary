from __future__ import annotations

from pydantic import BaseModel


class VillagerStateIn(BaseModel):
    liked: bool | None = None
    on_island: bool | None = None
    former_resident: bool | None = None


class VillagerStateOut(BaseModel):
    villager_id: str
    liked: bool
    on_island: bool
    former_resident: bool


class CatalogStateIn(BaseModel):
    owned: bool | None = None


class CatalogStateOut(BaseModel):
    catalog_type: str
    item_id: str
    owned: bool


class CatalogVariationStateIn(BaseModel):
    owned: bool | None = None


class CatalogVariationStateOut(BaseModel):
    catalog_type: str
    item_id: str
    variation_id: str
    owned: bool


class CatalogVariationStateBatchItem(BaseModel):
    variation_id: str
    owned: bool


class CatalogVariationStateBatchIn(BaseModel):
    items: list[CatalogVariationStateBatchItem]
