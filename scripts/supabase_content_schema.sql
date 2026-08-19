create table if not exists public.catalog_items (
  catalog_type text not null,
  item_id text not null,
  name text not null default '',
  name_ko text not null default '',
  name_en text not null default '',
  category text not null default '',
  category_ko text not null default '',
  source text not null default '',
  source_ko text not null default '',
  source_notes text not null default '',
  source_notes_ko text not null default '',
  buy integer not null default 0,
  sell integer not null default 0,
  number integer not null default 0,
  event_type text not null default '',
  date text not null default '',
  image_url text not null default '',
  not_for_sale boolean not null default false,
  variation_total integer not null default 0,
  status_label text not null default '',
  raw_json jsonb not null default '{}'::jsonb,
  item_json jsonb not null default '{}'::jsonb,
  built_at_utc timestamptz,
  primary key (catalog_type, item_id)
);

create index if not exists idx_catalog_items_type_category
on public.catalog_items (catalog_type, category);

create index if not exists idx_catalog_items_type_name
on public.catalog_items (catalog_type, name_ko, name_en);

create table if not exists public.catalog_variations (
  catalog_type text not null,
  item_id text not null,
  variation_id text not null,
  label text not null default '',
  color1 text not null default '',
  color2 text not null default '',
  pattern text not null default '',
  source text not null default '',
  source_ko text not null default '',
  source_notes text not null default '',
  source_notes_ko text not null default '',
  price integer not null default 0,
  image_url text not null default '',
  raw_json jsonb not null default '{}'::jsonb,
  built_at_utc timestamptz,
  primary key (catalog_type, item_id, variation_id)
);

create table if not exists public.villagers (
  villager_id text primary key,
  name text not null default '',
  name_ko text not null default '',
  name_en text not null default '',
  species text not null default '',
  species_ko text not null default '',
  personality text not null default '',
  personality_ko text not null default '',
  sub_personality text not null default '',
  gender text not null default '',
  hobby text not null default '',
  sign text not null default '',
  birthday text not null default '',
  catchphrase text not null default '',
  catchphrase_ko text not null default '',
  saying text not null default '',
  saying_ko text not null default '',
  image_url text not null default '',
  icon_url text not null default '',
  photo_url text not null default '',
  house_exterior_url text not null default '',
  house_interior_url text not null default '',
  raw_json jsonb not null default '{}'::jsonb,
  built_at_utc timestamptz
);

create table if not exists public.catalog_meta (
  catalog_type text primary key,
  status_label text not null default '',
  item_count integer not null default 0,
  variation_count integer not null default 0,
  built_at_utc timestamptz
);

create table if not exists public.content_version (
  key text primary key,
  value text not null default ''
);

create table if not exists public.recipe_tags (
  tag_key text primary key,
  tag_type text not null default '',
  name_ko text not null default '',
  name_en text not null default '',
  sort_order integer not null default 0,
  is_system boolean not null default true,
  built_at_utc timestamptz
);

create table if not exists public.recipe_tag_links (
  recipe_item_id text not null,
  tag_key text not null references public.recipe_tags(tag_key) on delete cascade,
  built_at_utc timestamptz,
  primary key (recipe_item_id, tag_key)
);
