import {
  detailBackdrop,
  detailCloseBtn,
  detailFields,
  detailImage,
  detailModal,
  detailNavHint,
  detailNextBtn,
  detailPrevBtn,
  detailRawFields,
  detailSourceHint,
  detailTitle,
  detailVariations,
  variationMarkAllBtn,
  variationUnmarkAllBtn,
} from "./dom.js";
import { state } from "./state.js";

/**
 * Detail modal controller for catalog item details and variation ownership state.
 * @param {{
 *   getJSON: (url: string, options?: RequestInit) => Promise<any>,
 *   updateCatalogVariationState: (catalogType: string, itemId: string, variationId: string, payload: { owned: boolean }) => Promise<any>,
 *   updateCatalogVariationStateBatch: (catalogType: string, itemId: string, items: Array<{ variation_id: string, owned: boolean }>) => Promise<any>,
 *   scheduleCatalogRefresh: (delayMs?: number) => void
 * }} deps
 */
export function createDetailController({
  getJSON,
  updateCatalogVariationState,
  updateCatalogVariationStateBatch,
  scheduleCatalogRefresh,
}) {
  function getDetailModeCache(mode) {
    if (!state.detailCacheByMode[mode]) state.detailCacheByMode[mode] = new Map();
    return state.detailCacheByMode[mode];
  }

  function getActiveDetailIndex() {
    if (!state.activeDetailItemId || !state.activeCatalogItemIds.length) return -1;
    return state.activeCatalogItemIds.indexOf(state.activeDetailItemId);
  }

  function syncDetailNavState() {
    const isOpen = !detailModal.classList.contains("hidden");
    const hasItems = state.activeCatalogItemIds.length > 0;
    const idx = getActiveDetailIndex();
    const canPrev = isOpen && hasItems && idx > 0;
    const canNext = isOpen && hasItems && idx >= 0 && idx < state.activeCatalogItemIds.length - 1;

    if (detailPrevBtn) detailPrevBtn.disabled = !canPrev;
    if (detailNextBtn) detailNextBtn.disabled = !canNext;

    if (detailNavHint) {
      detailNavHint.textContent = isOpen && idx >= 0 ? `${idx + 1} / ${state.activeCatalogItemIds.length}` : "";
    }
  }

  function closeDetailModal() {
    detailModal.classList.add("hidden");
    detailModal.setAttribute("aria-hidden", "true");
    state.activeDetailItemId = "";
    state.activeDetailVariations = [];
    state.activeDetailPayload = null;
    syncDetailNavState();
  }

  async function fetchCatalogDetail(itemId, { force = false } = {}) {
    const mode = state.activeMode;
    const cache = getDetailModeCache(mode);
    if (!force && cache.has(itemId)) return cache.get(itemId);
    const detail = await getJSON(`/api/catalog/${mode}/${itemId}/detail`);
    cache.set(itemId, detail);
    return detail;
  }

  function prefetchNeighborDetails() {
    if (!state.activeMode || state.activeMode === "villagers") return;
    const mode = state.activeMode;
    const cache = getDetailModeCache(mode);
    const idx = getActiveDetailIndex();
    if (idx < 0) return;
    const targets = [state.activeCatalogItemIds[idx - 1], state.activeCatalogItemIds[idx + 1]].filter(Boolean);
    targets.forEach((id) => {
      if (cache.has(id)) return;
      getJSON(`/api/catalog/${mode}/${id}/detail`)
        .then((payload) => cache.set(id, payload))
        .catch((err) => console.error(err));
    });
  }

  function openDetailModal(payload) {
    state.activeDetailPayload = payload;
    const summary = payload.summary || {};
    detailTitle.textContent = summary.name_en || payload.item?.name_en || "상세 정보";
    detailImage.src = summary.image_url || "/static/no-image.svg";
    detailImage.onerror = () => {
      detailImage.src = "/static/no-image.svg";
    };
    detailSourceHint.textContent = payload.from_single_endpoint
      ? "single API 상세 데이터"
      : "목록 API 상세 데이터(대체)";

    detailFields.innerHTML = "";
    (payload.fields || []).forEach((field) => {
      const row = document.createElement("p");
      row.className = "detail-field";
      row.textContent = `${field.label}: ${field.value}`;
      detailFields.appendChild(row);
    });

    detailVariations.innerHTML = "";
    state.activeDetailVariations = payload.variations || [];
    const variations = payload.variations || [];
    if (!variations.length) {
      const empty = document.createElement("p");
      empty.className = "detail-empty";
      empty.textContent = "변형 정보가 없습니다.";
      detailVariations.appendChild(empty);
    } else {
      variations.forEach((v) => {
        const box = document.createElement("article");
        box.className = `variation-card ${v.owned ? "owned" : ""}`;
        const img = document.createElement("img");
        img.className = "variation-image";
        img.src = v.image_url || "/static/no-image.svg";
        img.alt = v.label || "variation";
        img.onerror = () => {
          img.src = "/static/no-image.svg";
        };

        const title = document.createElement("p");
        title.className = "variation-title";
        title.textContent = v.label || "-";

        const meta = document.createElement("p");
        meta.className = "variation-meta";
        const parts = [];
        if (v.color1) parts.push(`색1: ${v.color1}`);
        if (v.color2) parts.push(`색2: ${v.color2}`);
        if (v.pattern) parts.push(`패턴: ${v.pattern}`);
        if (v.price) parts.push(`가격: ${v.price}`);
        meta.textContent = parts.join(" | ") || "-";

        const stateRow = document.createElement("p");
        stateRow.className = "variation-state";
        stateRow.textContent = v.owned ? "보유됨" : "미보유";

        box.addEventListener("click", async () => {
          const nextOwned = !Boolean(v.owned);
          try {
            await updateCatalogVariationState(state.activeMode, state.activeDetailItemId, v.id, {
              owned: nextOwned,
            });
            v.owned = nextOwned;
            stateRow.textContent = nextOwned ? "보유됨" : "미보유";
            box.classList.toggle("owned", nextOwned);
            state.activeDetailVariations = state.activeDetailVariations.map((x) =>
              x.id === v.id ? { ...x, owned: nextOwned } : x
            );
            if (state.activeDetailPayload && Array.isArray(state.activeDetailPayload.variations)) {
              state.activeDetailPayload.variations = state.activeDetailPayload.variations.map((x) =>
                x.id === v.id ? { ...x, owned: nextOwned } : x
              );
              getDetailModeCache(state.activeMode).set(state.activeDetailItemId, state.activeDetailPayload);
            }
            scheduleCatalogRefresh(250);
          } catch (err) {
            console.error(err);
          }
        });

        box.appendChild(img);
        box.appendChild(title);
        box.appendChild(meta);
        box.appendChild(stateRow);
        detailVariations.appendChild(box);
      });
    }

    detailRawFields.innerHTML = "";
    (payload.raw_fields || []).forEach((row) => {
      const p = document.createElement("p");
      p.className = "raw-field";
      p.textContent = `${row.key}: ${row.value}`;
      detailRawFields.appendChild(p);
    });

    detailModal.classList.remove("hidden");
    detailModal.setAttribute("aria-hidden", "false");
    syncDetailNavState();
  }

  async function openCatalogDetail(itemId, options = {}) {
    if (!state.activeMode || state.activeMode === "villagers") return;
    state.activeDetailItemId = itemId;
    const detail = await fetchCatalogDetail(itemId, options);
    openDetailModal(detail);
    prefetchNeighborDetails();
  }

  async function moveDetail(offset) {
    if (detailModal.classList.contains("hidden")) return;
    const idx = getActiveDetailIndex();
    if (idx < 0) return;
    const nextIdx = idx + offset;
    if (nextIdx < 0 || nextIdx >= state.activeCatalogItemIds.length) return;
    await openCatalogDetail(state.activeCatalogItemIds[nextIdx]);
  }

  function bindEvents() {
    detailBackdrop.addEventListener("click", closeDetailModal);
    detailCloseBtn.addEventListener("click", closeDetailModal);
    if (detailPrevBtn) {
      detailPrevBtn.addEventListener("click", () => {
        moveDetail(-1).catch((err) => console.error(err));
      });
    }
    if (detailNextBtn) {
      detailNextBtn.addEventListener("click", () => {
        moveDetail(1).catch((err) => console.error(err));
      });
    }
    variationMarkAllBtn.addEventListener("click", async () => {
      if (!state.activeDetailItemId || !state.activeDetailVariations.length) return;
      try {
        await updateCatalogVariationStateBatch(
          state.activeMode,
          state.activeDetailItemId,
          state.activeDetailVariations.map((v) => ({ variation_id: v.id, owned: true }))
        );
        await openCatalogDetail(state.activeDetailItemId, { force: true });
        scheduleCatalogRefresh(250);
      } catch (err) {
        console.error(err);
      }
    });
    variationUnmarkAllBtn.addEventListener("click", async () => {
      if (!state.activeDetailItemId || !state.activeDetailVariations.length) return;
      try {
        await updateCatalogVariationStateBatch(
          state.activeMode,
          state.activeDetailItemId,
          state.activeDetailVariations.map((v) => ({ variation_id: v.id, owned: false }))
        );
        await openCatalogDetail(state.activeDetailItemId, { force: true });
        scheduleCatalogRefresh(250);
      } catch (err) {
        console.error(err);
      }
    });
    document.addEventListener("keydown", (e) => {
      const isOpen = !detailModal.classList.contains("hidden");
      if (e.key === "Escape" && isOpen) {
        closeDetailModal();
        return;
      }
      if (!isOpen) return;
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        moveDetail(-1).catch((err) => console.error(err));
        return;
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        moveDetail(1).catch((err) => console.error(err));
      }
    });
  }

  return {
    bindEvents,
    closeDetailModal,
    moveDetail,
    openCatalogDetail,
    syncDetailNavState,
  };
}
