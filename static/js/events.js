import {
  catalogExtraSelect,
  catalogResetBtn,
  catalogSearchInput,
  catalogSortBySelect,
  catalogSortOrderSelect,
  catalogSortOrderToggleBtn,
  catalogTabs,
  recipeTagModal,
  loadMoreBtn,
  personalitySelect,
  resetBtn,
  scrollTopBtn,
  searchInput,
  subtypeSelect,
  sortBySelect,
  sortOrderSelect,
  sortOrderToggleBtn,
  speciesSelect,
  villagerTabs,
} from "./dom.js";
import { state } from "./state.js";

/**
 * Bind main page events (filters, tabs, reset, load-more, scroll-top).
 * @param {{
 *   scheduleLoad: () => void,
 *   loadCurrentModeData: () => Promise<void>,
 *   loadCatalogPage: (catalogType: string, options?: { append?: boolean }) => Promise<void>,
 *   toggleVisibleCatalogOwned: () => Promise<void>,
 *   updateScrollTopButton: () => void,
 *   detailController: { bindEvents: () => void }
 * }} handlers
 */
export function bindMainEvents({
  scheduleLoad,
  loadCurrentModeData,
  loadCatalogPage,
  toggleVisibleCatalogOwned,
  updateScrollTopButton,
  detailController,
}) {
  let loadingMore = false;
  const isMobileInfiniteMode = () =>
    window.matchMedia("(max-width: 768px)").matches &&
    state.activeMode !== "villagers" &&
    state.activeMode !== "home";

  const maybeAutoLoadMore = () => {
    if (!isMobileInfiniteMode() || loadingMore || !state.catalogHasMore) return;
    const docHeight = document.documentElement.scrollHeight;
    const viewportBottom = window.innerHeight + window.scrollY;
    const nearBottom = viewportBottom >= docHeight - 420;
    const underfilled = docHeight <= window.innerHeight + 24;
    if (!(nearBottom || underfilled)) return;
    loadingMore = true;
    loadCatalogPage(state.activeMode, { append: true })
      .catch((err) => console.error(err))
      .finally(() => {
        loadingMore = false;
        if (isMobileInfiniteMode() && state.catalogHasMore) {
          window.setTimeout(maybeAutoLoadMore, 0);
        }
      });
  };
  window.__acnhAutoInfiniteMaybe = () => {
    window.setTimeout(maybeAutoLoadMore, 0);
  };

  const runLoad = () => {
    loadCurrentModeData()
      .then(() => {
        maybeAutoLoadMore();
      })
      .catch((err) => console.error(err));
  };
  const syncSortOrderToggle = () => {
    if (!sortOrderToggleBtn) return;
    const isDesc = String(sortOrderSelect.value || "asc") === "desc";
    sortOrderToggleBtn.textContent = isDesc ? "↓" : "↑";
    sortOrderToggleBtn.setAttribute("aria-label", isDesc ? "내림차순 정렬" : "오름차순 정렬");
  };
  const syncCatalogSortOrderToggle = () => {
    if (!catalogSortOrderToggleBtn) return;
    const isDesc = String(catalogSortOrderSelect.value || "asc") === "desc";
    catalogSortOrderToggleBtn.textContent = isDesc ? "↓" : "↑";
    catalogSortOrderToggleBtn.setAttribute("aria-label", isDesc ? "내림차순 정렬" : "오름차순 정렬");
  };

  searchInput.addEventListener("input", scheduleLoad);
  personalitySelect.addEventListener("change", runLoad);
  subtypeSelect.addEventListener("change", runLoad);
  speciesSelect.addEventListener("change", runLoad);
  sortBySelect.addEventListener("change", runLoad);
  sortOrderSelect.addEventListener("change", () => {
    syncSortOrderToggle();
    runLoad();
  });
  if (sortOrderToggleBtn) {
    sortOrderToggleBtn.addEventListener("click", () => {
      const isDesc = String(sortOrderSelect.value || "asc") === "desc";
      sortOrderSelect.value = isDesc ? "asc" : "desc";
      sortOrderSelect.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }
  syncSortOrderToggle();
  syncCatalogSortOrderToggle();

  villagerTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      state.activeVillagerTab = tab.dataset.tab || "all";
      villagerTabs.forEach((el) => el.classList.toggle("active", el === tab));
      runLoad();
    });
  });

  resetBtn.addEventListener("click", () => {
    searchInput.value = "";
    personalitySelect.value = "";
    subtypeSelect.value = "";
    speciesSelect.value = "";
    if (typeof window.__acnhSyncVillagerSpeciesTabs === "function") {
      window.__acnhSyncVillagerSpeciesTabs();
    }
    if (typeof window.__acnhSyncVillagerSubtypeTabs === "function") {
      window.__acnhSyncVillagerSubtypeTabs();
    }
    sortBySelect.value = "name";
    sortOrderSelect.value = "asc";
    syncSortOrderToggle();
    state.activeVillagerTab = "all";
    villagerTabs.forEach((el) => el.classList.toggle("active", el.dataset.tab === "all"));
    runLoad();
  });

  catalogSearchInput.addEventListener("input", scheduleLoad);
  catalogExtraSelect.addEventListener("change", runLoad);
  catalogSortBySelect.addEventListener("change", runLoad);
  catalogSortOrderSelect.addEventListener("change", () => {
    syncCatalogSortOrderToggle();
    runLoad();
  });
  if (catalogSortOrderToggleBtn) {
    catalogSortOrderToggleBtn.addEventListener("click", () => {
      const isDesc = String(catalogSortOrderSelect.value || "asc") === "desc";
      catalogSortOrderSelect.value = isDesc ? "asc" : "desc";
      catalogSortOrderSelect.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  catalogTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      state.activeCatalogTab = tab.dataset.tab || "all";
      if (state.activeMode === "recipes" && state.sourceFilterByMode) {
        state.sourceFilterByMode[state.activeMode] = "";
      }
      catalogTabs.forEach((el) => el.classList.toggle("active", el === tab));
      runLoad();
    });
  });

  catalogResetBtn.addEventListener("click", () => {
    catalogSearchInput.value = "";
    catalogExtraSelect.value = "";
    if (!state.sourceFilterByMode || typeof state.sourceFilterByMode !== "object") {
      state.sourceFilterByMode = {};
    }
    if (state.activeMode) state.sourceFilterByMode[state.activeMode] = "";
    if (!state.recipeTagSelectionByMode || typeof state.recipeTagSelectionByMode !== "object") {
      state.recipeTagSelectionByMode = {};
    }
    if (!state.recipeTagMatchModeByMode || typeof state.recipeTagMatchModeByMode !== "object") {
      state.recipeTagMatchModeByMode = {};
    }
    if (state.activeMode) {
      state.recipeTagSelectionByMode[state.activeMode] = [];
      state.recipeTagMatchModeByMode[state.activeMode] = "and";
    }
    state.activeSubCategory = "";
    if (state.activeMode) state.subCategoryStateByMode[state.activeMode] = "";
    if (state.activeMode === "events") {
      catalogSortBySelect.value = "date";
    } else if (["bugs", "fish", "sea", "recipes"].includes(state.activeMode)) {
      catalogSortBySelect.value = "number";
    } else {
      catalogSortBySelect.value = "name";
    }
    catalogSortOrderSelect.value = "asc";
    syncCatalogSortOrderToggle();
    state.activeCatalogTab = "all";
    catalogTabs.forEach((el) => el.classList.toggle("active", el.dataset.tab === "all"));
    runLoad();
  });

  catalogTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      if (recipeTagModal) {
        recipeTagModal.classList.add("hidden");
        recipeTagModal.setAttribute("aria-hidden", "true");
      }
    });
  });

  loadMoreBtn.addEventListener("click", () => {
    if (state.activeMode === "villagers" || !state.catalogHasMore) return;
    loadCatalogPage(state.activeMode, { append: true }).catch((err) => console.error(err));
  });

  {
    let lastTriggerTs = 0;
    let togglingAll = false;
    const runToggleAll = async () => {
      const now = Date.now();
      if (togglingAll) return;
      if (now - lastTriggerTs < 500) return;
      lastTriggerTs = now;
      togglingAll = true;
      try {
        await toggleVisibleCatalogOwned();
      } catch (err) {
        console.error(err);
      } finally {
        togglingAll = false;
      }
    };

    const handleToggleAllEvent = (e) => {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      runToggleAll().catch((err) => console.error(err));
    };

    // inline onclick/ontouchstart 폴백에서 호출하는 전역 핸들러
    window.__acnhHandleToggleAll = handleToggleAllEvent;
  }

  if (scrollTopBtn) {
    scrollTopBtn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }
  window.addEventListener(
    "scroll",
    () => {
      updateScrollTopButton();
      maybeAutoLoadMore();
    },
    { passive: true }
  );

  detailController.bindEvents();
}
