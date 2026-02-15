import {
  catalogCardTemplate,
  catalogPanel,
  homePanel,
  list,
  loadMoreWrap,
  resultCount,
  scrollTopBtn,
  subCategoryTabs,
  topNav,
  villagerCardTemplate,
  villagerPanel,
} from "./dom.js";
import { state } from "./state.js";

export function updateScrollTopButton() {
  if (!scrollTopBtn) return;
  const shouldShow = window.scrollY > 320;
  scrollTopBtn.classList.toggle("hidden", !shouldShow);
}

export function renderNav({ onModeChange } = {}) {
  topNav.innerHTML = "";
  state.navModes.forEach((mode) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `nav-btn ${mode.key === state.activeMode ? "active" : ""}`;
    button.dataset.mode = mode.key;
    button.textContent = mode.label;
    button.addEventListener("click", () => {
      state.activeMode = mode.key;
      if (onModeChange) onModeChange(mode.key);
    });
    topNav.appendChild(button);
  });
}

export function updatePanels() {
  Array.from(topNav.querySelectorAll(".nav-btn")).forEach((el) => {
    el.classList.toggle("active", el.dataset.mode === state.activeMode);
  });

  const homeMode = state.activeMode === "home";
  const villagerMode = state.activeMode === "villagers";
  homePanel.classList.toggle("hidden", !homeMode);
  villagerPanel.classList.toggle("hidden", !villagerMode);
  catalogPanel.classList.toggle("hidden", villagerMode || homeMode);
  resultCount.classList.toggle("hidden", homeMode);
  list.classList.toggle("hidden", homeMode);
  loadMoreWrap.classList.toggle("hidden", homeMode || villagerMode || !state.catalogHasMore);
}

export function renderVillagers(items, { onToggleState, onOpenDetail, onSyncDetailNav } = {}) {
  list.innerHTML = "";
  resultCount.textContent = `${items.length}명`;
  state.renderedVillagers = items.slice();
  state.activeCatalogItemIds = state.renderedVillagers.map((v) => String(v.id || ""));
  if (onSyncDetailNav) onSyncDetailNav();

  items.forEach((v) => {
    const fragment = villagerCardTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".card");
    card.classList.add("clickable");
    const icon = fragment.querySelector(".icon");
    const nameKo = fragment.querySelector(".name-ko");
    const nameEn = fragment.querySelector(".name-en");
    const meta = fragment.querySelector(".meta");
    const birthday = fragment.querySelector(".birthday");
    const liked = fragment.querySelector(".liked");
    const onIsland = fragment.querySelector(".on-island");
    const formerResident = fragment.querySelector(".former-resident");

    icon.src = v.icon_uri || v.image_uri || "";
    icon.addEventListener("error", () => {
      if (icon.src !== v.image_uri && v.image_uri) icon.src = v.image_uri;
    });

    nameKo.textContent = v.name_ko || v.name_en;
    nameEn.textContent = v.name_en ? `EN: ${v.name_en}` : "";
    meta.textContent = `${v.species_ko} | ${v.personality_ko}`;
    birthday.textContent = v.birthday ? `생일: ${v.birthday}` : "";

    liked.checked = Boolean(v.liked);
    onIsland.checked = Boolean(v.on_island);
    formerResident.checked = Boolean(v.former_resident);

    liked.addEventListener("change", async () => {
      if (!onToggleState) return;
      await onToggleState(v.id, { liked: liked.checked });
    });
    onIsland.addEventListener("change", async () => {
      if (!onToggleState) return;
      await onToggleState(v.id, { on_island: onIsland.checked });
    });
    formerResident.addEventListener("change", async () => {
      if (!onToggleState) return;
      await onToggleState(v.id, { former_resident: formerResident.checked });
    });

    card.addEventListener("click", (e) => {
      if (e.target && e.target.closest("input, label, button")) return;
      if (onOpenDetail) onOpenDetail(v);
    });

    list.appendChild(fragment);
  });
}

export function renderCatalog(items, statusLabel, options = {}, handlers = {}) {
  const append = Boolean(options.append);
  const totalCount = Number(options.totalCount ?? items.length);
  state.catalogHasMore = Boolean(options.hasMore);

  if (!append) {
    list.innerHTML = "";
    state.renderedCatalogItems = [];
  }

  state.renderedCatalogItems = state.renderedCatalogItems.concat(items);
  resultCount.textContent = `${totalCount}개`;
  state.activeCatalogItemIds = state.renderedCatalogItems.map((item) => item.id);
  if (handlers.onSyncDetailNav) handlers.onSyncDetailNav();
  loadMoreWrap.classList.toggle("hidden", state.activeMode === "villagers" || !state.catalogHasMore);

  items.forEach((v) => {
    const fragment = catalogCardTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".card");
    card.classList.add("clickable");
    const icon = fragment.querySelector(".icon");
    const nameKo = fragment.querySelector(".name-ko");
    const nameEn = fragment.querySelector(".name-en");
    const meta = fragment.querySelector(".meta");
    const desc = fragment.querySelector(".description");
    const owned = fragment.querySelector(".owned");
    const ownedLabel = fragment.querySelector(".owned-label");
    const isArtMode = state.activeMode === "art";

    icon.src = v.image_url || "/static/no-image.svg";
    icon.addEventListener("error", () => {
      icon.src = "/static/no-image.svg";
    });

    nameKo.textContent = v.name_ko || v.name_en;
    nameEn.textContent = isArtMode ? "" : v.name_en ? `EN: ${v.name_en}` : "";

    const category = v.category_ko || v.category || "분류 없음";
    const ownedCount = Number(v.variation_owned_count || 0);
    const variationTotal = Number(v.variation_total || 0);
    const variationInfo = variationTotal ? ` | 변형: ${ownedCount}/${variationTotal}` : "";
    const authenticityInfo = v.authenticity_ko ? ` | ${v.authenticity_ko}` : "";
    meta.textContent = isArtMode ? "" : `분류: ${category}${authenticityInfo}${variationInfo}`;

    if (isArtMode) {
      desc.textContent = "";
      card.classList.add("art-card");
      icon.classList.add("art-icon");
      nameKo.classList.add("art-title");
    } else if (v.event_type || v.date) {
      const parts = [];
      if (v.event_type) parts.push(`타입: ${v.event_type}`);
      if (v.date) parts.push(`날짜: ${v.date}`);
      if (v.event_country_ko) parts.push(`국가/문화권: ${v.event_country_ko}`);
      desc.textContent = parts.join(" | ");
    } else if (
      state.activeMode === "clothing" ||
      state.activeMode === "furniture" ||
      state.activeMode === "interior" ||
      state.activeMode === "tools"
    ) {
      desc.innerHTML = "";
      const base = document.createElement("span");
      base.textContent = v.source ? `획득처: ${v.source}` : "획득처 정보 없음";
      desc.appendChild(base);
      if (v.source_notes) {
        const note = document.createElement("span");
        note.className = "note-hint";
        note.textContent = " ⓘ";
        note.setAttribute("data-tooltip", v.source_notes);
        note.setAttribute("tabindex", "0");
        note.setAttribute("role", "button");
        note.setAttribute("aria-label", v.source_notes);
        note.addEventListener("click", (e) => e.stopPropagation());
        desc.appendChild(note);
      }
    } else if (Array.isArray(v.styles_ko) && v.styles_ko.length) {
      const labelThemes =
        Array.isArray(v.label_themes_ko) && v.label_themes_ko.length ? v.label_themes_ko.join(", ") : "-";
      desc.textContent = `스타일: ${v.styles_ko.join(", ")} | 라벨: ${labelThemes}`;
    } else {
      desc.textContent = v.sell ? `판매가: ${v.sell}` : "";
    }

    const isPartialOwned = variationTotal > 0 && ownedCount > 0 && ownedCount < variationTotal;

    owned.checked = Boolean(v.owned);
    owned.indeterminate = isPartialOwned;
    ownedLabel.textContent = isPartialOwned ? "일부 보유" : statusLabel;
    if (isPartialOwned) {
      card.classList.add("partially-owned");
    }
    owned.addEventListener("change", async () => {
      owned.indeterminate = false;
      ownedLabel.textContent = statusLabel;
      card.classList.remove("partially-owned");
      if (!handlers.onToggleOwned) return;
      await handlers.onToggleOwned(v.id, owned.checked);
    });

    card.addEventListener("click", (e) => {
      if (e.target && e.target.closest("input, label, button")) return;
      if (handlers.onOpenDetail) handlers.onOpenDetail(v.id);
    });

    list.appendChild(fragment);
  });
}

export function fillSelect(selectEl, firstLabel, rows, preserveValue = "") {
  selectEl.innerHTML = "";
  const first = document.createElement("option");
  first.value = "";
  first.textContent = firstLabel;
  selectEl.appendChild(first);

  rows.forEach((row) => {
    const opt = document.createElement("option");
    opt.value = row.en;
    opt.textContent = row.ko ? `${row.ko} (${row.en})` : row.en;
    selectEl.appendChild(opt);
  });

  if (preserveValue) {
    const hasValue = rows.some((row) => row.en === preserveValue);
    if (hasValue) selectEl.value = preserveValue;
  }
}

export function renderSubCategoryTabs(catalogType, categories, { onCategoryChange } = {}) {
  const enabled = state.subCategoryEnabledModes.has(catalogType);
  subCategoryTabs.innerHTML = "";
  subCategoryTabs.classList.toggle("hidden", !enabled);
  if (!enabled) {
    state.activeSubCategory = "";
    return;
  }

  const saved = state.subCategoryStateByMode[catalogType] || "";
  const categorySet = new Set((categories || []).map((x) => x.en));
  state.activeSubCategory = categorySet.has(saved) ? saved : "";

  const rows = [...(categories || [])];
  rows.forEach((row) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `tab ${state.activeSubCategory === row.en ? "active" : ""}`;
    btn.dataset.category = row.en;
    btn.textContent = row.ko ? `${row.ko}` : row.en;
    btn.addEventListener("click", () => {
      state.activeSubCategory = row.en;
      state.subCategoryStateByMode[catalogType] = row.en;
      Array.from(subCategoryTabs.querySelectorAll(".tab")).forEach((el) => {
        el.classList.toggle("active", el === btn);
      });
      if (onCategoryChange) onCategoryChange(row.en);
    });
    subCategoryTabs.appendChild(btn);
  });
}
