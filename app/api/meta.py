from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter
from fastapi.responses import FileResponse


def create_meta_router(
    *,
    home_handler: Callable[[], FileResponse],
    nav_handler: Callable[[], dict[str, Any]],
    villager_meta_handler: Callable[[], dict[str, Any]],
) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    def home() -> FileResponse:
        return home_handler()

    @router.get("/api/nav")
    def get_nav() -> dict[str, Any]:
        return nav_handler()

    @router.get("/api/meta")
    def get_villager_meta() -> dict[str, Any]:
        return villager_meta_handler()

    return router
