import { apiGet, apiPost } from "./client";

export type Villager = {
  id: string;
  name: string;
  name_ko: string;
  name_en: string;
  personality: string;
  species: string;
  subtype: string;
  photo_url: string;
  icon_uri: string;
  image_uri: string;
  liked: boolean;
  on_island: boolean;
  camping_visited: boolean;
  former_resident: boolean;
  island_order: number;
};

export type VillagerResponse = { count: number; items: Villager[] };

export type VillagerFilters = {
  q?: string;
  personality?: string;
  species?: string;
  subtype?: string;
  liked?: boolean;
  on_island?: boolean;
  former_resident?: boolean;
};

export type VillagerState = Partial<Pick<Villager, "liked" | "on_island" | "camping_visited" | "former_resident">>;

export type VillagerMeta = {
  personalities: Array<{ en: string; ko: string }>;
  species: Array<{ en: string; ko: string }>;
  subtypes: Array<{ en: string; ko: string }>;
};

export function getVillagerMeta() {
  return apiGet<VillagerMeta>("/api/meta");
}

export function getVillagers(islandId: number, filters: VillagerFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  const query = params.toString();
  return apiGet<VillagerResponse>(`/api/villagers${query ? `?${query}` : ""}`, { "X-Island-Id": String(islandId) });
}

export function updateVillagerState(islandId: number, villagerId: string, state: VillagerState) {
  return apiPost<Villager>(`/api/villagers/${encodeURIComponent(villagerId)}/state`, state, { "X-Island-Id": String(islandId) });
}
