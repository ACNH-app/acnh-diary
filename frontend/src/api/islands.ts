import { apiGet, apiPost, apiRequest } from "./client";

export type Island = {
  id: number;
  name: string;
};

export function getIslands() {
  return apiGet<Island[]>("/api/islands");
}

export type IslandProfile = {
  island_id: number;
  island_name: string;
  nickname: string;
  representative_fruit: string;
  representative_flower: string;
  birthday: string;
  hemisphere: "north" | "south";
  time_travel_enabled: boolean;
  game_datetime: string;
};

export type IslandProfileInput = Omit<IslandProfile, "island_id">;

export function createIsland(name: string) {
  return apiPost<Island>("/api/islands", { name });
}

export function deleteIsland(islandId: number) {
  return apiRequest<{ deleted: boolean; id: number }>(`/api/islands/${islandId}`, "DELETE");
}

export function getIslandProfile(islandId: number) {
  return apiGet<IslandProfile>("/api/profile", { "X-Island-Id": String(islandId) });
}

export function updateIslandProfile(islandId: number, profile: IslandProfileInput) {
  return apiPost<IslandProfile>("/api/profile", profile, { "X-Island-Id": String(islandId) });
}
