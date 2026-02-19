import {
  deleteCalendarEntry,
  getCalendarEntries,
  getCalendarAnnotations,
  getCalendarEntriesByDate,
  getJSON,
  getHomeSummary,
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
  deletePlayer,
  updateIslandProfile,
} from "./js/api.js";
import {
  bindCalendarEvents,
  createDayLoader,
  initializeCalendarState,
  loadCalendarMonth,
} from "./js/calendar.js";
import { brandHomeBtn, calendarSelectedDate, resultCount } from "./js/dom.js";
import { createDataController } from "./js/data.js";
import { createDetailController } from "./js/detail.js";
import { bindMainEvents } from "./js/events.js";
import { bindArtGuideEvents } from "./js/art-guide.js";
import {
  bindHomeEvents,
  loadHomeIslandResidents,
  loadHomeSummary,
  loadIslandProfile,
  loadPlayers,
} from "./js/home.js";
import { renderNav, updatePanels, updateScrollTopButton } from "./js/render.js";
import { state } from "./js/state.js";
import { getEffectiveNow } from "./js/utils.js";

let detailController = null;
let calendarReloadMonth = null;
let calendarLoadDay = null;

async function navigateToMode(mode) {
  const target = String(mode || "").trim();
  if (!target) return;
  const hit = (state.navModes || []).find((m) => m.key === target);
  if (!hit) return;
  state.activeMode = target;
  window.__acnhCurrentMode = state.activeMode;
  updatePanels();
  renderNav({
    onModeChange: async (nextMode) => {
      state.activeMode = nextMode;
      window.__acnhCurrentMode = state.activeMode;
      updatePanels();
      if (state.activeMode === "home") {
        await ensureHomeProfileLoaded();
        await ensureHomeIslandResidentsLoaded();
        await ensureHomeSummaryLoaded();
        await ensurePlayersLoaded();
        await ensureCalendarLoaded();
        return;
      }
      await dataController.loadCurrentModeData();
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
});

detailController = createDetailController({
  getJSON,
  updateCatalogVariationState,
  updateCatalogVariationStateBatch,
  scheduleCatalogRefresh: dataController.scheduleCatalogRefresh,
});

bindHomeEvents({
  updateIslandProfile,
  getHomeSummary,
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
  updateScrollTopButton,
  detailController,
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
bindArtGuideEvents({ getJSON });

async function ensureHomeProfileLoaded() {
  if (state.islandProfileLoaded) return;
  await loadIslandProfile(getIslandProfile);
}

async function ensureHomeSummaryLoaded() {
  await loadHomeSummary(getHomeSummary);
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
});
window.addEventListener("acnh:navigate-mode", (e) => {
  const mode = e?.detail?.mode || "";
  navigateToMode(mode).catch((err) => console.error(err));
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

    renderNav({
      onModeChange: () => {
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
    updateScrollTopButton();
  } catch (err) {
    console.error(err);
    resultCount.textContent = "데이터를 불러오지 못했습니다.";
  }
})();
