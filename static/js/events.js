import {
  catalogExtraSelect,
  catalogResetBtn,
  catalogSearchInput,
  catalogSortBySelect,
  catalogSortOrderSelect,
  catalogTabs,
  loadMoreBtn,
  personalitySelect,
  resetBtn,
  scrollTopBtn,
  searchInput,
  sortBySelect,
  sortOrderSelect,
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
  const runLoad = () => {
    loadCurrentModeData().catch((err) => console.error(err));
  };

  searchInput.addEventListener("input", scheduleLoad);
  personalitySelect.addEventListener("change", runLoad);
  speciesSelect.addEventListener("change", runLoad);
  sortBySelect.addEventListener("change", runLoad);
  sortOrderSelect.addEventListener("change", runLoad);

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
    speciesSelect.value = "";
    sortBySelect.value = "name";
    sortOrderSelect.value = "asc";
    state.activeVillagerTab = "all";
    villagerTabs.forEach((el) => el.classList.toggle("active", el.dataset.tab === "all"));
    runLoad();
  });

  catalogSearchInput.addEventListener("input", scheduleLoad);
  catalogExtraSelect.addEventListener("change", runLoad);
  catalogSortBySelect.addEventListener("change", runLoad);
  catalogSortOrderSelect.addEventListener("change", runLoad);

  catalogTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      state.activeCatalogTab = tab.dataset.tab || "all";
      catalogTabs.forEach((el) => el.classList.toggle("active", el === tab));
      runLoad();
    });
  });

  catalogResetBtn.addEventListener("click", () => {
    catalogSearchInput.value = "";
    catalogExtraSelect.value = "";
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
    state.activeCatalogTab = "all";
    catalogTabs.forEach((el) => el.classList.toggle("active", el.dataset.tab === "all"));
    runLoad();
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
  window.addEventListener("scroll", updateScrollTopButton, { passive: true });

  detailController.bindEvents();
}
