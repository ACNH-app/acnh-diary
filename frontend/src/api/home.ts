import { apiGet } from "./client";

export type NavItem = {
  key: string;
  label: string;
  href?: string;
  icon?: string;
};

export type HomeSummary = {
  effective_datetime: string;
  season_ko: string;
  zodiac_ko: string;
  upcoming_events: Array<{ id: string; name_ko: string; name_en: string; date: string; delta_days: number }>;
  nook_shopping_today: Array<{ id: string; name_ko: string; name_en: string; date: string; delta_days: number }>;
  seasonal_recipes_now: string[];
  blooming_shrubs_now: string[];
};

export type Creature = {
  id: string;
  catalog_type: "bugs" | "fish" | "sea";
  number: number;
  name_ko: string;
  name_en: string;
  icon_url: string;
  location: string;
  time: string;
  months: string;
  owned: boolean;
  donated: boolean;
};

export type CreatureResponse = {
  effective_datetime: string;
  hemisphere: "north" | "south";
  catalog_type: string;
  count: number;
  counts_by_type: Record<string, number>;
  items: Creature[];
};

export function getNav() {
  return apiGet<NavItem[]>("/api/nav");
}

export function getHomeSummary(islandId?: number) {
  return apiGet<HomeSummary>(
    "/api/home/summary",
    islandId ? { "X-Island-Id": String(islandId) } : undefined,
  );
}

export function getHomeCreaturesNow(islandId: number) {
  return apiGet<CreatureResponse>(
    "/api/home/creatures-now?catalog_type=all&owned=false",
    { "X-Island-Id": String(islandId) },
  );
}
