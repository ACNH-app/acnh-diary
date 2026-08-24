import { apiGet } from "./client";

export type NavItem = {
  key: string;
  label: string;
  href?: string;
  icon?: string;
};

export type HomeSummary = {
  island?: {
    island_name?: string;
    nickname?: string;
    representative_fruit?: string;
    representative_flower?: string;
    hemisphere?: string;
  };
  catalog?: {
    owned?: number;
    total?: number;
    donated?: number;
  };
  villagers?: {
    on_island?: number;
    liked?: number;
    total?: number;
  };
};

export function getNav() {
  return apiGet<NavItem[]>("/api/nav");
}

export function getHomeSummary() {
  return apiGet<HomeSummary>("/api/home/summary");
}
