from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.api.deps import CatalogHandlerDeps, CatalogHandlers
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

    def _merge_state_for_special_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            origin = str(item.get("origin_catalog_type") or "").strip()
            if not origin:
                continue
            grouped.setdefault(origin, []).append(item)

        merged_by_id: dict[str, dict[str, Any]] = {}
        for origin, rows in grouped.items():
            rows_with_state = deps.with_catalog_state(origin, rows)
            rows_with_counts = deps.with_catalog_variation_counts(origin, rows_with_state)
            for row in rows_with_counts:
                row_id = str(row.get("id") or "")
                if row_id:
                    merged_by_id[row_id] = row

        return [merged_by_id.get(str(item.get("id") or ""), item) for item in items]

    def get_catalog_meta(catalog_type: str) -> dict[str, Any]:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="알 수 없는 카탈로그입니다.")

        rows = deps.load_catalog(catalog_type)
        category_values = {x["category"] for x in rows if x["category"]}
        if catalog_type == "recipes":
            for row in rows:
                filters = row.get("recipe_filters")
                if isinstance(filters, list):
                    category_values.update(str(v).strip() for v in filters if str(v).strip())
        categories = deps.order_categories(catalog_type, list(category_values))
        category_rows = [
            {"en": c, "ko": deps.category_ko_for(catalog_type, c)} for c in categories
        ]

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
            response["label_themes"] = [
                {"en": t, "ko": label_theme_map.get(t, t)} for t in label_themes
            ]

        if catalog_type == "events":
            event_types = sorted({x["event_type"] for x in rows if x["event_type"]})
            response["event_types"] = event_types
        if catalog_type == "art":
            response["authenticity_types"] = [
                {"en": "genuine_only", "ko": "진품만"},
                {"en": "has_fake", "ko": "가품 있음"},
            ]

        return response

    def get_recipe_tags(catalog_type: str) -> dict[str, Any]:
        if catalog_type != "recipes":
            raise HTTPException(status_code=404, detail="레시피 태그는 recipes 카탈로그에서만 지원합니다.")
        rows = deps.load_recipe_tags() or []
        return {
            "count": len(rows),
            "items": rows,
        }

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
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="알 수 없는 카탈로그입니다.")

        page = max(1, int(page or 1))
        page_size = max(1, min(200, int(page_size or 60)))

        # 먼저 정적 필터를 적용해 후보군을 줄인 뒤 상태/보유 집계를 붙이면 응답 속도가 빨라진다.
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
            if catalog_type == "recipes" and (
                category.startswith("season:")
                or category.startswith("event:")
                or category.startswith("npc:")
                or category.startswith("ingredient:")
            ):
                items = [
                    x
                    for x in items
                    if category in (x.get("recipe_filters") or [])
                ]
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
            items = _merge_state_for_special_items(items)
        else:
            items = deps.with_catalog_state(catalog_type, items)
            items = deps.with_catalog_variation_counts(catalog_type, items)

        if owned is not None:
            items = [x for x in items if x["owned"] is owned]
        if variation_scope == "full":
            items = [
                x
                for x in items
                if int(x.get("variation_total") or 0) > 0
                and int(x.get("variation_owned_count") or 0)
                == int(x.get("variation_total") or 0)
            ]
        elif variation_scope == "partial":
            items = [
                x
                for x in items
                if int(x.get("variation_total") or 0) > 0
                and 0
                < int(x.get("variation_owned_count") or 0)
                < int(x.get("variation_total") or 0)
            ]

        items = deps.sort_catalog_items(items, sort_by=sort_by, sort_order=sort_order)
        total_count = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        paged_items = items[start:end]
        has_more = end < total_count
        return {
            "count": total_count,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "has_more": has_more,
            "items": paged_items,
        }

    def get_art_guide() -> dict[str, Any]:
        if "art" not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="미술품 카탈로그가 없습니다.")
        items = deps.load_catalog("art")
        rows = deps.sort_catalog_items(items, sort_by="name", sort_order="asc")
        return {
            "count": len(rows),
            "items": [
                {
                    "id": x["id"],
                    "name": x.get("name") or x.get("name_en") or "",
                    "name_ko": x.get("name_ko") or "",
                    "name_en": x.get("name_en") or "",
                    "authenticity": x.get("authenticity") or "",
                    "authenticity_ko": x.get("authenticity_ko") or "",
                    "real_image_url": x.get("real_image_url") or x.get("image_url") or "",
                    "fake_image_url": x.get("fake_image_url") or "",
                    "real_description": x.get("real_description") or "",
                    "fake_description": x.get("fake_description") or "",
                    "owned": bool(x.get("owned")),
                }
                for x in deps.with_catalog_state("art", rows)
            ],
        }

    def get_catalog_detail(catalog_type: str, item_id: str) -> dict[str, Any]:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="알 수 없는 카탈로그입니다.")

        item = next((x for x in deps.load_catalog(catalog_type) if x["id"] == item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")
        state_catalog_type = _resolve_state_catalog_type(catalog_type, item_id)

        base_row = deps.find_catalog_row(catalog_type, item_id)
        if not base_row:
            raise HTTPException(status_code=404, detail="아이템 원본 데이터를 찾을 수 없습니다.")

        detail_row = base_row
        from_single = False
        # art는 목록 응답에 real_info/fake_info가 충분히 포함되므로
        # single endpoint 추가 호출을 생략해 상세 열기 속도를 개선한다.
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

        variation_state_map = deps.get_catalog_variation_state_map(state_catalog_type, item_id)
        return deps.catalog_detail_payload(
            catalog_type=state_catalog_type,
            item=item,
            detail=detail_row,
            from_single=from_single,
            variation_state_map=variation_state_map,
        )

    def update_catalog_state(
        catalog_type: str, item_id: str, payload: CatalogStateIn
    ) -> CatalogStateOut:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="알 수 없는 카탈로그입니다.")

        state_catalog_type = _resolve_state_catalog_type(catalog_type, item_id)

        deps.init_db()
        if not deps.find_catalog_row(catalog_type, item_id):
            raise HTTPException(status_code=404, detail="아이템 원본 데이터를 찾을 수 없습니다.")
        variation_ids = deps.variation_ids_for_item(state_catalog_type, item_id)

        with deps.get_db() as conn:
            existing = conn.execute(
                """
                SELECT owned, donated, quantity
                FROM catalog_state
                WHERE catalog_type = ? AND item_id = ?
                """,
                (state_catalog_type, item_id),
            ).fetchone()

            current_owned = bool(existing["owned"]) if existing else False
            current_donated = bool(existing["donated"]) if existing else False
            current_qty = max(0, int((existing["quantity"] if existing else 0) or 0))
            new_owned = payload.owned if payload.owned is not None else current_owned
            new_donated = (
                payload.donated if payload.donated is not None else current_donated
            )
            new_qty = (
                max(0, int(payload.quantity))
                if payload.quantity is not None
                else current_qty
            )
            deps.upsert_catalog_state(
                conn,
                state_catalog_type,
                item_id,
                bool(new_owned),
                int(new_qty),
                bool(new_donated),
            )
            deps.upsert_all_variation_states(
                conn, state_catalog_type, item_id, variation_ids, bool(new_owned)
            )
        deps.invalidate_catalog_state_caches(state_catalog_type)
        if _is_special_items_mode(catalog_type):
            deps.invalidate_catalog_state_caches(catalog_type)

        return CatalogStateOut(
            catalog_type=catalog_type,
            item_id=item_id,
            owned=bool(new_owned),
            donated=bool(new_donated),
            quantity=int(new_qty),
        )

    def update_catalog_state_bulk(
        catalog_type: str,
        payload: CatalogStateBulkIn,
    ) -> dict[str, Any]:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="알 수 없는 카탈로그입니다.")
        item_ids = [str(x).strip() for x in (payload.item_ids or []) if str(x).strip()]
        if not item_ids:
            return {"updated": 0, "owned": bool(payload.owned)}

        # 현재 모드 목록에 있는 id만 허용
        loaded_rows = deps.load_catalog(catalog_type)
        valid_ids = {str(x.get("id") or "") for x in loaded_rows if str(x.get("id") or "")}
        target_ids = [item_id for item_id in item_ids if item_id in valid_ids]
        if not target_ids:
            return {"updated": 0, "owned": bool(payload.owned)}

        deps.init_db()
        state_type_map = {
            item_id: _resolve_state_catalog_type(catalog_type, item_id) for item_id in target_ids
        }
        variation_map = {
            item_id: deps.variation_ids_for_item(state_type_map[item_id], item_id)
            for item_id in target_ids
        }

        if _is_special_items_mode(catalog_type):
            groups: dict[str, list[str]] = {}
            for item_id in target_ids:
                groups.setdefault(state_type_map[item_id], []).append(item_id)
            updated_total = 0
            for state_catalog_type, grouped_item_ids in groups.items():
                with deps.get_db() as conn:
                    placeholders = ",".join("?" for _ in grouped_item_ids)
                    existing_rows = conn.execute(
                        f"""
                        SELECT item_id, donated, quantity
                        FROM catalog_state
                        WHERE catalog_type = ? AND item_id IN ({placeholders})
                        """,
                        (state_catalog_type, *grouped_item_ids),
                    ).fetchall()
                    existing_map = {
                        str(r["item_id"]): {
                            "donated": bool(r["donated"]),
                            "quantity": max(0, int(r["quantity"] or 0)),
                        }
                        for r in existing_rows
                    }

                    state_rows = []
                    for item_id in grouped_item_ids:
                        prev = existing_map.get(item_id, {"donated": False, "quantity": 0})
                        donated = bool(prev["donated"])
                        current_qty = int(prev["quantity"])
                        variation_ids = variation_map[item_id]
                        has_variations = len(variation_ids) > 0
                        if state_catalog_type == "furniture" and not has_variations:
                            quantity = max(1, current_qty) if payload.owned else 0
                        else:
                            quantity = current_qty
                        state_rows.append(
                            (state_catalog_type, item_id, int(payload.owned), int(donated), int(quantity))
                        )

                    conn.executemany(
                        """
                        INSERT INTO catalog_state (catalog_type, item_id, owned, donated, quantity)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(catalog_type, item_id) DO UPDATE SET
                            owned = excluded.owned,
                            donated = excluded.donated,
                            quantity = excluded.quantity,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        state_rows,
                    )

                    variation_rows = []
                    for item_id in grouped_item_ids:
                        for variation_id in variation_map[item_id]:
                            qty = 1 if payload.owned else 0
                            variation_rows.append(
                                (state_catalog_type, item_id, variation_id, int(payload.owned), int(qty))
                            )
                    if variation_rows:
                        conn.executemany(
                            """
                            INSERT INTO catalog_variation_state (catalog_type, item_id, variation_id, owned, quantity)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(catalog_type, item_id, variation_id) DO UPDATE SET
                                owned = excluded.owned,
                                quantity = excluded.quantity,
                                updated_at = CURRENT_TIMESTAMP
                            """,
                            variation_rows,
                        )
                deps.invalidate_catalog_state_caches(state_catalog_type)
                updated_total += len(grouped_item_ids)
            deps.invalidate_catalog_state_caches(catalog_type)
            return {"updated": updated_total, "owned": bool(payload.owned)}

        with deps.get_db() as conn:
            placeholders = ",".join("?" for _ in target_ids)
            existing_rows = conn.execute(
                f"""
                SELECT item_id, donated, quantity
                FROM catalog_state
                WHERE catalog_type = ? AND item_id IN ({placeholders})
                """,
                (catalog_type, *target_ids),
            ).fetchall()
            existing_map = {
                str(r["item_id"]): {
                    "donated": bool(r["donated"]),
                    "quantity": max(0, int(r["quantity"] or 0)),
                }
                for r in existing_rows
            }

            state_rows = []
            for item_id in target_ids:
                prev = existing_map.get(item_id, {"donated": False, "quantity": 0})
                donated = bool(prev["donated"])
                current_qty = int(prev["quantity"])
                variation_ids = variation_map[item_id]
                has_variations = len(variation_ids) > 0
                if catalog_type == "furniture" and not has_variations:
                    quantity = max(1, current_qty) if payload.owned else 0
                else:
                    quantity = current_qty
                state_rows.append(
                    (catalog_type, item_id, int(payload.owned), int(donated), int(quantity))
                )

            conn.executemany(
                """
                INSERT INTO catalog_state (catalog_type, item_id, owned, donated, quantity)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(catalog_type, item_id) DO UPDATE SET
                    owned = excluded.owned,
                    donated = excluded.donated,
                    quantity = excluded.quantity,
                    updated_at = CURRENT_TIMESTAMP
                """,
                state_rows,
            )

            variation_rows = []
            for item_id in target_ids:
                for variation_id in variation_map[item_id]:
                    qty = 1 if payload.owned else 0
                    variation_rows.append(
                        (catalog_type, item_id, variation_id, int(payload.owned), int(qty))
                    )
            if variation_rows:
                conn.executemany(
                    """
                    INSERT INTO catalog_variation_state (catalog_type, item_id, variation_id, owned, quantity)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(catalog_type, item_id, variation_id) DO UPDATE SET
                        owned = excluded.owned,
                        quantity = excluded.quantity,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    variation_rows,
                )
        deps.invalidate_catalog_state_caches(catalog_type)

        return {"updated": len(target_ids), "owned": bool(payload.owned)}

    def update_catalog_variation_state(
        catalog_type: str,
        item_id: str,
        variation_id: str,
        payload: CatalogVariationStateIn,
    ) -> CatalogVariationStateOut:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="알 수 없는 카탈로그입니다.")

        state_catalog_type = _resolve_state_catalog_type(catalog_type, item_id)

        if not deps.find_catalog_row(catalog_type, item_id):
            raise HTTPException(status_code=404, detail="아이템 원본 데이터를 찾을 수 없습니다.")
        variation_ids = deps.variation_ids_for_item(state_catalog_type, item_id)
        variation_id_set = set(variation_ids)
        if variation_id not in variation_id_set:
            raise HTTPException(status_code=404, detail="변형을 찾을 수 없습니다.")

        deps.init_db()
        with deps.get_db() as conn:
            existing = conn.execute(
                """
                SELECT owned, quantity
                FROM catalog_variation_state
                WHERE catalog_type = ? AND item_id = ? AND variation_id = ?
                """,
                (state_catalog_type, item_id, variation_id),
            ).fetchone()

            current_owned = bool(existing["owned"]) if existing else False
            current_qty = max(0, int((existing["quantity"] if existing else 0) or 0))
            new_owned = payload.owned if payload.owned is not None else current_owned
            new_qty = (
                max(0, int(payload.quantity))
                if payload.quantity is not None
                else current_qty
            )
            if payload.quantity is not None:
                new_owned = new_qty > 0

            conn.execute(
                """
                INSERT INTO catalog_variation_state (catalog_type, item_id, variation_id, owned, quantity)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(catalog_type, item_id, variation_id) DO UPDATE SET
                    owned = excluded.owned,
                    quantity = excluded.quantity,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (state_catalog_type, item_id, variation_id, int(new_owned), int(new_qty)),
            )
            deps.recalc_item_owned_from_variations(conn, state_catalog_type, item_id, variation_ids)
        deps.invalidate_catalog_state_caches(state_catalog_type)
        if _is_special_items_mode(catalog_type):
            deps.invalidate_catalog_state_caches(catalog_type)

        return CatalogVariationStateOut(
            catalog_type=catalog_type,
            item_id=item_id,
            variation_id=variation_id,
            owned=bool(new_owned),
            quantity=int(new_qty),
        )

    def update_catalog_variation_state_batch(
        catalog_type: str,
        item_id: str,
        payload: CatalogVariationStateBatchIn,
    ) -> dict[str, Any]:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="알 수 없는 카탈로그입니다.")
        if not payload.items:
            return {"updated": 0}

        state_catalog_type = _resolve_state_catalog_type(catalog_type, item_id)

        if not deps.find_catalog_row(catalog_type, item_id):
            raise HTTPException(status_code=404, detail="아이템 원본 데이터를 찾을 수 없습니다.")
        variation_ids = deps.variation_ids_for_item(state_catalog_type, item_id)
        variation_id_set = set(variation_ids)
        for row in payload.items:
            if row.variation_id not in variation_id_set:
                raise HTTPException(
                    status_code=404, detail=f"변형을 찾을 수 없습니다: {row.variation_id}"
                )

        deps.init_db()
        with deps.get_db() as conn:
            conn.executemany(
                """
                INSERT INTO catalog_variation_state (catalog_type, item_id, variation_id, owned, quantity)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(catalog_type, item_id, variation_id) DO UPDATE SET
                    owned = excluded.owned,
                    quantity = excluded.quantity,
                    updated_at = CURRENT_TIMESTAMP
                """,
                [
                    (
                        state_catalog_type,
                        item_id,
                        row.variation_id,
                        int((max(0, int(row.quantity)) > 0) if row.quantity is not None else row.owned),
                        int(max(0, int(row.quantity)) if row.quantity is not None else (1 if row.owned else 0)),
                    )
                    for row in payload.items
                ],
            )
            item_owned = deps.recalc_item_owned_from_variations(
                conn, state_catalog_type, item_id, variation_ids
            )
        deps.invalidate_catalog_state_caches(state_catalog_type)
        if _is_special_items_mode(catalog_type):
            deps.invalidate_catalog_state_caches(catalog_type)

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
        get_art_guide=get_art_guide,
    )
