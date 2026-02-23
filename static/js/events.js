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
 *   detailController: { bindEvents: () => void },
 *   onStateChange?: (historyAction?: "push" | "replace") => void
 * }} handlers
 */
export function bindMainEvents({
  scheduleLoad,
  loadCurrentModeData,
  loadCatalogPage,
  toggleVisibleCatalogOwned,
  updateScrollTopButton,
  detailController,
  onStateChange,
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

  const runLoad = (historyAction = "replace") => {
    loadCurrentModeData()
      .then(() => {
        maybeAutoLoadMore();
        if (onStateChange) onStateChange(historyAction);
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
  personalitySelect.addEventListener("change", () => runLoad("replace"));
  subtypeSelect.addEventListener("change", () => runLoad("replace"));
  speciesSelect.addEventListener("change", () => runLoad("replace"));
  sortBySelect.addEventListener("change", () => runLoad("replace"));
  sortOrderSelect.addEventListener("change", () => {
    syncSortOrderToggle();
    runLoad("replace");
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
      runLoad("push");
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
    runLoad("push");
  });

  catalogSearchInput.addEventListener("input", scheduleLoad);
  catalogExtraSelect.addEventListener("change", () => runLoad("replace"));
  catalogSortBySelect.addEventListener("change", () => runLoad("replace"));
  catalogSortOrderSelect.addEventListener("change", () => {
    syncCatalogSortOrderToggle();
    runLoad("replace");
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
      const tabKey = String(tab.dataset.tab || "");
      const ownedBtn = catalogTabs.find((el) => el.dataset.tab === "owned");
      const unownedBtn = catalogTabs.find((el) => el.dataset.tab === "unowned");
      const isOwned = tabKey === "owned";
      const isUnowned = tabKey === "unowned";
      if (!isOwned && !isUnowned) return;

      const wasActive = tab.classList.contains("active");
      if (wasActive) {
        // 재클릭하면 전체(둘 다 해제)
        state.activeCatalogTab = "all";
        ownedBtn?.classList.remove("active");
        unownedBtn?.classList.remove("active");
      } else if (isOwned) {
        // 보유만 선택 (미보유는 자동 해제)
        state.activeCatalogTab = "owned";
        ownedBtn?.classList.add("active");
        unownedBtn?.classList.remove("active");
      } else {
        // 미보유만 선택 (보유만은 자동 해제)
        state.activeCatalogTab = "unowned";
        ownedBtn?.classList.remove("active");
        unownedBtn?.classList.add("active");
      }

      if (state.activeMode === "recipes" && state.sourceFilterByMode) {
        state.sourceFilterByMode[state.activeMode] = "";
      }
      runLoad("push");
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
    catalogSortBySelect.value = "number";
    catalogSortOrderSelect.value = "asc";
    syncCatalogSortOrderToggle();
    state.activeCatalogTab = "all";
    catalogTabs.forEach((el) => el.classList.remove("active"));
    runLoad("push");
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
