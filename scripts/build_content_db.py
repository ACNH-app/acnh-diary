from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import CATALOG_TYPES
from app.core.content_db import get_content_db
from app.domain.catalog import category_ko_for
from app.services.catalog_data import (
    _build_variations,
    _catalog_row_index,
    _recipe_filter_keys,
    load_catalog,
    load_villagers,
)
from app.services.source import extract_source_pair, translate_source_value_to_ko

SNAPSHOT_PATH = ROOT / "data" / "content_full_snapshot.json"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS catalog_items (
    catalog_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    name_ko TEXT NOT NULL DEFAULT '',
    name_en TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    category_ko TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    source_ko TEXT NOT NULL DEFAULT '',
    source_notes TEXT NOT NULL DEFAULT '',
    source_notes_ko TEXT NOT NULL DEFAULT '',
    buy INTEGER NOT NULL DEFAULT 0,
    sell INTEGER NOT NULL DEFAULT 0,
    number INTEGER NOT NULL DEFAULT 0,
    event_type TEXT NOT NULL DEFAULT '',
    date TEXT NOT NULL DEFAULT '',
    image_url TEXT NOT NULL DEFAULT '',
    not_for_sale INTEGER NOT NULL DEFAULT 0,
    variation_total INTEGER NOT NULL DEFAULT 0,
    status_label TEXT NOT NULL DEFAULT '',
    raw_json TEXT NOT NULL DEFAULT '{}',
    item_json TEXT NOT NULL DEFAULT '{}',
    built_at_utc TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (catalog_type, item_id)
);

CREATE INDEX IF NOT EXISTS idx_catalog_items_type_category
ON catalog_items (catalog_type, category);

CREATE INDEX IF NOT EXISTS idx_catalog_items_type_name
ON catalog_items (catalog_type, name_ko, name_en);

CREATE INDEX IF NOT EXISTS idx_catalog_items_type_source
ON catalog_items (catalog_type, source);

CREATE TABLE IF NOT EXISTS catalog_variations (
    catalog_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    variation_id TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    color1 TEXT NOT NULL DEFAULT '',
    color2 TEXT NOT NULL DEFAULT '',
    pattern TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    source_ko TEXT NOT NULL DEFAULT '',
    source_notes TEXT NOT NULL DEFAULT '',
    source_notes_ko TEXT NOT NULL DEFAULT '',
    price INTEGER NOT NULL DEFAULT 0,
    image_url TEXT NOT NULL DEFAULT '',
    raw_json TEXT NOT NULL DEFAULT '{}',
    built_at_utc TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (catalog_type, item_id, variation_id)
);

CREATE INDEX IF NOT EXISTS idx_catalog_variations_item
ON catalog_variations (catalog_type, item_id);

CREATE TABLE IF NOT EXISTS villagers (
    villager_id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    name_ko TEXT NOT NULL DEFAULT '',
    name_en TEXT NOT NULL DEFAULT '',
    species TEXT NOT NULL DEFAULT '',
    species_ko TEXT NOT NULL DEFAULT '',
    personality TEXT NOT NULL DEFAULT '',
    personality_ko TEXT NOT NULL DEFAULT '',
    sub_personality TEXT NOT NULL DEFAULT '',
    gender TEXT NOT NULL DEFAULT '',
    hobby TEXT NOT NULL DEFAULT '',
    sign TEXT NOT NULL DEFAULT '',
    birthday TEXT NOT NULL DEFAULT '',
    catchphrase TEXT NOT NULL DEFAULT '',
    catchphrase_ko TEXT NOT NULL DEFAULT '',
    saying TEXT NOT NULL DEFAULT '',
    saying_ko TEXT NOT NULL DEFAULT '',
    image_url TEXT NOT NULL DEFAULT '',
    icon_url TEXT NOT NULL DEFAULT '',
    photo_url TEXT NOT NULL DEFAULT '',
    house_exterior_url TEXT NOT NULL DEFAULT '',
    house_interior_url TEXT NOT NULL DEFAULT '',
    raw_json TEXT NOT NULL DEFAULT '{}',
    built_at_utc TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_villagers_name
ON villagers (name_ko, name_en);

CREATE TABLE IF NOT EXISTS catalog_meta (
    catalog_type TEXT PRIMARY KEY,
    status_label TEXT NOT NULL DEFAULT '',
    item_count INTEGER NOT NULL DEFAULT 0,
    variation_count INTEGER NOT NULL DEFAULT 0,
    built_at_utc TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS content_version (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS recipe_tags (
    tag_key TEXT PRIMARY KEY,
    tag_type TEXT NOT NULL DEFAULT '',
    name_ko TEXT NOT NULL DEFAULT '',
    name_en TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_system INTEGER NOT NULL DEFAULT 1,
    built_at_utc TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS recipe_tag_links (
    recipe_item_id TEXT NOT NULL,
    tag_key TEXT NOT NULL,
    built_at_utc TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (recipe_item_id, tag_key),
    FOREIGN KEY (tag_key) REFERENCES recipe_tags(tag_key)
);

CREATE INDEX IF NOT EXISTS idx_recipe_tag_links_tag_key
ON recipe_tag_links (tag_key, recipe_item_id);
"""


def _exec_schema(conn) -> None:
    conn.executescript(SCHEMA_SQL)
    cols = {str(r["name"]) for r in conn.execute("PRAGMA table_info(catalog_items)").fetchall()}
    if "item_json" not in cols:
        conn.execute("ALTER TABLE catalog_items ADD COLUMN item_json TEXT NOT NULL DEFAULT '{}'")
    if "source_ko" not in cols:
        conn.execute("ALTER TABLE catalog_items ADD COLUMN source_ko TEXT NOT NULL DEFAULT ''")
    if "source_notes_ko" not in cols:
        conn.execute("ALTER TABLE catalog_items ADD COLUMN source_notes_ko TEXT NOT NULL DEFAULT ''")
    vcols = {str(r["name"]) for r in conn.execute("PRAGMA table_info(catalog_variations)").fetchall()}
    if "source_ko" not in vcols:
        conn.execute("ALTER TABLE catalog_variations ADD COLUMN source_ko TEXT NOT NULL DEFAULT ''")
    if "source_notes_ko" not in vcols:
        conn.execute("ALTER TABLE catalog_variations ADD COLUMN source_notes_ko TEXT NOT NULL DEFAULT ''")


def _clear_tables(conn) -> None:
    conn.execute("DELETE FROM catalog_items")
    conn.execute("DELETE FROM catalog_variations")
    conn.execute("DELETE FROM villagers")
    conn.execute("DELETE FROM catalog_meta")
    conn.execute("DELETE FROM recipe_tag_links")
    conn.execute("DELETE FROM recipe_tags")
    conn.execute("DELETE FROM content_version")


def _recipe_tag_type(tag_key: str) -> str:
    if tag_key.startswith("season:"):
        return "season"
    if tag_key.startswith("event:"):
        return "event"
    if tag_key.startswith("npc:"):
        return "npc"
    if tag_key.startswith("ingredient:"):
        return "ingredient"
    return "custom"


def _recipe_tag_name_en(tag_key: str) -> str:
    if ":" in tag_key:
        return tag_key.split(":", 1)[1]
    return tag_key


def _build_source_snapshot() -> dict[str, object]:
    # 스냅샷 갱신 시에는 content.db를 읽지 않고 원본 로더 경로를 사용한다.
    prev_use_content_db = os.environ.get("USE_CONTENT_DB")
    os.environ["USE_CONTENT_DB"] = "0"
    for fn in (load_catalog, _catalog_row_index, load_villagers):
        try:
            fn.cache_clear()  # type: ignore[attr-defined]
        except Exception:
            pass

    snapshot_catalog: dict[str, dict[str, object]] = {}
    try:
        for catalog_type, cfg in CATALOG_TYPES.items():
            items = load_catalog(catalog_type)
            row_index = _catalog_row_index(catalog_type)
            bundled: list[dict[str, object]] = []
            for item in items:
                item_id = str(item.get("id") or "").strip()
                if not item_id:
                    continue
                raw = row_index.get(item_id) or {}
                bundled.append({"item": item, "raw": raw})
            snapshot_catalog[catalog_type] = {
                "status_label": str(cfg.get("status_label") or ""),
                "items": bundled,
            }
        return {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "catalog": snapshot_catalog,
            "villagers": load_villagers(),
        }
    finally:
        if prev_use_content_db is None:
            os.environ.pop("USE_CONTENT_DB", None)
        else:
            os.environ["USE_CONTENT_DB"] = prev_use_content_db
        for fn in (load_catalog, _catalog_row_index, load_villagers):
            try:
                fn.cache_clear()  # type: ignore[attr-defined]
            except Exception:
                pass


def _load_or_create_snapshot(refresh: bool) -> dict[str, object]:
    if SNAPSHOT_PATH.exists() and not refresh:
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    snapshot = _build_source_snapshot()
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return snapshot


def _insert_catalog(conn, built_at: str, snapshot: dict[str, object]) -> tuple[int, int]:
    item_count = 0
    variation_count = 0
    recipe_tag_links: list[tuple[str, str, str]] = []
    recipe_tag_rows: dict[str, tuple[str, str, str, int, int, str]] = {}
    recipe_tag_rank = 0
    snap_catalog = snapshot.get("catalog")
    if not isinstance(snap_catalog, dict):
        raise RuntimeError("snapshot.catalog 형식이 올바르지 않습니다.")

    for catalog_type in CATALOG_TYPES.keys():
        snap_entry = snap_catalog.get(catalog_type, {})
        if not isinstance(snap_entry, dict):
            continue
        status_label = str(snap_entry.get("status_label") or "")
        bundled = snap_entry.get("items")
        if not isinstance(bundled, list):
            continue

        item_rows: list[tuple] = []
        variation_rows: list[tuple] = []

        for row_bundle in bundled:
            if not isinstance(row_bundle, dict):
                continue
            item = row_bundle.get("item")
            raw = row_bundle.get("raw")
            if not isinstance(item, dict):
                continue
            if not isinstance(raw, dict):
                raw = {}
            item_id = str(item.get("id") or "").strip()
            if not item_id:
                continue
            item_source_ko = str(item.get("source_ko") or item.get("source") or "")
            item_source_notes_ko = str(item.get("source_notes_ko") or item.get("source_notes") or "")
            item_rows.append(
                (
                    catalog_type,
                    item_id,
                    str(item.get("name") or ""),
                    str(item.get("name_ko") or ""),
                    str(item.get("name_en") or ""),
                    str(item.get("category") or ""),
                    str(item.get("category_ko") or ""),
                    str(item.get("source") or ""),
                    item_source_ko,
                    str(item.get("source_notes") or ""),
                    item_source_notes_ko,
                    int(item.get("buy") or 0),
                    int(item.get("sell") or 0),
                    int(item.get("number") or 0),
                    str(item.get("event_type") or ""),
                    str(item.get("date") or ""),
                    str(item.get("image_url") or ""),
                    int(bool(item.get("not_for_sale"))),
                    int(item.get("variation_total") or 0),
                    status_label,
                    json.dumps(raw, ensure_ascii=False),
                    json.dumps(item, ensure_ascii=False),
                    built_at,
                )
            )
            # raw 기준으로 분리 한글 출처 필드를 보정
            source_ko, notes_ko = extract_source_pair(raw)
            if source_ko or notes_ko:
                last = item_rows[-1]
                item_rows[-1] = (
                    last[0],  # catalog_type
                    last[1],  # item_id
                    last[2],  # name
                    last[3],  # name_ko
                    last[4],  # name_en
                    last[5],  # category
                    last[6],  # category_ko
                    last[7],  # source
                    source_ko or last[8],  # source_ko
                    last[9],  # source_notes
                    notes_ko or last[10],  # source_notes_ko
                    last[11],  # buy
                    last[12],  # sell
                    last[13],  # number
                    last[14],  # event_type
                    last[15],  # date
                    last[16],  # image_url
                    last[17],  # not_for_sale
                    last[18],  # variation_total
                    last[19],  # status_label
                    last[20],  # raw_json
                    last[21],  # item_json
                    last[22],  # built_at
                )

            if catalog_type == "recipes":
                tag_keys = _recipe_filter_keys(raw if isinstance(raw, dict) else {}, source_ko or item_source_ko, notes_ko or item_source_notes_ko)
                for tag_key in tag_keys:
                    tag_key = str(tag_key or "").strip()
                    if not tag_key:
                        continue
                    recipe_tag_links.append((item_id, tag_key, built_at))
                    if tag_key not in recipe_tag_rows:
                        recipe_tag_rank += 1
                        recipe_tag_rows[tag_key] = (
                            tag_key,
                            _recipe_tag_type(tag_key),
                            str(category_ko_for("recipes", tag_key) or tag_key),
                            _recipe_tag_name_en(tag_key),
                            recipe_tag_rank,
                            1,
                            built_at,
                        )

            for variation in _build_variations(raw if isinstance(raw, dict) else {}):
                variation_rows.append(
                    (
                        catalog_type,
                        item_id,
                        str(variation.get("id") or ""),
                        str(variation.get("label") or ""),
                        str(variation.get("color1") or ""),
                        str(variation.get("color2") or ""),
                        str(variation.get("pattern") or ""),
                        str(variation.get("source") or ""),
                        str(translate_source_value_to_ko(variation.get("source")) or variation.get("source") or ""),
                        str(variation.get("source_notes") or ""),
                        str(variation.get("source_notes") or ""),
                        int(variation.get("price") or 0),
                        str(variation.get("image_url") or ""),
                        json.dumps(variation, ensure_ascii=False),
                        built_at,
                    )
                )

        conn.executemany(
            """
            INSERT OR REPLACE INTO catalog_items (
                catalog_type, item_id, name, name_ko, name_en, category, category_ko,
                source, source_ko, source_notes, source_notes_ko, buy, sell, number, event_type, date, image_url,
                not_for_sale, variation_total, status_label, raw_json, item_json, built_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            item_rows,
        )
        if variation_rows:
            conn.executemany(
                """
                INSERT OR REPLACE INTO catalog_variations (
                    catalog_type, item_id, variation_id, label, color1, color2, pattern,
                    source, source_ko, source_notes, source_notes_ko, price, image_url, raw_json, built_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                variation_rows,
            )
        conn.execute(
            """
            INSERT OR REPLACE INTO catalog_meta (
                catalog_type, status_label, item_count, variation_count, built_at_utc
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                catalog_type,
                status_label,
                len(item_rows),
                len(variation_rows),
                built_at,
            ),
        )

        item_count += len(item_rows)
        variation_count += len(variation_rows)

    if recipe_tag_rows:
        conn.executemany(
            """
            INSERT OR REPLACE INTO recipe_tags (
                tag_key, tag_type, name_ko, name_en, sort_order, is_system, built_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            list(recipe_tag_rows.values()),
        )
    if recipe_tag_links:
        conn.executemany(
            """
            INSERT OR REPLACE INTO recipe_tag_links (
                recipe_item_id, tag_key, built_at_utc
            ) VALUES (?, ?, ?)
            """,
            recipe_tag_links,
        )
    return item_count, variation_count


def _insert_villagers(conn, built_at: str, snapshot: dict[str, object]) -> int:
    villagers = snapshot.get("villagers")
    if not isinstance(villagers, list):
        raise RuntimeError("snapshot.villagers 형식이 올바르지 않습니다.")
    rows = []
    for v in villagers:
        if not isinstance(v, dict):
            continue
        villager_id = str(v.get("id") or "").strip()
        if not villager_id:
            continue
        rows.append(
            (
                villager_id,
                str(v.get("name") or ""),
                str(v.get("name_ko") or ""),
                str(v.get("name_en") or ""),
                str(v.get("species") or ""),
                str(v.get("species_ko") or ""),
                str(v.get("personality") or ""),
                str(v.get("personality_ko") or ""),
                str(v.get("sub_personality") or ""),
                str(v.get("gender") or ""),
                str(v.get("hobby") or ""),
                str(v.get("sign") or ""),
                str(v.get("birthday") or ""),
                str(v.get("catchphrase") or ""),
                str(v.get("catchphrase_ko") or ""),
                str(v.get("saying") or ""),
                str(v.get("saying_ko") or ""),
                str(v.get("image_uri") or ""),
                str(v.get("icon_uri") or ""),
                str(v.get("photo_url") or ""),
                str(v.get("house_exterior_url") or ""),
                str(v.get("house_interior_url") or ""),
                json.dumps(v, ensure_ascii=False),
                built_at,
            )
        )

    conn.executemany(
        """
        INSERT OR REPLACE INTO villagers (
            villager_id, name, name_ko, name_en, species, species_ko, personality, personality_ko,
            sub_personality, gender, hobby, sign, birthday, catchphrase, catchphrase_ko, saying, saying_ko,
            image_url, icon_url, photo_url, house_exterior_url, house_interior_url, raw_json, built_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def _write_version(conn, built_at: str, item_count: int, variation_count: int, villager_count: int) -> None:
    meta = {
        "built_at_utc": built_at,
        "catalog_types": str(len(CATALOG_TYPES)),
        "catalog_items": str(item_count),
        "catalog_variations": str(variation_count),
        "villagers": str(villager_count),
        "builder": "scripts/build_content_db.py",
    }
    conn.executemany(
        "INSERT INTO content_version (key, value) VALUES (?, ?)",
        list(meta.items()),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build local content.db from snapshot/local data.")
    parser.add_argument(
        "--refresh-snapshot",
        action="store_true",
        help="Recreate data/content_full_snapshot.json from current loaders before build.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    built_at = datetime.now(timezone.utc).isoformat()
    snapshot = _load_or_create_snapshot(refresh=bool(args.refresh_snapshot))
    with get_content_db() as conn:
        _exec_schema(conn)
        _clear_tables(conn)
        item_count, variation_count = _insert_catalog(conn, built_at, snapshot)
        villager_count = _insert_villagers(conn, built_at, snapshot)
        _write_version(conn, built_at, item_count, variation_count, villager_count)
        conn.commit()
    print(f"built_at={built_at}")
    print(f"snapshot={SNAPSHOT_PATH}")
    print(f"snapshot_refreshed={bool(args.refresh_snapshot)}")
    print(f"catalog_items={item_count}")
    print(f"catalog_variations={variation_count}")
    print(f"villagers={villager_count}")


if __name__ == "__main__":
    main()
