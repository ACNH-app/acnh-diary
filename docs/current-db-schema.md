# 현재 DB 스키마 정리

기준: 로컬 프로젝트 루트의 `app.db`, `content.db`

## 1) 상태 DB (`app.db`)

사용자 상태(보유/기증/수량), 섬 프로필, 플레이어, 캘린더 데이터를 저장한다.

### 테이블 목록

- `villager_state`
- `clothing_state`
- `catalog_state`
- `catalog_variation_state`
- `island_profile`
- `player_profile`
- `calendar_entry`

### 스키마

```sql
CREATE TABLE villager_state (
    villager_id TEXT PRIMARY KEY,
    liked INTEGER NOT NULL DEFAULT 0,
    on_island INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
, former_resident INTEGER NOT NULL DEFAULT 0, island_order INTEGER NOT NULL DEFAULT 0);

CREATE TABLE clothing_state (
    item_id TEXT PRIMARY KEY,
    owned INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE catalog_state (
    catalog_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    owned INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, quantity INTEGER NOT NULL DEFAULT 0, donated INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (catalog_type, item_id)
);

CREATE TABLE catalog_variation_state (
    catalog_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    variation_id TEXT NOT NULL,
    owned INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, quantity INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (catalog_type, item_id, variation_id)
);

CREATE TABLE island_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    island_name TEXT NOT NULL DEFAULT '',
    nickname TEXT NOT NULL DEFAULT '',
    representative_fruit TEXT NOT NULL DEFAULT '',
    representative_flower TEXT NOT NULL DEFAULT '',
    hemisphere TEXT NOT NULL DEFAULT 'north',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
, birthday TEXT NOT NULL DEFAULT '', time_travel_enabled INTEGER NOT NULL DEFAULT 0, game_datetime TEXT NOT NULL DEFAULT '');

CREATE TABLE player_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT '',
    birthday TEXT NOT NULL DEFAULT '',
    is_main INTEGER NOT NULL DEFAULT 0,
    is_sub INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE calendar_entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_date TEXT NOT NULL,
    npc_name TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    checked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## 2) 콘텐츠 DB (`content.db`)

카탈로그/주민 원본+가공 데이터(한글 필드 포함), 레시피 태그를 저장한다.

### 테이블 목록

- `catalog_items`
- `catalog_meta`
- `catalog_variations`
- `content_version`
- `recipe_tags`
- `recipe_tag_links`
- `villagers`

### 스키마

```sql
CREATE TABLE catalog_items (
    catalog_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    name_ko TEXT NOT NULL DEFAULT '',
    name_en TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    category_ko TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    source_notes TEXT NOT NULL DEFAULT '',
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
    built_at_utc TEXT NOT NULL DEFAULT '', item_json TEXT NOT NULL DEFAULT '{}', source_ko TEXT NOT NULL DEFAULT '', source_notes_ko TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (catalog_type, item_id)
);
CREATE INDEX idx_catalog_items_type_category
ON catalog_items (catalog_type, category);
CREATE INDEX idx_catalog_items_type_name
ON catalog_items (catalog_type, name_ko, name_en);
CREATE INDEX idx_catalog_items_type_source
ON catalog_items (catalog_type, source);

CREATE TABLE catalog_variations (
    catalog_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    variation_id TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    color1 TEXT NOT NULL DEFAULT '',
    color2 TEXT NOT NULL DEFAULT '',
    pattern TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    source_notes TEXT NOT NULL DEFAULT '',
    price INTEGER NOT NULL DEFAULT 0,
    image_url TEXT NOT NULL DEFAULT '',
    raw_json TEXT NOT NULL DEFAULT '{}',
    built_at_utc TEXT NOT NULL DEFAULT '', source_ko TEXT NOT NULL DEFAULT '', source_notes_ko TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (catalog_type, item_id, variation_id)
);
CREATE INDEX idx_catalog_variations_item
ON catalog_variations (catalog_type, item_id);

CREATE TABLE villagers (
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
CREATE INDEX idx_villagers_name
ON villagers (name_ko, name_en);

CREATE TABLE content_version (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

CREATE TABLE catalog_meta (
    catalog_type TEXT PRIMARY KEY,
    status_label TEXT NOT NULL DEFAULT '',
    item_count INTEGER NOT NULL DEFAULT 0,
    variation_count INTEGER NOT NULL DEFAULT 0,
    built_at_utc TEXT NOT NULL DEFAULT ''
);

CREATE TABLE recipe_tags (
    tag_key TEXT PRIMARY KEY,
    tag_type TEXT NOT NULL DEFAULT '',
    name_ko TEXT NOT NULL DEFAULT '',
    name_en TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_system INTEGER NOT NULL DEFAULT 1,
    built_at_utc TEXT NOT NULL DEFAULT ''
);

CREATE TABLE recipe_tag_links (
    recipe_item_id TEXT NOT NULL,
    tag_key TEXT NOT NULL,
    built_at_utc TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (recipe_item_id, tag_key),
    FOREIGN KEY (tag_key) REFERENCES recipe_tags(tag_key)
);
CREATE INDEX idx_recipe_tag_links_tag_key
ON recipe_tag_links (tag_key, recipe_item_id);
```

## 3) 스키마 재확인 명령어

```bash
sqlite3 app.db ".schema"
sqlite3 content.db ".schema"
```
