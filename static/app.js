import {
  getJSON,
  updateCatalogVariationState,
  updateCatalogVariationStateBatch,
} from "./js/api.js";
import { resultCount } from "./js/dom.js";
import { createDataController } from "./js/data.js";
import { createDetailController } from "./js/detail.js";
import { bindMainEvents } from "./js/events.js";
import { renderNav, updatePanels, updateScrollTopButton } from "./js/render.js";
import { state } from "./js/state.js";

let detailController = null;

const dataController = createDataController({
  onSyncDetailNav: () => {
    if (detailController) detailController.syncDetailNavState();
  },
  onOpenDetail: (itemId) => {
    if (!detailController) return;
    detailController.openCatalogDetail(itemId).catch((err) => console.error(err));
  },
});

detailController = createDetailController({
  getJSON,
  updateCatalogVariationState,
  updateCatalogVariationStateBatch,
  scheduleCatalogRefresh: dataController.scheduleCatalogRefresh,
});

bindMainEvents({
  scheduleLoad: dataController.scheduleLoad,
  loadCurrentModeData: dataController.loadCurrentModeData,
  loadCatalogPage: dataController.loadCatalogPage,
  updateScrollTopButton,
  detailController,
});

(async () => {
  try {
    const nav = await getJSON("/api/nav");
    state.navModes = nav.modes || [];

    if (!state.navModes.find((m) => m.key === "villagers")) {
      state.navModes.unshift({ key: "villagers", label: "주민" });
    }

    renderNav({
      onModeChange: () => {
        updatePanels();
        dataController.loadCurrentModeData().catch((err) => console.error(err));
      },
    });
    updatePanels();

    await dataController.loadVillagerMeta();
    await dataController.loadCurrentModeData();
    updateScrollTopButton();
  } catch (err) {
    console.error(err);
    resultCount.textContent = "데이터를 불러오지 못했습니다.";
  }
})();
