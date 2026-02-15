import { getJSON, updateCatalogState, updateVillagerState } from "./api.js";
import {
  catalogExtraSelect,
  catalogArtGuideBtn,
  catalogSearchInput,
  catalogSortBySelect,
  catalogSortOrderSelect,
  catalogTabs,
  personalitySelect,
  searchInput,
  sortBySelect,
  sortOrderSelect,
  speciesSelect,
} from "./dom.js";
import {
  fillSelect,
  renderCatalog,
  renderSubCategoryTabs,
  renderVillagers,
} from "./render.js";
import { state } from "./state.js";
import { sortVillagers, toQuery } from "./utils.js";

/**
 * Data loading/orchestration controller for villagers and catalog.
 * @param {{
 *   onSyncDetailNav?: () => void,
 *   onOpenDetail?: (itemId: string) => void,
 *   onOpenVillagerDetail?: (villager: any) => void
 * }} [handlers]
 */
export function createDataController({ onSyncDetailNav, onOpenDetail, onOpenVillagerDetail } = {}) {
  const safeSyncDetailNav = () => {
    if (onSyncDetailNav) onSyncDetailNav();
  };
  const safeOpenDetail = (itemId) => {
    if (onOpenDetail) onOpenDetail(itemId);
  };
  const safeOpenVillagerDetail = (villager) => {
    if (onOpenVillagerDetail) onOpenVillagerDetail(villager);
  };
  function needsVillagerReloadAfterToggle(payload) {
    if (!payload || typeof payload !== "object") return false;
    if (state.activeVillagerTab === "liked" && payload.liked === false) return true;
    if (state.activeVillagerTab === "island" && payload.on_island === false) return true;
    if (state.activeVillagerTab === "former" && payload.former_resident === false) return true;
    return false;
  }

  function needsCatalogReloadAfterToggle(nextOwned) {
    if (state.activeCatalogTab === "owned" && nextOwned === false) return true;
    if (state.activeCatalogTab === "unowned" && nextOwned === true) return true;
    return false;
  }

  /** Load villager filter metadata into select boxes. */
  async function loadVillagerMeta() {
    const meta = await getJSON("/api/meta");

    meta.personalities.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.en;
      opt.textContent = `${p.ko} (${p.en})`;
      personalitySelect.appendChild(opt);
    });

    const sortedSpecies = [...meta.species].sort((a, b) =>
      (a.ko || a.en).localeCompare(b.ko || b.en, "ko")
    );

    sortedSpecies.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.en;
      opt.textContent = `${s.ko} (${s.en})`;
      speciesSelect.appendChild(opt);
    });
  }

  /** Load catalog metadata once per catalog type and cache it in state. */
  async function ensureCatalogMeta(catalogType) {
    if (state.catalogMetaCache[catalogType]) return state.catalogMetaCache[catalogType];
    const meta = await getJSON(`/api/catalog/${catalogType}/meta`);
    state.catalogMetaCache[catalogType] = meta;
    return meta;
  }

  /** Apply catalog metadata to filter controls and sub-category tabs. */
  async function applyCatalogMeta(catalogType) {
    const meta = await ensureCatalogMeta(catalogType);
    catalogSearchInput.placeholder = `${meta.label} 이름 검색 (한글/영문)`;
    const prevExtraValue = catalogExtraSelect.value;
    const prevExtraType = catalogExtraSelect.dataset.extraType || "";
    const subCategoryRows =
      catalogType === "art" ? meta.authenticity_types || [] : meta.categories || [];
    renderSubCategoryTabs(catalogType, subCategoryRows, {
      onCategoryChange: () => {
        loadCurrentModeData().catch((err) => console.error(err));
      },
    });

    catalogExtraSelect.classList.add("hidden");
    catalogExtraSelect.innerHTML = "";
    catalogExtraSelect.dataset.extraType = "";
    if (catalogArtGuideBtn) {
      catalogArtGuideBtn.classList.toggle("hidden", catalogType !== "art");
    }

    if (catalogType === "clothing") {
      fillSelect(
        catalogExtraSelect,
        "스타일 전체",
        meta.styles || [],
        prevExtraType === "style" ? prevExtraValue : ""
      );
      catalogExtraSelect.dataset.extraType = "style";
      catalogExtraSelect.classList.remove("hidden");
    }

    if (catalogType === "events") {
      const rows = (meta.event_types || []).map((x) => ({ en: x, ko: x }));
      fillSelect(
        catalogExtraSelect,
        "이벤트 타입 전체",
        rows,
        prevExtraType === "event_type" ? prevExtraValue : ""
      );
      catalogExtraSelect.dataset.extraType = "event_type";
      catalogExtraSelect.classList.remove("hidden");
    }
    const ownedTab = catalogTabs.find((el) => el.dataset.tab === "owned");
    if (ownedTab) ownedTab.textContent = `${meta.status_label}만`;
  }

  /** Fetch and render villagers based on current filters/sort/tab state. */
  async function loadVillagers() {
    const tabFilters = { liked: null, on_island: null, former_resident: null };
    if (state.activeVillagerTab === "liked") tabFilters.liked = true;
    if (state.activeVillagerTab === "island") tabFilters.on_island = true;
    if (state.activeVillagerTab === "former") tabFilters.former_resident = true;

    const query = toQuery({
      q: searchInput.value.trim(),
      personality: personalitySelect.value,
      species: speciesSelect.value,
      ...tabFilters,
    });

    const data = await getJSON(`/api/villagers?${query}`);
    renderVillagers(sortVillagers(data.items, sortBySelect.value || "name", sortOrderSelect.value || "asc"), {
      onSyncDetailNav: safeSyncDetailNav,
      onToggleState: async (villagerId, payload) => {
        await updateVillagerState(villagerId, payload);
        if (needsVillagerReloadAfterToggle(payload)) {
          await loadCurrentModeData();
        }
      },
      onOpenDetail: (villager) => {
        safeOpenVillagerDetail(villager);
      },
    });
  }

  /** Load first catalog page for the given type. */
  async function loadCatalog(catalogType) {
    return loadCatalogPage(catalogType, { append: false });
  }

  /** Fetch and render one catalog page; append if requested. */
  async function loadCatalogPage(catalogType, { append = false } = {}) {
    await applyCatalogMeta(catalogType);
    const meta = state.catalogMetaCache[catalogType] || { status_label: "보유" };
    const nextPage = append ? state.catalogPage + 1 : 1;

    const queryParams = {
      q: catalogSearchInput.value.trim(),
      category: catalogType === "art" ? "" : state.activeSubCategory,
      fake_state: catalogType === "art" ? state.activeSubCategory : "",
      owned: state.activeCatalogTab === "owned" ? true : state.activeCatalogTab === "unowned" ? false : null,
      sort_by: catalogSortBySelect.value,
      sort_order: catalogSortOrderSelect.value,
      page: nextPage,
      page_size: state.catalogPageSize,
    };

    const extraType = catalogExtraSelect.dataset.extraType;
    if (!catalogExtraSelect.classList.contains("hidden") && catalogExtraSelect.value) {
      queryParams[extraType] = catalogExtraSelect.value;
    }

    const query = toQuery(queryParams);
    const data = await getJSON(`/api/catalog/${catalogType}?${query}`);
    state.catalogPage = Number(data.page || nextPage);
    renderCatalog(
      data.items || [],
      meta.status_label || "보유",
      {
        append,
        totalCount: Number(data.total_count ?? data.count ?? 0),
        hasMore: Boolean(data.has_more),
      },
      {
        onSyncDetailNav: safeSyncDetailNav,
        onToggleOwned: async (itemId, owned) => {
          await updateCatalogState(state.activeMode, itemId, { owned });
          const target = state.renderedCatalogItems.find((x) => x.id === itemId);
          if (target) target.owned = owned;
          if (needsCatalogReloadAfterToggle(owned)) {
            await loadCurrentModeData();
          }
        },
        onOpenDetail: (itemId) => {
          safeOpenDetail(itemId);
        },
      }
    );
  }

  /** Dispatch loading based on current active mode (villagers/catalog). */
  async function loadCurrentModeData() {
    if (state.activeMode === "home") return;
    if (state.activeMode === "villagers") {
      await loadVillagers();
      return;
    }
    await loadCatalog(state.activeMode);
  }

  /** Debounced loader for text inputs. */
  function scheduleLoad() {
    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(() => {
      loadCurrentModeData().catch((err) => console.error(err));
    }, 220);
  }

  /** Deferred refresh used after detail variation toggles/batch updates. */
  function scheduleCatalogRefresh(delayMs = 400) {
    clearTimeout(state.catalogRefreshTimer);
    state.catalogRefreshTimer = setTimeout(() => {
      if (state.activeMode === "villagers") return;
      loadCurrentModeData().catch((err) => console.error(err));
    }, delayMs);
  }

  return {
    loadVillagerMeta,
    loadCatalogPage,
    loadCurrentModeData,
    scheduleCatalogRefresh,
    scheduleLoad,
  };
}
