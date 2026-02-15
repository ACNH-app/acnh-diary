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
 *   updateScrollTopButton: () => void,
 *   detailController: { bindEvents: () => void }
 * }} handlers
 */
export function bindMainEvents({
  scheduleLoad,
  loadCurrentModeData,
  loadCatalogPage,
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
    catalogSortBySelect.value = state.activeMode === "events" ? "date" : "name";
    catalogSortOrderSelect.value = "asc";
    state.activeCatalogTab = "all";
    catalogTabs.forEach((el) => el.classList.toggle("active", el.dataset.tab === "all"));
    runLoad();
  });

  loadMoreBtn.addEventListener("click", () => {
    if (state.activeMode === "villagers" || !state.catalogHasMore) return;
    loadCatalogPage(state.activeMode, { append: true }).catch((err) => console.error(err));
  });

  if (scrollTopBtn) {
    scrollTopBtn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }
  window.addEventListener("scroll", updateScrollTopButton, { passive: true });

  detailController.bindEvents();
}
