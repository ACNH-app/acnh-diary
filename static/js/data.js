import { getJSON, updateCatalogState, updateCatalogStateBulk, updateVillagerState } from "./api.js";
import {
  catalogExtraSelect,
  catalogArtGuideBtn,
  catalogSearchInput,
  catalogSortBySelect,
  catalogSortOrderSelect,
  catalogTabs,
  personalitySelect,
  resultCount,
  searchInput,
  subtypeSelect,
  sortBySelect,
  sortOrderSelect,
  speciesSelect,
  villagerSubtypeTabs,
  villagerSpeciesTabs,
} from "./dom.js";
import {
  fillSelect,
  renderCatalog,
  renderSubCategoryTabs,
  renderVillagers,
} from "./render.js";
import { state } from "./state.js";
import { compareNamePriority, sortVillagers, toQuery } from "./utils.js";

/**
 * Data loading/orchestration controller for villagers and catalog.
 * @param {{
 *   onSyncDetailNav?: () => void,
 *   onOpenDetail?: (itemId: string) => void,
 *   onOpenVillagerDetail?: (villager: any) => void
 * }} [handlers]
 */
export function createDataController({ onSyncDetailNav, onOpenDetail, onOpenVillagerDetail } = {}) {
  const villagerQueryCache = new Map();
  const catalogSortInitialized = new Set();
  let catalogFetchSeq = 0;
  let catalogFetchAbortController = null;
  const getMusicCardMetaCache = () => {
    if (!state.musicCardMetaCache || typeof state.musicCardMetaCache !== "object") {
      state.musicCardMetaCache = {};
    }
    return state.musicCardMetaCache;
  };
  const getCatalogAllItemsCache = () => {
    if (!state.catalogAllItemsByMode || typeof state.catalogAllItemsByMode !== "object") {
      state.catalogAllItemsByMode = {};
    }
    return state.catalogAllItemsByMode;
  };
  const findCatalogCardById = (itemId) => {
    const id = String(itemId || "").trim();
    if (!id) return null;
    const cards = Array.from(document.querySelectorAll("#list .card"));
    return cards.find((el) => String(el?.dataset?.itemId || "").trim() === id) || null;
  };

  const safeSyncDetailNav = () => {
    if (onSyncDetailNav) onSyncDetailNav();
  };
  const safeOpenDetail = (itemId) => {
    if (onOpenDetail) onOpenDetail(itemId);
  };
  const safeOpenVillagerDetail = (villager) => {
    if (onOpenVillagerDetail) onOpenVillagerDetail(villager);
  };
  const textKoSort = (a, b) => compareNamePriority(a, b);
  const catalogName = (x) => x?.name_ko || x?.name || x?.name_en || "";
  const getExtraFilterValue = () => {
    if (catalogExtraSelect.classList.contains("hidden")) return "";
    return String(catalogExtraSelect.value || "").trim();
  };
  const getActiveOwnedFilter = () => {
    if (state.activeCatalogTab === "owned") return true;
    if (state.activeCatalogTab === "unowned") return false;
    return null;
  };
  const getActiveSourceFilter = (catalogType) => {
    if (!catalogType || catalogType !== "recipes") return "";
    const map = state.sourceFilterByMode && typeof state.sourceFilterByMode === "object"
      ? state.sourceFilterByMode
      : {};
    return String(map[catalogType] || "").trim();
  };
  const upsertCatalogItemCaches = (catalogType, itemId, patch) => {
    const id = String(itemId || "").trim();
    if (!id) return;
    const patchObj = patch && typeof patch === "object" ? patch : {};
    const applyPatch = (row) => {
      if (!row || String(row.id || "").trim() !== id) return row;
      return { ...row, ...patchObj };
    };
    state.renderedCatalogItems = (state.renderedCatalogItems || []).map(applyPatch);
    const allRows = getCatalogAllItemsCache()[catalogType];
    if (Array.isArray(allRows)) {
      getCatalogAllItemsCache()[catalogType] = allRows.map(applyPatch);
    }
  };
  const bulkPatchCatalogCache = (catalogType, itemIds, patcher) => {
    const cache = getCatalogAllItemsCache();
    const rows = cache[catalogType];
    if (!Array.isArray(rows) || !rows.length) return;
    const idSet = new Set((itemIds || []).map((x) => String(x || "").trim()).filter(Boolean));
    if (!idSet.size) return;
    cache[catalogType] = rows.map((row) => {
      const rid = String(row?.id || "").trim();
      if (!idSet.has(rid)) return row;
      return patcher(row);
    });
  };
  const invalidateDetailCacheItem = (mode, itemId) => {
    const key = String(mode || "").trim();
    const id = String(itemId || "").trim();
    if (!key || !id) return;
    const cache = state.detailCacheByMode?.[key];
    if (cache && typeof cache.delete === "function") {
      cache.delete(id);
    }
  };
  const sortCatalogLocal = (rows, sortBy, sortOrder) => {
    const sign = sortOrder === "desc" ? -1 : 1;
    const safeRows = [...rows];
    safeRows.sort((a, b) => {
      if (sortBy === "number") {
        const an = Number(a?.number ?? Number.MAX_SAFE_INTEGER);
        const bn = Number(b?.number ?? Number.MAX_SAFE_INTEGER);
        if (an !== bn) return (an - bn) * sign;
      } else if (sortBy === "category") {
        const ac = a?.category_ko || a?.category || "";
        const bc = b?.category_ko || b?.category || "";
        const diff = textKoSort(ac, bc);
        if (diff) return diff * sign;
      } else if (sortBy === "date") {
        const ad = String(a?.date || "");
        const bd = String(b?.date || "");
        const diff = ad.localeCompare(bd);
        if (diff) return diff * sign;
      }
      const nameDiff = textKoSort(catalogName(a), catalogName(b));
      if (nameDiff) return nameDiff * sign;
      return textKoSort(a?.id || "", b?.id || "") * sign;
    });
    return safeRows;
  };

  async function enrichMusicCardRows(rows) {
    const cache = getMusicCardMetaCache();
    const targets = rows.filter((row) => {
      const id = String(row?.id || "").trim();
      return id && !cache[id];
    });

    await Promise.all(
      targets.map(async (row) => {
        const id = String(row?.id || "").trim();
        if (!id) return;
        try {
          const payload = await getJSON(`/api/catalog/music/${id}/detail`);
          const fields = Array.isArray(payload?.fields) ? payload.fields : [];
          const rawFields = Array.isArray(payload?.raw_fields) ? payload.raw_fields : [];
          const buyField = fields.find((f) => String(f?.label || "").trim() === "구매가");
          const saleField = fields.find((f) => String(f?.label || "").trim() === "비매품 여부");
          const patch = {};
          const buyRaw = String(buyField?.value || "").trim();
          if (buyRaw) {
            patch.buy = Number(buyRaw.replace(/[^\d]/g, "")) || 0;
          } else {
            const rawBuy = rawFields.find((f) => {
              const key = String(f?.key || "").toLowerCase();
              return key === "buy" || key === "buy-price";
            });
            const rawBuyText = String(rawBuy?.value || "").trim();
            if (rawBuyText) {
              patch.buy = Number(rawBuyText.replace(/[^\d]/g, "")) || 0;
            }
          }
          const saleText = String(saleField?.value || "").trim();
          if (saleText) {
            patch.not_for_sale = saleText === "비매품";
          } else if (typeof payload?.summary?.not_for_sale === "boolean") {
            patch.not_for_sale = Boolean(payload.summary.not_for_sale);
          } else {
            const rawOrderable = rawFields.find((f) => {
              const key = String(f?.key || "").toLowerCase();
              return key === "is_orderable" || key === "isorderable";
            });
            const rawOrderableText = String(rawOrderable?.value || "").trim().toLowerCase();
            if (rawOrderableText === "true") patch.not_for_sale = false;
            if (rawOrderableText === "false") patch.not_for_sale = true;
          }
          if (patch.not_for_sale === false && (patch.buy === undefined || patch.buy <= 0)) {
            // K.K. 노래는 구매 가능한 경우 기본 구매가가 3,200벨이다.
            patch.buy = 3200;
          }
          cache[id] = patch;
        } catch (err) {
          console.error(err);
          cache[id] = {};
        }
      })
    );

    return rows.map((row) => {
      const id = String(row?.id || "").trim();
      const patch = cache[id] || {};
      return { ...row, ...patch };
    });
  }
  function needsVillagerReloadAfterToggle(payload) {
    if (!payload || typeof payload !== "object") return false;
    if (state.activeVillagerTab === "liked" && payload.liked === false) return true;
    if (state.activeVillagerTab === "island" && payload.on_island === false) return true;
    if (state.activeVillagerTab === "not_island" && payload.on_island === true) return true;
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

    personalitySelect.innerHTML = '<option value="">성격 전체</option>';
    speciesSelect.innerHTML = '<option value="">종 전체</option>';

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

    const syncVillagerSpeciesTabs = () => {
      if (!villagerSpeciesTabs) return;
      const active = String(speciesSelect.value || "");
      Array.from(villagerSpeciesTabs.querySelectorAll(".tab")).forEach((btn) => {
        const species = String(btn?.dataset?.species || "");
        btn.classList.toggle("active", species === active);
      });
    };

    if (villagerSpeciesTabs) {
      villagerSpeciesTabs.innerHTML = "";
      const rows = [{ en: "", ko: "종 전체" }, ...sortedSpecies];
      rows.forEach((row) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "tab";
        btn.dataset.species = String(row.en || "");
        btn.textContent = row.ko || row.en;
        btn.addEventListener("click", () => {
          const next = String(row.en || "");
          if (String(speciesSelect.value || "") === next) return;
          speciesSelect.value = next;
          speciesSelect.dispatchEvent(new Event("change", { bubbles: true }));
        });
        villagerSpeciesTabs.appendChild(btn);
      });
    }

    if (speciesSelect && !speciesSelect.dataset.speciesSyncBound) {
      speciesSelect.addEventListener("change", syncVillagerSpeciesTabs);
      speciesSelect.dataset.speciesSyncBound = "1";
    }
    syncVillagerSpeciesTabs();
    window.__acnhSyncVillagerSpeciesTabs = syncVillagerSpeciesTabs;

    const villagersPayload = await getJSON("/api/villagers");
    const villagerRows = Array.isArray(villagersPayload?.items) ? villagersPayload.items : [];
    const subtypeMap = new Map();
    villagerRows.forEach((row) => {
      const raw = String(row?.sub_personality || "").trim();
      if (!raw) return;
      const key = raw.toLowerCase();
      if (!subtypeMap.has(key)) subtypeMap.set(key, raw);
    });
    const subtypeRows = Array.from(subtypeMap.values()).sort((a, b) => a.localeCompare(b, "ko"));
    const effectiveSubtypeRows = subtypeRows.length ? subtypeRows : ["A", "B"];
    const prevSubtype = String(subtypeSelect?.value || "");
    if (subtypeSelect) {
      subtypeSelect.innerHTML = '<option value="">서브타입 전체</option>';
      effectiveSubtypeRows.forEach((subtype) => {
        const opt = document.createElement("option");
        opt.value = subtype;
        opt.textContent = subtype;
        subtypeSelect.appendChild(opt);
      });
      if (prevSubtype && effectiveSubtypeRows.includes(prevSubtype)) {
        subtypeSelect.value = prevSubtype;
      }
    }

    const syncVillagerSubtypeTabs = () => {
      if (!villagerSubtypeTabs) return;
      const active = String(subtypeSelect?.value || "");
      Array.from(villagerSubtypeTabs.querySelectorAll(".tab")).forEach((btn) => {
        const subtype = String(btn?.dataset?.subtype || "");
        btn.classList.toggle("active", subtype === active);
      });
    };
    if (subtypeSelect && !subtypeSelect.dataset.subtypeSyncBound) {
      subtypeSelect.addEventListener("change", syncVillagerSubtypeTabs);
      subtypeSelect.dataset.subtypeSyncBound = "1";
    }

    if (villagerSubtypeTabs) {
      villagerSubtypeTabs.innerHTML = "";
      const rows = effectiveSubtypeRows.map((x) => ({ key: x, label: x }));
      rows.forEach((row) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "tab";
        btn.dataset.subtype = String(row.key || "");
        btn.textContent = row.label;
        btn.addEventListener("click", () => {
          const nextRaw = String(row.key || "");
          if (!subtypeSelect) return;
          const current = String(subtypeSelect.value || "");
          const next = current === nextRaw ? "" : nextRaw;
          subtypeSelect.value = next;
          subtypeSelect.dispatchEvent(new Event("change", { bubbles: true }));
        });
        villagerSubtypeTabs.appendChild(btn);
      });
    }
    syncVillagerSubtypeTabs();
    window.__acnhSyncVillagerSubtypeTabs = syncVillagerSubtypeTabs;
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
    catalogSearchInput.placeholder = `${meta.label} 이름/출처 검색 (한글/영문)`;
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

    // 생물도감 + 레시피는 번호순이 기본 정렬.
    if (["bugs", "fish", "sea", "recipes"].includes(catalogType) && !catalogSortInitialized.has(catalogType)) {
      catalogSortBySelect.value = "number";
      catalogSortOrderSelect.value = "asc";
      catalogSortInitialized.add(catalogType);
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

    const cacheKey = query || "__all__";
    let data = villagerQueryCache.get(cacheKey);
    if (!data) {
      data = await getJSON(`/api/villagers?${query}`);
      villagerQueryCache.set(cacheKey, data);
    }

    const sourceItems = Array.isArray(data.items) ? data.items : [];
    const filteredItems =
      state.activeVillagerTab === "not_island"
        ? sourceItems.filter((row) => !Boolean(row?.on_island))
        : sourceItems;
    const subtypeFilter = String(subtypeSelect?.value || "").trim().toLowerCase();
    const finalItems = subtypeFilter
      ? filteredItems.filter((row) => String(row?.sub_personality || "").trim().toLowerCase() === subtypeFilter)
      : filteredItems;

    renderVillagers(sortVillagers(finalItems, sortBySelect.value || "name", sortOrderSelect.value || "asc"), {
      onSyncDetailNav: safeSyncDetailNav,
      onToggleState: async (villagerId, payload) => {
        await updateVillagerState(villagerId, payload);
        villagerQueryCache.clear();
        if (needsVillagerReloadAfterToggle(payload)) {
          await loadCurrentModeData();
        }
      },
      onOpenDetail: (villager) => {
        safeOpenVillagerDetail(villager);
      },
    });
  }

  /** Load catalog list (optionally preserving currently visible page span). */
  async function loadCatalog(catalogType, { preserveVisible = false } = {}) {
    return loadCatalogPage(catalogType, { append: false, preserveVisible });
  }

  async function ensureCatalogRows(catalogType) {
    const cache = getCatalogAllItemsCache();
    const existing = cache[catalogType];
    if (Array.isArray(existing) && existing.length) return existing;

    const rows = [];
    let page = 1;
    while (true) {
      const query = toQuery({
        page,
        page_size: 200,
        sort_by: "number",
        sort_order: "asc",
      });
      const chunk = await getJSON(`/api/catalog/${catalogType}?${query}`);
      const items = Array.isArray(chunk?.items) ? chunk.items : [];
      rows.push(...items);
      if (!chunk?.has_more || !items.length) break;
      page += 1;
    }
    cache[catalogType] = rows;
    return rows;
  }

  /** Fetch and render one catalog page; append if requested. */
  async function loadCatalogPage(catalogType, { append = false, preserveVisible = false } = {}) {
    const requestSeq = ++catalogFetchSeq;
    if (!append && catalogFetchAbortController) {
      try {
        catalogFetchAbortController.abort();
      } catch {
        // ignore
      }
    }
    catalogFetchAbortController = new AbortController();
    await applyCatalogMeta(catalogType);
    const meta = state.catalogMetaCache[catalogType] || { status_label: "보유" };
    try {
      await ensureCatalogRows(catalogType);
    } catch (err) {
      if (err?.name === "AbortError") return;
      throw err;
    }
    if (requestSeq !== catalogFetchSeq) return;

    const qNorm = String(catalogSearchInput.value || "").trim().toLowerCase();
    const ownedFilter = getActiveOwnedFilter();
    const extraType = catalogExtraSelect.dataset.extraType || "";
    const extraValue = getExtraFilterValue();
    const subCategory = String(state.activeSubCategory || "");
    const sourceFilter = getActiveSourceFilter(catalogType);
    const cache = getCatalogAllItemsCache();
    const allRows = Array.isArray(cache[catalogType])
      ? cache[catalogType]
      : [];

    let filtered = allRows.filter((row) => {
      if (qNorm) {
        const hay = `${row?.name_ko || ""} ${row?.name_en || ""} ${row?.name || ""} ${row?.source || ""} ${row?.source_notes || ""}`.toLowerCase();
        if (!hay.includes(qNorm)) return false;
      }

      if (catalogType === "art") {
        if (subCategory && String(row?.authenticity || "") !== subCategory) return false;
      } else if (
        catalogType === "recipes"
        && subCategory
        && (
          subCategory.startsWith("season:")
          || subCategory.startsWith("event:")
          || subCategory.startsWith("npc:")
        )
      ) {
        const recipeFilters = Array.isArray(row?.recipe_filters) ? row.recipe_filters : [];
        if (!recipeFilters.includes(subCategory)) return false;
      } else if (subCategory && String(row?.category || "") !== subCategory) {
        return false;
      }

      if (ownedFilter !== null && Boolean(row?.owned) !== ownedFilter) return false;

      if (sourceFilter) {
        const source = String(row?.source || "").trim();
        if (!source) return false;
        const tokens = source
          .split(",")
          .map((x) => String(x || "").trim())
          .filter(Boolean);
        if (!tokens.includes(sourceFilter)) return false;
      }

      if (extraValue) {
        if (extraType === "style") {
          const styles = Array.isArray(row?.styles) ? row.styles : [];
          if (!styles.includes(extraValue)) return false;
        } else if (extraType === "event_type") {
          if (String(row?.event_type || "") !== extraValue) return false;
        }
      }

      return true;
    });

    filtered = sortCatalogLocal(
      filtered,
      String(catalogSortBySelect.value || "name"),
      String(catalogSortOrderSelect.value || "asc")
    );

    const targetPage = append
      ? Math.max(1, Number(state.catalogLoadedPages || 1)) + 1
      : preserveVisible
        ? Math.max(1, Number(state.catalogLoadedPages || 1))
        : 1;
    const start = append ? (targetPage - 1) * state.catalogPageSize : 0;
    const end = targetPage * state.catalogPageSize;
    const items = filtered.slice(start, end);
    state.catalogPage = targetPage;
    state.catalogLoadedPages = targetPage;
    let renderItems = items;
    if (catalogType === "music" && renderItems.length) {
      renderItems = await enrichMusicCardRows(renderItems);
      const cache = getCatalogAllItemsCache();
      const byId = new Map(renderItems.map((x) => [String(x.id || ""), x]));
      cache[catalogType] = (cache[catalogType] || []).map((row) => {
        const id = String(row?.id || "");
        return byId.has(id) ? byId.get(id) : row;
      });
    }

    renderCatalog(
      renderItems,
      meta.status_label || "보유",
      {
        append,
        totalCount: filtered.length,
        hasMore: end < filtered.length,
      },
      {
        onSyncDetailNav: safeSyncDetailNav,
        onToggleOwned: async (itemId, owned, extra = {}) => {
          await updateCatalogState(state.activeMode, itemId, {
            owned,
            quantity: extra.quantity,
          });
          invalidateDetailCacheItem(state.activeMode, itemId);
          const target = state.renderedCatalogItems.find((x) => x.id === itemId);
          if (target) {
            target.owned = owned;
            if (state.activeMode === "furniture" && typeof extra.quantity === "number") {
              target.quantity = extra.quantity;
            }
          }
          upsertCatalogItemCaches(state.activeMode, itemId, {
            owned,
            ...(typeof extra.quantity === "number" ? { quantity: extra.quantity } : {}),
          });
          if (needsCatalogReloadAfterToggle(owned)) {
            const id = String(itemId || "").trim();
            const card = findCatalogCardById(id);
            if (card) card.remove();
            state.renderedCatalogItems = state.renderedCatalogItems.filter(
              (x) => String(x?.id || "").trim() !== id
            );
            state.activeCatalogItemIds = state.renderedCatalogItems.map((x) => x.id);
            resultCount.textContent = `${state.renderedCatalogItems.length}개`;
            scheduleCatalogRefresh(220);
          }
        },
        onUpdateQuantity: async (itemId, quantity) => {
          const owned = quantity > 0;
          await updateCatalogState(state.activeMode, itemId, { owned, quantity });
          invalidateDetailCacheItem(state.activeMode, itemId);
          const target = state.renderedCatalogItems.find((x) => x.id === itemId);
          if (target) {
            target.quantity = quantity;
            target.owned = owned;
          }
          upsertCatalogItemCaches(state.activeMode, itemId, { quantity, owned });
          if (needsCatalogReloadAfterToggle(owned)) {
            const id = String(itemId || "").trim();
            const card = findCatalogCardById(id);
            if (card) card.remove();
            state.renderedCatalogItems = state.renderedCatalogItems.filter(
              (x) => String(x?.id || "").trim() !== id
            );
            state.activeCatalogItemIds = state.renderedCatalogItems.map((x) => x.id);
            resultCount.textContent = `${state.renderedCatalogItems.length}개`;
            scheduleCatalogRefresh(220);
          }
        },
        onToggleDonated: async (itemId, donated) => {
          await updateCatalogState(state.activeMode, itemId, { donated });
          invalidateDetailCacheItem(state.activeMode, itemId);
          const target = state.renderedCatalogItems.find((x) => x.id === itemId);
          if (target) {
            target.donated = donated;
          }
          upsertCatalogItemCaches(state.activeMode, itemId, { donated });
        },
        onOpenDetail: (itemId) => {
          safeOpenDetail(itemId);
        },
        onFilterBySource: async (source) => {
          if (catalogType !== "recipes") return;
          const next = String(source || "").trim();
          if (!state.sourceFilterByMode || typeof state.sourceFilterByMode !== "object") {
            state.sourceFilterByMode = {};
          }
          const current = String(state.sourceFilterByMode[catalogType] || "").trim();
          state.sourceFilterByMode[catalogType] = current === next ? "" : next;
          await loadCatalog(catalogType, { preserveVisible: false });
        },
      }
    );
    if (typeof window.__acnhAutoInfiniteMaybe === "function") {
      window.__acnhAutoInfiniteMaybe();
    }
  }

  /** Dispatch loading based on current active mode (villagers/catalog). */
  async function loadCurrentModeData() {
    if (state.activeMode === "home") return;
    if (state.activeMode === "villagers") {
      await loadVillagers();
      return;
    }
    await loadCatalog(state.activeMode, { preserveVisible: false });
  }

  /** Set owned state for all currently rendered catalog items (current filtered list/page). */
  async function setVisibleCatalogOwned(owned) {
    let catalogMode = String(state.activeMode || "");
    if (!catalogMode || catalogMode === "home" || catalogMode === "villagers") {
      catalogMode = String(document.querySelector("#list")?.dataset?.catalogMode || "");
    }
    if (catalogMode && catalogMode !== "home" && catalogMode !== "villagers") {
      state.activeMode = catalogMode;
    }
    if (!catalogMode || catalogMode === "home" || catalogMode === "villagers") return;
    const ownedInputs = Array.from(document.querySelectorAll("#list .owned"));
    const domItemIds = ownedInputs
      .map((el) => String(el?.dataset?.itemId || el?.closest?.(".card")?.dataset?.itemId || "").trim())
      .filter(Boolean);
    const rows = Array.isArray(state.renderedCatalogItems) ? state.renderedCatalogItems : [];
    const fallbackIds = rows.map((x) => String(x?.id || "").trim()).filter(Boolean);
    const activeIds = Array.isArray(state.activeCatalogItemIds)
      ? state.activeCatalogItemIds.map((x) => String(x || "").trim()).filter(Boolean)
      : [];
    const itemIds = Array.from(new Set(domItemIds.length ? domItemIds : fallbackIds.length ? fallbackIds : activeIds));
    if (!itemIds.length) return;
    if (state.detailCacheByMode && state.detailCacheByMode[catalogMode]) {
      // 대량 토글 시에는 항목별 delete보다 모드 캐시를 비우는 편이 안전하다.
      state.detailCacheByMode[catalogMode] = new Map();
    }

    const rowById = new Map(rows.map((x) => [String(x.id || ""), x]));
    const nextOwned = Boolean(owned);

    // 즉시 반영(낙관적 업데이트)
    itemIds.forEach((itemId) => {
      const item = rowById.get(itemId);
      if (!item) return;
      item.owned = nextOwned;
      if (catalogMode === "furniture" && Number(item.variation_total || 0) === 0) {
        const currentQty = Math.max(0, Number(item.quantity || 0));
        item.quantity = nextOwned ? Math.max(1, currentQty) : 0;
      }
    });
    bulkPatchCatalogCache(catalogMode, itemIds, (row) => {
      const nextRow = { ...row, owned: nextOwned };
      if (catalogMode === "furniture" && Number(row?.variation_total || 0) === 0) {
        const currentQty = Math.max(0, Number(row?.quantity || 0));
        nextRow.quantity = nextOwned ? Math.max(1, currentQty) : 0;
      }
      return nextRow;
    });
    ownedInputs.forEach((el) => {
      const input = /** @type {HTMLInputElement} */ (el);
      input.indeterminate = false;
      input.checked = nextOwned;
    });

    // 보유/미보유 탭에서는 서버 응답을 기다리지 않고 즉시 목록 반영.
    const shouldPruneNow =
      (state.activeCatalogTab === "owned" && !nextOwned) ||
      (state.activeCatalogTab === "unowned" && nextOwned);
    if (shouldPruneNow) {
      const idSet = new Set(itemIds.map((x) => String(x)));
      const cards = Array.from(document.querySelectorAll("#list .card"));
      cards.forEach((card) => {
        const id = String(card?.dataset?.itemId || "").trim();
        if (idSet.has(id)) card.remove();
      });
      state.renderedCatalogItems = rows.filter((x) => !idSet.has(String(x?.id || "").trim()));
      state.activeCatalogItemIds = state.renderedCatalogItems.map((x) => x.id);
      resultCount.textContent = `${state.renderedCatalogItems.length}개`;
    }

    const fallbackSingleUpdates = async () => {
      for (const itemId of itemIds) {
        const item = rowById.get(itemId);
        const variationTotal = Number(item?.variation_total || 0);
        const isFurniture = catalogMode === "furniture";
        const payload = { owned: nextOwned };
        if (isFurniture && variationTotal === 0) {
          const currentQty = Math.max(0, Number(item?.quantity || 0));
          payload.quantity = nextOwned ? Math.max(1, currentQty) : 0;
        }
        try {
          await updateCatalogState(catalogMode, itemId, payload);
        } catch (e) {
          console.error(e);
        }
      }
    };

    try {
      await updateCatalogStateBulk(catalogMode, itemIds, nextOwned);
    } catch (err) {
      console.error(err);
      const status = Number(err?.status || err?.response?.status || 0);
      // bulk 미지원 서버에서만 단건 폴백. (요청 폭주 방지)
      if (status === 404 || status === 405) {
        await fallbackSingleUpdates();
      }
    }
    // bulk 동기화 이후에는 로컬 캐시가 이미 갱신됐으므로 즉시 재로딩을 생략한다.
  }

  async function toggleVisibleCatalogOwned() {
    const ownedInputs = Array.from(document.querySelectorAll("#list .owned"));
    if (!ownedInputs.length) return;
    const allOwned = ownedInputs.every((el) => {
      const input = /** @type {HTMLInputElement} */ (el);
      return Boolean(input.checked) && !Boolean(input.indeterminate);
    });
    await setVisibleCatalogOwned(!allOwned);
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
      if (state.activeMode === "villagers" || state.activeMode === "home") return;
      loadCatalog(state.activeMode, { preserveVisible: true }).catch((err) => console.error(err));
    }, delayMs);
  }

  return {
    loadVillagerMeta,
    loadCatalogPage,
    loadCurrentModeData,
    scheduleCatalogRefresh,
    scheduleLoad,
    setVisibleCatalogOwned,
    toggleVisibleCatalogOwned,
  };
}
