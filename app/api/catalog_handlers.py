from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.api.deps import CatalogHandlerDeps, CatalogHandlers
from app.schemas.state import (
    CatalogStateIn,
    CatalogStateOut,
    CatalogVariationStateBatchIn,
    CatalogVariationStateIn,
    CatalogVariationStateOut,
)


def create_catalog_handlers(deps: CatalogHandlerDeps) -> CatalogHandlers:
    def get_catalog_meta(catalog_type: str) -> dict[str, Any]:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="알 수 없는 카탈로그입니다.")

        rows = deps.load_catalog(catalog_type)
        categories = deps.order_categories(
            catalog_type, list({x["category"] for x in rows if x["category"]})
        )
        category_rows = [
            {"en": c, "ko": deps.category_ko_for(catalog_type, c)} for c in categories
        ]

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
            ]

        if category:
            items = [x for x in items if x["category"] == category]
        if style:
            items = [x for x in items if style in x.get("styles", [])]
        if label_theme:
            items = [x for x in items if label_theme in x.get("label_themes", [])]
        if event_type:
            items = [x for x in items if x.get("event_type") == event_type]
        if fake_state:
            items = [x for x in items if x.get("authenticity") == fake_state]

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

        base_row = deps.find_catalog_row(catalog_type, item_id)
        if not base_row:
            raise HTTPException(status_code=404, detail="아이템 원본 데이터를 찾을 수 없습니다.")

        detail_row = base_row
        from_single = False
        # art는 목록 응답에 real_info/fake_info가 충분히 포함되므로
        # single endpoint 추가 호출을 생략해 상세 열기 속도를 개선한다.
        should_fetch_single = catalog_type != "art" and len(deps.build_variations(base_row)) == 0
        if should_fetch_single:
            name_en = str(base_row.get("event") or base_row.get("name") or "").strip()
            try:
                single_row = deps.fetch_single_catalog_row(catalog_type, name_en)
                if single_row:
                    detail_row = single_row
                    from_single = True
            except Exception:
                from_single = False

        variation_state_map = deps.get_catalog_variation_state_map(catalog_type, item_id)
        return deps.catalog_detail_payload(
            catalog_type=catalog_type,
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

        deps.init_db()
        if not deps.find_catalog_row(catalog_type, item_id):
            raise HTTPException(status_code=404, detail="아이템 원본 데이터를 찾을 수 없습니다.")
        variation_ids = deps.variation_ids_for_item(catalog_type, item_id)

        with deps.get_db() as conn:
            existing = conn.execute(
                "SELECT owned FROM catalog_state WHERE catalog_type = ? AND item_id = ?",
                (catalog_type, item_id),
            ).fetchone()

            current_owned = bool(existing["owned"]) if existing else False
            new_owned = payload.owned if payload.owned is not None else current_owned

            deps.upsert_catalog_state(conn, catalog_type, item_id, bool(new_owned))
            deps.upsert_all_variation_states(
                conn, catalog_type, item_id, variation_ids, bool(new_owned)
            )

        return CatalogStateOut(
            catalog_type=catalog_type,
            item_id=item_id,
            owned=bool(new_owned),
        )

    def update_catalog_variation_state(
        catalog_type: str,
        item_id: str,
        variation_id: str,
        payload: CatalogVariationStateIn,
    ) -> CatalogVariationStateOut:
        if catalog_type not in deps.catalog_types:
            raise HTTPException(status_code=404, detail="알 수 없는 카탈로그입니다.")

        if not deps.find_catalog_row(catalog_type, item_id):
            raise HTTPException(status_code=404, detail="아이템 원본 데이터를 찾을 수 없습니다.")
        variation_ids = deps.variation_ids_for_item(catalog_type, item_id)
        variation_id_set = set(variation_ids)
        if variation_id not in variation_id_set:
            raise HTTPException(status_code=404, detail="변형을 찾을 수 없습니다.")

        deps.init_db()
        with deps.get_db() as conn:
            existing = conn.execute(
                """
                SELECT owned
                FROM catalog_variation_state
                WHERE catalog_type = ? AND item_id = ? AND variation_id = ?
                """,
                (catalog_type, item_id, variation_id),
            ).fetchone()

            current_owned = bool(existing["owned"]) if existing else False
            new_owned = payload.owned if payload.owned is not None else current_owned

            conn.execute(
                """
                INSERT INTO catalog_variation_state (catalog_type, item_id, variation_id, owned)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(catalog_type, item_id, variation_id) DO UPDATE SET
                    owned = excluded.owned,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (catalog_type, item_id, variation_id, int(new_owned)),
            )
            deps.recalc_item_owned_from_variations(conn, catalog_type, item_id, variation_ids)

        return CatalogVariationStateOut(
            catalog_type=catalog_type,
            item_id=item_id,
            variation_id=variation_id,
            owned=bool(new_owned),
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

        if not deps.find_catalog_row(catalog_type, item_id):
            raise HTTPException(status_code=404, detail="아이템 원본 데이터를 찾을 수 없습니다.")
        variation_ids = deps.variation_ids_for_item(catalog_type, item_id)
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
                INSERT INTO catalog_variation_state (catalog_type, item_id, variation_id, owned)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(catalog_type, item_id, variation_id) DO UPDATE SET
                    owned = excluded.owned,
                    updated_at = CURRENT_TIMESTAMP
                """,
                [
                    (catalog_type, item_id, row.variation_id, int(row.owned))
                    for row in payload.items
                ],
            )
            item_owned = deps.recalc_item_owned_from_variations(
                conn, catalog_type, item_id, variation_ids
            )

        return {"updated": len(payload.items), "item_owned": item_owned}

    return CatalogHandlers(
        get_catalog_meta=get_catalog_meta,
        get_catalog=get_catalog,
        get_catalog_detail=get_catalog_detail,
        update_catalog_state=update_catalog_state,
        update_catalog_variation_state=update_catalog_variation_state,
        update_catalog_variation_state_batch=update_catalog_variation_state_batch,
        get_art_guide=get_art_guide,
    )
