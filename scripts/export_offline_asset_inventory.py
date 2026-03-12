from __future__ import annotations

import csv
import sqlite3
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CONTENT_DB = BASE_DIR / 'content.db'
MANIFEST_DIR = BASE_DIR / 'data' / 'offline_asset_manifests'


def _query_rows(conn: sqlite3.Connection, query: str) -> list[dict[str, str]]:
    cur = conn.execute(query)
    columns = [row[0] for row in cur.description]
    return [dict(zip(columns, row)) for row in cur.fetchall()]


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not CONTENT_DB.exists():
        raise SystemExit(f'missing content db: {CONTENT_DB}')

    with sqlite3.connect(CONTENT_DB) as conn:
        catalog_rows = _query_rows(
            conn,
            """
            SELECT catalog_type, item_id, image_url
            FROM catalog_items
            WHERE image_url LIKE 'http%'
            ORDER BY catalog_type, item_id
            """,
        )
        variation_rows = _query_rows(
            conn,
            """
            SELECT catalog_type, item_id, variation_id, image_url
            FROM catalog_variations
            WHERE image_url LIKE 'http%'
            ORDER BY catalog_type, item_id, variation_id
            """,
        )
        villager_rows = _query_rows(
            conn,
            """
            SELECT villager_id, image_url, icon_url, photo_url, house_exterior_url, house_interior_url
            FROM villagers
            ORDER BY villager_id
            """,
        )

    _write_csv(
        MANIFEST_DIR / 'catalog_remote_images.csv',
        catalog_rows,
        ['catalog_type', 'item_id', 'image_url'],
    )
    _write_csv(
        MANIFEST_DIR / 'catalog_variation_remote_images.csv',
        variation_rows,
        ['catalog_type', 'item_id', 'variation_id', 'image_url'],
    )
    _write_csv(
        MANIFEST_DIR / 'villager_remote_images.csv',
        villager_rows,
        [
            'villager_id',
            'image_url',
            'icon_url',
            'photo_url',
            'house_exterior_url',
            'house_interior_url',
        ],
    )

    unique_urls: set[str] = {row['image_url'] for row in catalog_rows if row['image_url']}
    unique_urls.update(row['image_url'] for row in variation_rows if row['image_url'])
    for row in villager_rows:
        for key in (
            'image_url',
            'icon_url',
            'photo_url',
            'house_exterior_url',
            'house_interior_url',
        ):
            if row[key]:
                unique_urls.add(row[key])

    catalog_counter = Counter(row['catalog_type'] for row in catalog_rows)
    print(f'catalog_rows={len(catalog_rows)}')
    for catalog_type, count in sorted(catalog_counter.items()):
        print(f'catalog_type={catalog_type} remote_images={count}')
    print(f'variation_rows={len(variation_rows)}')
    print(f'villager_rows={len(villager_rows)}')
    print(f'combined_unique_urls={len(unique_urls)}')


if __name__ == '__main__':
    main()
