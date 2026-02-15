from __future__ import annotations

from typing import Any

from fastapi.responses import FileResponse

from app.api.deps import MetaHandlerDeps, MetaHandlers


def create_meta_handlers(deps: MetaHandlerDeps) -> MetaHandlers:
    def home() -> FileResponse:
        return FileResponse(deps.base_dir / "static" / "index.html")

    def get_nav() -> dict[str, Any]:
        return {
            "modes": [
                {"key": "villagers", "label": "주민"},
                *[
                    {"key": key, "label": cfg["label"]}
                    for key, cfg in deps.catalog_types.items()
                ],
            ]
        }

    def get_villager_meta() -> dict[str, Any]:
        villagers = deps.load_villagers()
        personality_map = deps.load_personality_map()
        species_map = deps.load_species_map()
        personalities = sorted({v["personality"] for v in villagers})
        species = sorted({v["species"] for v in villagers})
        return {
            "personalities": [
                {"en": p, "ko": personality_map.get(p, p)} for p in personalities
            ],
            "species": [{"en": s, "ko": species_map.get(s, s)} for s in species],
        }

    return MetaHandlers(
        home=home,
        get_nav=get_nav,
        get_villager_meta=get_villager_meta,
    )
