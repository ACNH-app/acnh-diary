from __future__ import annotations

from app.api.catalog_handlers import create_catalog_handlers
from app.api.deps import AppHandlerDeps, AppHandlers
from app.api.meta_handlers import create_meta_handlers
from app.api.villager_handlers import create_villager_handlers


def create_handlers(deps: AppHandlerDeps) -> AppHandlers:
    return AppHandlers(
        meta=create_meta_handlers(deps.meta),
        villagers=create_villager_handlers(deps.villagers),
        catalog=create_catalog_handlers(deps.catalog),
    )
