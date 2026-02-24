import {
  deleteCalendarEntry,
  getCalendarEntries,
  getCalendarAnnotations,
  getCalendarEntriesByDate,
  getJSON,
  getHomeSummary,
  getHomeCreaturesNow,
  getHomeIslandResidents,
  getVillagerMeta,
  getVillagers,
  getIslandProfile,
  getPlayers,
  saveCalendarEntry,
  savePlayer,
  setCalendarEntryChecked,
  setMainPlayer,
  updateIslandResidentOrder,
  updateVillagerState,
  updateCatalogVariationState,
  updateCatalogVariationStateBatch,
  updateCatalogState,
  deletePlayer,
  updateIslandProfile,
} from "./js/api.js";
import {
  bindCalendarEvents,
  createDayLoader,
  initializeCalendarState,
  loadCalendarMonth,
} from "./js/calendar.js";
import {
  brandHomeBtn,
  calendarSelectedDate,
  catalogExtraSelect,
  catalogSearchInput,
  catalogSortBySelect,
  catalogSortOrderSelect,
  catalogTabs,
  personalitySelect,
  resultCount,
  searchInput,
  sortBySelect,
  sortOrderSelect,
  speciesSelect,
  subtypeSelect,
  villagerTabs,
} from "./js/dom.js";
import { createDataController } from "./js/data.js";
import { createDetailController } from "./js/detail.js";
import { bindMainEvents } from "./js/events.js";
import {
  bindHomeEvents,
  loadHomeIslandResidents,
  loadHomeSummary,
  loadHomeCreaturesNow,
  loadIslandProfile,
  loadPlayers,
} from "./js/home.js";
import { renderNav, updatePanels, updateScrollTopButton } from "./js/render.js";
import { state } from "./js/state.js";
import { getEffectiveNow } from "./js/utils.js";

let detailController = null;
let calendarReloadMonth = null;
let calendarLoadDay = null;
let historyRestoreInProgress = false;
let lastViewQuery = "";

function isCatalogMode(mode) {
  return mode !== "home" && mode !== "villagers";
}

function syncTabButtonStates() {
  villagerTabs.forEach((el) => {
    const tab = String(el?.dataset?.tab || "all");
    el.classList.toggle("active", tab === state.activeVillagerTab);
  });
  catalogTabs.forEach((el) => {
    const tab = String(el?.dataset?.tab || "all");
    el.classList.toggle("active", tab === state.activeCatalogTab);
  });
}

function serializeViewQuery() {
  const params = new URLSearchParams();
  params.set("mode", String(state.activeMode || "home"));
  if (state.activeMode === "villagers") {
    params.set("vtab", String(state.activeVillagerTab || "all"));
    if (searchInput.value.trim()) params.set("vq", searchInput.value.trim());
    if (personalitySelect.value) params.set("personality", personalitySelect.value);
    if (speciesSelect.value) params.set("species", speciesSelect.value);
    if (subtypeSelect.value) params.set("subtype", subtypeSelect.value);
    if (sortBySelect.value) params.set("vsort", sortBySelect.value);
    if (sortOrderSelect.value) params.set("vorder", sortOrderSelect.value);
  } else if (isCatalogMode(state.activeMode)) {
    params.set("ctab", String(state.activeCatalogTab || "all"));
    if (catalogSearchInput.value.trim()) params.set("cq", catalogSearchInput.value.trim());
    if (catalogSortBySelect.value) params.set("csort", catalogSortBySelect.value);
    if (catalogSortOrderSelect.value) params.set("corder", catalogSortOrderSelect.value);
    const sub = String(state.subCategoryStateByMode?.[state.activeMode] || "");
    if (sub) params.set("sub", sub);
    if (catalogExtraSelect?.value) params.set("extra", catalogExtraSelect.value);
    if (state.activeMode === "recipes") {
      const source = String(state.sourceFilterByMode?.recipes || "").trim();
      if (source) params.set("source", source);
      const tags = Array.isArray(state.recipeTagSelectionByMode?.recipes)
        ? state.recipeTagSelectionByMode.recipes
        : [];
      if (tags.length) params.set("rtags", tags.join(","));
      const match = String(state.recipeTagMatchModeByMode?.recipes || "and").toLowerCase();
      if (match === "or") params.set("rmatch", "or");
    }
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

function commitViewHistory(historyAction = "replace") {
  if (historyRestoreInProgress) return;
  const query = serializeViewQuery();
  if (!query && !lastViewQuery) return;
  const url = `${window.location.pathname}${query}`;
  if (historyAction === "push" && query !== lastViewQuery) {
    window.history.pushState({ q: query }, "", url);
  } else {
    window.history.replaceState({ q: query }, "", url);
  }
  lastViewQuery = query;
}

function applyViewFromUrlSearch(search) {
  const params = new URLSearchParams(String(search || ""));
  const mode = params.get("mode") || "home";
  const knownModes = new Set((state.navModes || []).map((m) => String(m?.key || "")));
  state.activeMode = knownModes.has(mode) ? mode : "home";

  state.activeVillagerTab = params.get("vtab") || "all";
  searchInput.value = params.get("vq") || "";
  personalitySelect.value = params.get("personality") || "";
  speciesSelect.value = params.get("species") || "";
  subtypeSelect.value = params.get("subtype") || "";
  sortBySelect.value = params.get("vsort") || "name";
  sortOrderSelect.value = params.get("vorder") || "asc";

  state.activeCatalogTab = params.get("ctab") || "all";
  catalogSearchInput.value = params.get("cq") || "";
  catalogSortBySelect.value = params.get("csort") || (
    ["bugs", "fish", "sea", "recipes"].includes(state.activeMode) ? "number" : "name"
  );
  catalogSortOrderSelect.value = params.get("corder") || "asc";

  const sub = params.get("sub") || "";
  state.activeSubCategory = sub;
  if (state.activeMode) {
    state.subCategoryStateByMode[state.activeMode] = sub;
  }
  catalogExtraSelect.value = params.get("extra") || "";

  if (!state.sourceFilterByMode || typeof state.sourceFilterByMode !== "object") {
    state.sourceFilterByMode = {};
  }
  state.sourceFilterByMode.recipes = params.get("source") || "";

  if (!state.recipeTagSelectionByMode || typeof state.recipeTagSelectionByMode !== "object") {
    state.recipeTagSelectionByMode = {};
  }
  const tagRaw = params.get("rtags") || "";
  state.recipeTagSelectionByMode.recipes = tagRaw
    ? tagRaw.split(",").map((x) => String(x || "").trim()).filter(Boolean)
    : [];

  if (!state.recipeTagMatchModeByMode || typeof state.recipeTagMatchModeByMode !== "object") {
    state.recipeTagMatchModeByMode = {};
  }
  state.recipeTagMatchModeByMode.recipes = params.get("rmatch") === "or" ? "or" : "and";

  syncTabButtonStates();
}

async function navigateToMode(mode) {
  const target = String(mode || "").trim();
  if (!target) return;
  if (state.activeMode === "recipes" && target !== "recipes" && state.sourceFilterByMode) {
    state.sourceFilterByMode.recipes = "";
  }
  const hit = (state.navModes || []).find((m) => m.key === target);
  if (!hit) return;
  state.activeMode = target;
  window.__acnhCurrentMode = state.activeMode;
  updatePanels();
  renderNav({
    onModeChange: async (nextMode) => {
      if (state.activeMode === "recipes" && nextMode !== "recipes" && state.sourceFilterByMode) {
        state.sourceFilterByMode.recipes = "";
      }
      state.activeMode = nextMode;
      window.__acnhCurrentMode = state.activeMode;
      updatePanels();
      if (state.activeMode === "home") {
        await ensureHomeProfileLoaded();
        await ensureHomeIslandResidentsLoaded();
        await ensureHomeSummaryLoaded();
        await ensurePlayersLoaded();
        await ensureCalendarLoaded();
        commitViewHistory("push");
        return;
      }
      await dataController.loadCurrentModeData();
      commitViewHistory("push");
    },
  });
  if (state.activeMode === "home") {
    await ensureHomeProfileLoaded();
    await ensureHomeIslandResidentsLoaded();
    await ensureHomeSummaryLoaded();
    await ensurePlayersLoaded();
    await ensureCalendarLoaded();
    return;
  }
  await dataController.loadCurrentModeData();
  commitViewHistory("push");
}

const dataController = createDataController({
  onSyncDetailNav: () => {
    if (detailController) detailController.syncDetailNavState();
  },
  onOpenDetail: (itemId) => {
    if (!detailController) return;
    detailController.openCatalogDetail(itemId).catch((err) => console.error(err));
  },
  onOpenVillagerDetail: (villager) => {
    if (!detailController) return;
    detailController.openVillagerDetail(villager);
  },
  onStateChange: (historyAction = "replace") => {
    commitViewHistory(historyAction);
  },
});

detailController = createDetailController({
  getJSON,
  updateCatalogState,
  updateCatalogVariationState,
  updateCatalogVariationStateBatch,
  scheduleCatalogRefresh: dataController.scheduleCatalogRefresh,
});

bindHomeEvents({
  updateIslandProfile,
  getHomeSummary,
  getHomeCreaturesNow,
  getPlayers,
  savePlayer,
  setMainPlayer,
  deletePlayer,
});

bindMainEvents({
  scheduleLoad: dataController.scheduleLoad,
  loadCurrentModeData: dataController.loadCurrentModeData,
  loadCatalogPage: dataController.loadCatalogPage,
  toggleVisibleCatalogOwned: dataController.toggleVisibleCatalogOwned,
  toggleVisibleCatalogDonated: dataController.toggleVisibleCatalogDonated,
  updateScrollTopButton,
  detailController,
  onStateChange: (historyAction = "replace") => {
    commitViewHistory(historyAction);
  },
});
window.__acnhToggleAllOwned = () => dataController.toggleVisibleCatalogOwned();
window.__acnhCurrentMode = state.activeMode;
window.__acnhForceBulkToggleVisible = async () => {
  const ownedInputs = Array.from(document.querySelectorAll("#list .owned"));
  if (!ownedInputs.length) return false;
  const allOwned = ownedInputs.every((el) => Boolean(el.checked) && !Boolean(el.indeterminate));
  await dataController.setVisibleCatalogOwned(!allOwned);
  return true;
};

async function ensureHomeProfileLoaded() {
  if (state.islandProfileLoaded) return;
  await loadIslandProfile(getIslandProfile);
}

async function ensureHomeSummaryLoaded() {
  await loadHomeSummary(getHomeSummary);
  await loadHomeCreaturesNow(getHomeCreaturesNow);
}

async function ensureHomeIslandResidentsLoaded() {
  await loadHomeIslandResidents(getHomeIslandResidents, {
    onOpenVillagerDetail: (villager, residents) => {
      if (!detailController) return;
      detailController.openVillagerDetail(villager, {
        contextVillagers: Array.isArray(residents) ? residents : [],
      });
    },
    getVillagerMeta,
    getVillagers,
    updateVillagerState,
    updateIslandResidentOrder,
  });
}

async function ensurePlayersLoaded() {
  await loadPlayers(getPlayers, {
    onSetMain: async (playerId) => {
      await setMainPlayer(playerId);
      await ensurePlayersLoaded();
    },
    onDelete: async (playerId) => {
      await deletePlayer(playerId);
      await ensurePlayersLoaded();
    },
  });
}

async function ensureCalendarLoaded() {
  if (state.calendarLoaded) return;
  initializeCalendarState();
  const reloadMonth = async () => {
    await loadCalendarMonth(getCalendarEntries, getCalendarAnnotations);
  };
  const loadDay = createDayLoader({
    getCalendarEntriesByDate,
    setCalendarEntryChecked,
    deleteCalendarEntry,
    reloadMonth,
  });
  bindCalendarEvents({
    saveCalendarEntry,
    reloadMonth,
    loadDay,
  });
  calendarReloadMonth = reloadMonth;
  calendarLoadDay = loadDay;
  await reloadMonth();
  await loadDay();
  state.calendarLoaded = true;
}

function effectiveIsoDate() {
  const now = getEffectiveNow(state);
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

async function syncCalendarToEffectiveDate() {
  const date = effectiveIsoDate();
  state.calendarSelectedDate = date;
  state.calendarMonth = date.slice(0, 7);
  if (calendarSelectedDate) {
    calendarSelectedDate.value = date;
  }
  if (!state.calendarLoaded || !calendarReloadMonth || !calendarLoadDay) return;
  await calendarReloadMonth();
  await calendarLoadDay();
}

window.addEventListener("acnh:effective-date-changed", () => {
  syncCalendarToEffectiveDate().catch((err) => console.error(err));
  ensureHomeSummaryLoaded().catch((err) => console.error(err));
});
window.addEventListener("acnh:navigate-mode", (e) => {
  const mode = e?.detail?.mode || "";
  navigateToMode(mode).catch((err) => console.error(err));
});
window.addEventListener("popstate", () => {
  historyRestoreInProgress = true;
  applyViewFromUrlSearch(window.location.search);
  window.__acnhCurrentMode = state.activeMode;
  updatePanels();
  renderNav({
    onModeChange: () => {
      if (state.activeMode !== "recipes" && state.sourceFilterByMode) {
        state.sourceFilterByMode.recipes = "";
      }
      window.__acnhCurrentMode = state.activeMode;
      updatePanels();
      if (state.activeMode === "home") {
        ensureHomeProfileLoaded().catch((err) => console.error(err));
        ensureHomeIslandResidentsLoaded().catch((err) => console.error(err));
        ensureHomeSummaryLoaded().catch((err) => console.error(err));
        ensurePlayersLoaded().catch((err) => console.error(err));
        ensureCalendarLoaded().catch((err) => console.error(err));
        return;
      }
      dataController.loadCurrentModeData().catch((err) => console.error(err));
    },
  });
  const task = state.activeMode === "home"
    ? Promise.all([
        ensureHomeProfileLoaded(),
        ensureHomeIslandResidentsLoaded(),
        ensureHomeSummaryLoaded(),
        ensurePlayersLoaded(),
        ensureCalendarLoaded(),
      ])
    : dataController.loadCurrentModeData();
  Promise.resolve(task)
    .catch((err) => console.error(err))
    .finally(() => {
      lastViewQuery = window.location.search || "";
      historyRestoreInProgress = false;
    });
});
if (brandHomeBtn) {
  brandHomeBtn.addEventListener("click", () => {
    navigateToMode("home").catch((err) => console.error(err));
  });
}

(async () => {
  try {
    const nav = await getJSON("/api/nav");
    state.navModes = nav.modes || [];

    if (!state.navModes.find((m) => m.key === "home")) {
      state.navModes.unshift({ key: "home", label: "홈" });
    }
    if (!state.navModes.find((m) => m.key === "villagers")) {
      state.navModes.unshift({ key: "villagers", label: "주민" });
    }

    applyViewFromUrlSearch(window.location.search);
    window.__acnhCurrentMode = state.activeMode;

    renderNav({
      onModeChange: () => {
        if (state.activeMode !== "recipes" && state.sourceFilterByMode) {
          state.sourceFilterByMode.recipes = "";
        }
        window.__acnhCurrentMode = state.activeMode;
        updatePanels();
        if (state.activeMode === "home") {
          ensureHomeProfileLoaded().catch((err) => console.error(err));
          ensureHomeIslandResidentsLoaded().catch((err) => console.error(err));
          ensureHomeSummaryLoaded().catch((err) => console.error(err));
          ensurePlayersLoaded().catch((err) => console.error(err));
          ensureCalendarLoaded().catch((err) => console.error(err));
          commitViewHistory("push");
          return;
        }
        dataController.loadCurrentModeData().catch((err) => console.error(err));
        commitViewHistory("push");
      },
    });
    updatePanels();

    await ensureHomeProfileLoaded();
    await ensureHomeIslandResidentsLoaded();
    await ensureHomeSummaryLoaded();
    await ensurePlayersLoaded();
    await ensureCalendarLoaded();
    await dataController.loadVillagerMeta();
    if (state.activeMode !== "home") {
      await dataController.loadCurrentModeData();
    }
    commitViewHistory("replace");
    updateScrollTopButton();
  } catch (err) {
    console.error(err);
    resultCount.textContent = "데이터를 불러오지 못했습니다.";
  }
})();
