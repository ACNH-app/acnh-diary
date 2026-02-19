export async function getJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text();
    const err = new Error(text || "요청 실패");
    err.status = res.status;
    throw err;
  }
  return res.json();
}

function postJSON(url, payload) {
  return getJSON(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateVillagerState(villagerId, payload) {
  return postJSON(`/api/villagers/${villagerId}/state`, payload);
}

export function updateIslandResidentOrder(villagerIds) {
  return postJSON("/api/villagers/island-order", { villager_ids: villagerIds });
}

export function getVillagers(params = {}) {
  const q = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    q.set(k, String(v));
  });
  const qs = q.toString();
  return getJSON(`/api/villagers${qs ? `?${qs}` : ""}`);
}

export function updateCatalogState(catalogType, itemId, payload) {
  return postJSON(`/api/catalog/${catalogType}/${itemId}/state`, payload);
}

export function updateCatalogStateBulk(catalogType, itemIds, owned) {
  return postJSON(`/api/catalog/${catalogType}/state/bulk`, {
    item_ids: itemIds,
    owned: Boolean(owned),
  });
}

export function updateCatalogVariationState(catalogType, itemId, variationId, payload) {
  return postJSON(`/api/catalog/${catalogType}/${itemId}/variations/${variationId}/state`, payload);
}

export function updateCatalogVariationStateBatch(catalogType, itemId, items) {
  return postJSON(`/api/catalog/${catalogType}/${itemId}/variations/state`, { items });
}

export function getIslandProfile() {
  return getJSON("/api/profile");
}

export function updateIslandProfile(payload) {
  return postJSON("/api/profile", payload);
}

export function getHomeSummary() {
  return getJSON("/api/home/summary");
}

export function getHomeIslandResidents() {
  return getJSON("/api/villagers?on_island=true");
}

export function getVillagerMeta() {
  return getJSON("/api/meta");
}

export function getPlayers() {
  return getJSON("/api/players");
}

export function savePlayer(payload) {
  return postJSON("/api/players", payload);
}

export function setMainPlayer(playerId) {
  return postJSON(`/api/players/${playerId}/main`, {});
}

export async function deletePlayer(playerId) {
  const res = await fetch(`/api/players/${playerId}`, { method: "DELETE" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "삭제 실패");
  }
  return res.json();
}

export function getCalendarEntries(month) {
  const q = new URLSearchParams({ month: String(month || "") });
  return getJSON(`/api/calendar?${q.toString()}`);
}

export function getCalendarAnnotations(month) {
  const q = new URLSearchParams({ month: String(month || "") });
  return getJSON(`/api/calendar/annotations?${q.toString()}`);
}

export function getCalendarEntriesByDate(date) {
  const q = new URLSearchParams({ date: String(date || "") });
  return getJSON(`/api/calendar/day?${q.toString()}`);
}

export function saveCalendarEntry(payload) {
  return postJSON("/api/calendar", payload);
}

export function setCalendarEntryChecked(entryId, checked) {
  return postJSON(`/api/calendar/${entryId}/checked`, { checked: Boolean(checked) });
}

export async function deleteCalendarEntry(entryId) {
  const res = await fetch(`/api/calendar/${entryId}`, { method: "DELETE" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "삭제 실패");
  }
  return res.json();
}
