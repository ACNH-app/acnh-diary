from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.api.deps import CatalogHandlerDeps, CatalogHandlers
from app.repositories.state import (
    get_catalog_state_map,
    save_all_variation_states,
    save_catalog_state,
    save_catalog_variation_batch,
    save_catalog_variation_state,
)
from app.schemas.state import (
    CatalogStateBulkIn,
    CatalogStateIn,
    CatalogStateOut,
    CatalogVariationStateBatchIn,
    CatalogVariationStateIn,
    CatalogVariationStateOut,
)


def create_catalog_handlers(deps: CatalogHandlerDeps) -> CatalogHandlers:
    def _is_special_items_mode(catalog_type: str) -> bool:
        return catalog_type == "special_items"

    def _special_item_rows_by_id() -> dict[str, dict[str, Any]]:
        rows = deps.load_catalog("special_items")
        return {str(x.get("id") or ""): x for x in rows if str(x.get("id") or "")}

    def _resolve_state_catalog_type(catalog_type: str, item_id: str) -> str:
        if not _is_special_items_mode(catalog_type):
            return catalog_type
        item = _special_item_rows_by_id().get(item_id)
        origin = str((item or {}).get("origin_catalog_type") or "").strip()
        return origin if origin in deps.catalog_types else catalog_type

    def _merge_state_for_special_items_for_island(
        island_id: int,
        items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            origin = str(item.get("origin_catalog_type") or "").strip()
            if not origin:
                continue
            grouped.setdefault(origin, []).append(item)

        merged_by_id: dict[str, dict[str, Any]] = {}
        for origin, rows in grouped.items():
            rows_with_state = deps.with_catalog_state(island_id, origin, rows)
            rows_with_counts = deps.with_catalog_variation_counts(island_id, origin, rows_with_state)
            for row in rows_with_counts:
                row_id = str(row.get("id") or "")
                if row_id:
                    merged_by_id[row_id] = row
        return [merged_by_id.get(str(item.get("id") or ""), item) for item in items]

    def get_catalog_meta(catalog_type: str) -> dict[str, Any]:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="Catalog not found.")

        rows = deps.load_catalog(catalog_type)
        category_values = {x["category"] for x in rows if x["category"]}
        if catalog_type == "recipes":
            for row in rows:
                filters = row.get("recipe_filters")
                if isinstance(filters, list):
                    category_values.update(str(v).strip() for v in filters if str(v).strip())
        categories = deps.order_categories(catalog_type, list(category_values))
        category_rows = [{"en": c, "ko": deps.category_ko_for(catalog_type, c)} for c in categories]
        if catalog_type == "photos":
            category_rows = []

        response: dict[str, Any] = {
            "label": deps.catalog_types[catalog_type]["label"],
            "status_label": deps.catalog_types[catalog_type]["status_label"],
            "categories": category_rows,
        }
        if catalog_type == "clothing":
            style_map = deps.load_clothing_style_map()
            label_theme_map = deps.load_clothing_label_theme_map()
            styles = sorted({s for x in rows for s in x.get("styles", [])})
            label_themes = sorted({t for x in rows for t in x.get("label_themes", [])})
            response["styles"] = [{"en": s, "ko": style_map.get(s, s)} for s in styles]
            response["label_themes"] = [{"en": t, "ko": label_theme_map.get(t, t)} for t in label_themes]
        if catalog_type == "events":
            response["event_types"] = sorted({x["event_type"] for x in rows if x["event_type"]})
        if catalog_type == "art":
            response["authenticity_types"] = [
                {"en": "genuine_only", "ko": "진품만"},
                {"en": "has_fake", "ko": "가품 있음"},
            ]
        return response

    def get_recipe_tags(catalog_type: str) -> dict[str, Any]:
        if catalog_type != "recipes":
            raise HTTPException(status_code=404, detail="Recipe tags are only available for recipes.")
        rows = deps.load_recipe_tags() or []
        return {"count": len(rows), "items": rows}

    def get_catalog(
        island_id: int,
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
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="Catalog not found.")

        page = max(1, int(page or 1))
        page_size = max(1, min(200, int(page_size or 60)))
        items = deps.load_catalog(catalog_type)

        q_norm = q.strip().lower()
        if q_norm:
            items = [
                x
                for x in items
                if q_norm in x["name"].lower()
                or q_norm in x["name_ko"].lower()
                or q_norm in x["name_en"].lower()
                or q_norm in str(x.get("source") or "").lower()
                or q_norm in str(x.get("source_notes") or "").lower()
            ]
        if category:
            if catalog_type == "recipes" and category.startswith(("season:", "event:", "npc:", "ingredient:")):
                items = [x for x in items if category in (x.get("recipe_filters") or [])]
            else:
                items = [x for x in items if x["category"] == category]
        if style:
            items = [x for x in items if style in x.get("styles", [])]
        if label_theme:
            items = [x for x in items if label_theme in x.get("label_themes", [])]
        if event_type:
            items = [x for x in items if x.get("event_type") == event_type]
        if fake_state:
            items = [x for x in items if x.get("authenticity") == fake_state]

        if _is_special_items_mode(catalog_type):
            items = _merge_state_for_special_items_for_island(island_id, items)
        else:
            items = deps.with_catalog_state(island_id, catalog_type, items)
            items = deps.with_catalog_variation_counts(island_id, catalog_type, items)

        if owned is not None:
            items = [x for x in items if x["owned"] is owned]
        if variation_scope == "full":
            items = [
                x
                for x in items
                if int(x.get("variation_total") or 0) > 0
                and int(x.get("variation_owned_count") or 0) == int(x.get("variation_total") or 0)
            ]
        elif variation_scope == "partial":
            items = [
                x
                for x in items
                if int(x.get("variation_total") or 0) > 0
                and 0 < int(x.get("variation_owned_count") or 0) < int(x.get("variation_total") or 0)
            ]

        items = deps.sort_catalog_items(items, sort_by=sort_by, sort_order=sort_order)
        total_count = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "count": total_count,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "has_more": end < total_count,
            "items": items[start:end],
        }

    def get_catalog_detail(island_id: int, catalog_type: str, item_id: str) -> dict[str, Any]:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="Catalog not found.")
        item = next((x for x in deps.load_catalog(catalog_type) if x["id"] == item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found.")
        state_catalog_type = _resolve_state_catalog_type(catalog_type, item_id)
        base_row = deps.find_catalog_row(catalog_type, item_id)
        if not base_row:
            raise HTTPException(status_code=404, detail="Source row not found.")

        detail_row = base_row
        from_single = False
        should_fetch_single = state_catalog_type != "art" and len(deps.build_variations(base_row)) == 0
        if should_fetch_single:
            name_en = str(base_row.get("event") or base_row.get("name") or "").strip()
            try:
                single_row = deps.fetch_single_catalog_row(state_catalog_type, name_en)
                if single_row:
                    detail_row = single_row
                    from_single = True
            except Exception:
                from_single = False

        variation_state_map = deps.get_catalog_variation_state_map(island_id, state_catalog_type, item_id)
        return deps.catalog_detail_payload(
            catalog_type=state_catalog_type,
            item=item,
            detail=detail_row,
            from_single=from_single,
            variation_state_map=variation_state_map,
        )

    def update_catalog_state(island_id: int, catalog_type: str, item_id: str, payload: CatalogStateIn) -> CatalogStateOut:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="Catalog not found.")
        state_catalog_type = _resolve_state_catalog_type(catalog_type, item_id)
        if not deps.find_catalog_row(catalog_type, item_id):
            raise HTTPException(status_code=404, detail="Item source row not found.")

        variation_ids = deps.variation_ids_for_item(state_catalog_type, item_id)
        existing = get_catalog_state_map(island_id, state_catalog_type).get(item_id, {})
        new_owned = payload.owned if payload.owned is not None else bool(existing.get("owned"))
        new_donated = payload.donated if payload.donated is not None else bool(existing.get("donated"))
        new_qty = max(0, int(payload.quantity)) if payload.quantity is not None else max(0, int(existing.get("quantity") or 0))

        save_catalog_state(
            island_id,
            state_catalog_type,
            item_id,
            owned=bool(new_owned),
            donated=bool(new_donated),
            quantity=int(new_qty),
        )
        save_all_variation_states(island_id, state_catalog_type, item_id, variation_ids, bool(new_owned))
        deps.invalidate_catalog_state_caches(state_catalog_type, island_id)
        if _is_special_items_mode(catalog_type):
            deps.invalidate_catalog_state_caches(catalog_type, island_id)

        return CatalogStateOut(
            catalog_type=catalog_type,
            item_id=item_id,
            owned=bool(new_owned),
            donated=bool(new_donated),
            quantity=int(new_qty),
        )

    def update_catalog_state_bulk(island_id: int, catalog_type: str, payload: CatalogStateBulkIn) -> dict[str, Any]:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="Catalog not found.")
        item_ids = [str(x).strip() for x in (payload.item_ids or []) if str(x).strip()]
        if not item_ids:
            return {"updated": 0, "owned": bool(payload.owned)}

        loaded_rows = deps.load_catalog(catalog_type)
        valid_ids = {str(x.get("id") or "") for x in loaded_rows if str(x.get("id") or "")}
        target_ids = [item_id for item_id in item_ids if item_id in valid_ids]
        if not target_ids:
            return {"updated": 0, "owned": bool(payload.owned)}

        state_type_map = {item_id: _resolve_state_catalog_type(catalog_type, item_id) for item_id in target_ids}
        updated_total = 0
        for item_id in target_ids:
            state_catalog_type = state_type_map[item_id]
            variation_ids = deps.variation_ids_for_item(state_catalog_type, item_id)
            existing = get_catalog_state_map(island_id, state_catalog_type).get(item_id, {})
            donated = bool(existing.get("donated"))
            current_qty = max(0, int(existing.get("quantity") or 0))
            quantity = max(1, current_qty) if state_catalog_type == "furniture" and not variation_ids and payload.owned else (0 if state_catalog_type == "furniture" and not variation_ids else current_qty)
            save_catalog_state(
                island_id,
                state_catalog_type,
                item_id,
                owned=bool(payload.owned),
                donated=donated,
                quantity=quantity,
            )
            save_all_variation_states(island_id, state_catalog_type, item_id, variation_ids, bool(payload.owned))
            deps.invalidate_catalog_state_caches(state_catalog_type, island_id)
            updated_total += 1

        if _is_special_items_mode(catalog_type):
            deps.invalidate_catalog_state_caches(catalog_type, island_id)
        else:
            deps.invalidate_catalog_state_caches(catalog_type, island_id)
        return {"updated": updated_total, "owned": bool(payload.owned)}

    def update_catalog_variation_state(
        island_id: int,
        catalog_type: str,
        item_id: str,
        variation_id: str,
        payload: CatalogVariationStateIn,
    ) -> CatalogVariationStateOut:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="Catalog not found.")
        state_catalog_type = _resolve_state_catalog_type(catalog_type, item_id)
        if not deps.find_catalog_row(catalog_type, item_id):
            raise HTTPException(status_code=404, detail="Item source row not found.")
        variation_ids = deps.variation_ids_for_item(state_catalog_type, item_id)
        if variation_id not in set(variation_ids):
            raise HTTPException(status_code=404, detail="Variation not found.")

        existing = deps.get_catalog_variation_state_map(island_id, state_catalog_type, item_id).get(variation_id, {})
        current_owned = bool(existing.get("owned"))
        current_qty = max(0, int(existing.get("quantity") or 0))
        new_owned = payload.owned if payload.owned is not None else current_owned
        new_qty = max(0, int(payload.quantity)) if payload.quantity is not None else current_qty
        if payload.quantity is not None:
            new_owned = new_qty > 0

        save_catalog_variation_state(
            island_id,
            state_catalog_type,
            item_id,
            variation_id,
            owned=bool(new_owned),
            quantity=int(new_qty),
            all_variation_ids=variation_ids,
        )
        deps.invalidate_catalog_state_caches(state_catalog_type, island_id)
        if _is_special_items_mode(catalog_type):
            deps.invalidate_catalog_state_caches(catalog_type, island_id)

        return CatalogVariationStateOut(
            catalog_type=catalog_type,
            item_id=item_id,
            variation_id=variation_id,
            owned=bool(new_owned),
            quantity=int(new_qty),
        )

    def update_catalog_variation_state_batch(
        island_id: int,
        catalog_type: str,
        item_id: str,
        payload: CatalogVariationStateBatchIn,
    ) -> dict[str, Any]:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="Catalog not found.")
        if not payload.items:
            return {"updated": 0}

        state_catalog_type = _resolve_state_catalog_type(catalog_type, item_id)
        if not deps.find_catalog_row(catalog_type, item_id):
            raise HTTPException(status_code=404, detail="Item source row not found.")
        variation_ids = deps.variation_ids_for_item(state_catalog_type, item_id)
        variation_id_set = set(variation_ids)
        for row in payload.items:
            if row.variation_id not in variation_id_set:
                raise HTTPException(status_code=404, detail=f"Variation not found: {row.variation_id}")

        item_owned = save_catalog_variation_batch(
            island_id,
            state_catalog_type,
            item_id,
            [
                {"variation_id": row.variation_id, "owned": row.owned, "quantity": row.quantity}
                for row in payload.items
            ],
            variation_ids,
        )
        deps.invalidate_catalog_state_caches(state_catalog_type, island_id)
        if _is_special_items_mode(catalog_type):
            deps.invalidate_catalog_state_caches(catalog_type, island_id)
        return {"updated": len(payload.items), "item_owned": item_owned}

    return CatalogHandlers(
        get_catalog_meta=get_catalog_meta,
        get_catalog=get_catalog,
        get_catalog_detail=get_catalog_detail,
        get_recipe_tags=get_recipe_tags,
        update_catalog_state=update_catalog_state,
        update_catalog_state_bulk=update_catalog_state_bulk,
        update_catalog_variation_state=update_catalog_variation_state,
        update_catalog_variation_state_batch=update_catalog_variation_state_batch,
    )
