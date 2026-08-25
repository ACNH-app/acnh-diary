import { apiGet, apiPost } from "./client";

export type CatalogType = "fish" | "bugs" | "sea" | "fossils" | "items" | "recipes";

export type CatalogItem = {
  id: string;
  number?: number;
  name_ko: string;
  name_en: string;
  category?: string;
  image_url?: string;
  owned: boolean;
  donated: boolean;
  quantity?: number;
  variation_total?: number;
  variation_owned_count?: number;
};

export type CatalogResponse = {
  count: number;
  total_count: number;
  page: number;
  page_size: number;
  has_more: boolean;
  items: CatalogItem[];
};

export type CatalogState = {
  owned?: boolean;
  donated?: boolean;
  quantity?: number;
};

export type CatalogDetail = {
  item: CatalogItem;
  summary: {
    name_en: string;
    image_url: string;
    category: string;
    event_type: string;
    date: string;
    not_for_sale: boolean;
    variation_total: number;
  };
  fields: Array<{ label: string; value: string }>;
  variations: Array<{ id: string; name?: string; owned: boolean; quantity: number }>;
};

export function getCatalog(catalogType: CatalogType, islandId: number, query = "", owned?: boolean, sortOrder = "asc") {
  const params = new URLSearchParams({ page: "1", page_size: "60", sort_by: "name", sort_order: sortOrder });
  if (query.trim()) params.set("q", query.trim());
  if (owned !== undefined) params.set("owned", String(owned));
  return apiGet<CatalogResponse>(`/api/catalog/${catalogType}?${params.toString()}`, {
    "X-Island-Id": String(islandId),
  });
}

export function updateCatalogState(catalogType: CatalogType, itemId: string, islandId: number, state: CatalogState) {
  return apiPost<CatalogItem>(`/api/catalog/${catalogType}/${encodeURIComponent(itemId)}/state`, state, {
    "X-Island-Id": String(islandId),
  });
}

export function getCatalogDetail(catalogType: CatalogType, itemId: string, islandId: number) {
  return apiGet<CatalogDetail>(`/api/catalog/${catalogType}/${encodeURIComponent(itemId)}/detail`, {
    "X-Island-Id": String(islandId),
  });
}
