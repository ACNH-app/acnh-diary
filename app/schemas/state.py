from __future__ import annotations

from pydantic import BaseModel


class VillagerStateIn(BaseModel):
    liked: bool | None = None
    on_island: bool | None = None
    camping_visited: bool | None = None
    former_resident: bool | None = None


class VillagerStateOut(BaseModel):
    villager_id: str
    liked: bool
    on_island: bool
    camping_visited: bool
    former_resident: bool


class VillagerIslandOrderIn(BaseModel):
    villager_ids: list[str]


class CatalogStateIn(BaseModel):
    owned: bool | None = None
    donated: bool | None = None
    quantity: int | None = None


class CatalogStateOut(BaseModel):
    catalog_type: str
    item_id: str
    owned: bool
    donated: bool
    quantity: int


class CatalogStateBulkIn(BaseModel):
    item_ids: list[str]
    owned: bool


class CatalogVariationStateIn(BaseModel):
    owned: bool | None = None
    quantity: int | None = None


class CatalogVariationStateOut(BaseModel):
    catalog_type: str
    item_id: str
    variation_id: str
    owned: bool
    quantity: int


class CatalogVariationStateBatchItem(BaseModel):
    variation_id: str
    owned: bool
    quantity: int | None = None


class CatalogVariationStateBatchIn(BaseModel):
    items: list[CatalogVariationStateBatchItem]


class IslandProfileIn(BaseModel):
    island_name: str = ""
    nickname: str = ""
    representative_fruit: str = ""
    representative_flower: str = ""
    birthday: str = ""
    hemisphere: str = "north"
    time_travel_enabled: bool = False
    game_datetime: str = ""


class IslandProfileOut(BaseModel):
    island_name: str
    nickname: str
    representative_fruit: str
    representative_flower: str
    birthday: str
    hemisphere: str
    time_travel_enabled: bool
    game_datetime: str


class CalendarEntryIn(BaseModel):
    id: int | None = None
    visit_date: str
    npc_name: str
    note: str = ""
    checked: bool = False


class CalendarEntryOut(BaseModel):
    id: int
    visit_date: str
    npc_name: str
    note: str
    checked: bool


class CalendarCheckedIn(BaseModel):
    checked: bool


class PlayerIn(BaseModel):
    id: int | None = None
    name: str
    birthday: str = ""
    is_main: bool = False
    is_sub: bool = False


class PlayerOut(BaseModel):
    id: int
    name: str
    birthday: str
    is_main: bool
    is_sub: bool
