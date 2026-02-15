export async function getJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "요청 실패");
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

export function updateCatalogState(catalogType, itemId, payload) {
  return postJSON(`/api/catalog/${catalogType}/${itemId}/state`, payload);
}

export function updateCatalogVariationState(catalogType, itemId, variationId, payload) {
  return postJSON(`/api/catalog/${catalogType}/${itemId}/variations/${variationId}/state`, payload);
}

export function updateCatalogVariationStateBatch(catalogType, itemId, items) {
  return postJSON(`/api/catalog/${catalogType}/${itemId}/variations/state`, { items });
}
