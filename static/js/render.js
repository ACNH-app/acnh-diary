import {
  catalogCardTemplate,
  catalogPanel,
  homePanel,
  list,
  loadMoreWrap,
  mobileBottomNav,
  mobileNavSheet,
  mobileNavSheetBackdrop,
  navBreadcrumb,
  resultCount,
  scrollTopBtn,
  subCategoryTabs,
  topNav,
  villagerCardTemplate,
  villagerPanel,
} from "./dom.js";
import { state } from "./state.js";

let navDismissHandlersBound = false;
const mobileNavQuery = window.matchMedia("(max-width: 768px)");
const tapNavQuery = window.matchMedia("(hover: none), (pointer: coarse)");
let villagerRenderToken = 0;
const monthToNumber = {
  january: 1,
  february: 2,
  march: 3,
  april: 4,
  may: 5,
  june: 6,
  july: 7,
  august: 8,
  september: 9,
  october: 10,
  november: 11,
  december: 12,
};

function parseBirthdayNumberPart(value) {
  const text = String(value || "").trim().toLowerCase();
  if (!text) return 0;
  const directNum = Number.parseInt(text, 10);
  if (Number.isFinite(directNum) && directNum > 0) return directNum;
  const monthNum = monthToNumber[text];
  if (Number.isFinite(monthNum) && monthNum > 0) return monthNum;
  const numMatch = text.match(/(\d{1,2})/);
  if (numMatch) {
    const parsed = Number.parseInt(numMatch[1], 10);
    if (Number.isFinite(parsed) && parsed > 0) return parsed;
  }
  return 0;
}

function formatVillagerBirthday(v) {
  const month = parseBirthdayNumberPart(v?.birthday_month);
  const day = parseBirthdayNumberPart(v?.birthday_day);
  if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
    return `${month}/${day}`;
  }
  const raw = String(v?.birthday || "").trim();
  if (!raw) return "";
  const match = raw.match(/(\d{1,2}).*?(\d{1,2})/);
  if (match) {
    const m = Number.parseInt(match[1], 10);
    const d = Number.parseInt(match[2], 10);
    if (Number.isFinite(m) && Number.isFinite(d) && m >= 1 && m <= 12 && d >= 1 && d <= 31) {
      return `${m}/${d}`;
    }
  }
  const parts = raw.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    const m = parseBirthdayNumberPart(parts[0]);
    const d = parseBirthdayNumberPart(parts[1]);
    if (m >= 1 && m <= 12 && d >= 1 && d <= 31) return `${m}/${d}`;
  }
  return raw;
}

function buildNavGroups(modes) {
  const rows = Array.isArray(modes) ? modes : [];
  const byKey = new Map(rows.map((m) => [m.key, m]));
  const used = new Set();
  const pick = (keys) =>
    keys
      .map((key) => byKey.get(key))
      .filter(Boolean)
      .filter((m) => {
        if (used.has(m.key)) return false;
        used.add(m.key);
        return true;
      });

  const groups = [];
  // 홈은 브랜드 버튼에서만 진입한다.
  pick(["home"]);
  const villagerModes = pick(["villagers"]);
  const encyclopediaModes = pick(["fossils", "bugs", "fish", "sea", "art"]);
  const catalogModes = pick([
    "furniture",
    "interior",
    "clothing",
    "music",
    "items",
    "tools",
    "special_items",
    "gyroids",
    "photos",
    "recipes",
    "reactions",
  ]);
  // 이벤트는 상단 네비에서 숨기고 홈 캘린더에서만 진입한다.
  pick(["events"]);
  if (villagerModes.length) groups.push({ key: "villagers", label: "주민", modes: villagerModes });
  if (encyclopediaModes.length) groups.push({ key: "encyclopedia", label: "도감", modes: encyclopediaModes });
  if (catalogModes.length) groups.push({ key: "catalog", label: "카탈로그", modes: catalogModes });
  groups.push({ key: "more", label: "기타", modes: [] });
  return groups;
}

function syncActivePrimaryFromMode() {
  const key = state.activeMode;
  if (key === "home") {
    state.nav.activePrimaryKey = "";
    return;
  }
  const hit = state.nav.groups.find((g) => (g.modes || []).some((m) => m.key === key));
  if (hit) {
    state.nav.activePrimaryKey = hit.key;
    return;
  }
  state.nav.activePrimaryKey = state.nav.groups[0]?.key || "home";
}

function syncLegacyNavState() {
  state.navGroups = state.nav.groups;
  state.activePrimaryNav = state.nav.activePrimaryKey;
  state.openNavPrimaryKey = state.nav.openPrimaryKey;
}

function clearOpenPrimary() {
  state.nav.openPrimaryKey = "";
}

function getModeByKey(modeKey) {
  return (state.navModes || []).find((mode) => mode.key === modeKey) || null;
}

function updateNavBreadcrumb() {
  if (!navBreadcrumb) return;
  if (state.activeMode === "home") {
    navBreadcrumb.textContent = "";
    navBreadcrumb.classList.add("hidden");
    return;
  }
  const mode = getModeByKey(state.activeMode);
  const activeGroup = state.nav.groups.find((g) => g.key === state.nav.activePrimaryKey) || null;
  const modeInGroup = activeGroup?.modes?.some((m) => m.key === state.activeMode);
  const text = modeInGroup && activeGroup
    ? `${activeGroup.label} > ${mode?.label || state.activeMode}`
    : mode?.label || state.activeMode;
  state.nav.breadcrumb = text;
  navBreadcrumb.textContent = text;
  navBreadcrumb.classList.remove("hidden");
}

function mobileEntryIcon(key) {
  if (key === "home") return "/static/icons/nav-home-leaf.svg";
  if (key === "villagers") return "/static/icons/nav-villager-face.svg";
  if (key === "encyclopedia") return "/static/icons/nav-encyclopedia-fossil.svg";
  if (key === "catalog") return "/static/icons/shopping_icon.png";
  if (key === "more") return "/static/icons/nav-more-bell.svg";
  return "/static/no-image.svg";
}

function getMobileEntries() {
  const entries = [
    { key: "home", label: "홈", modes: [{ key: "home", label: "홈" }] },
    ...state.nav.groups,
  ];
  return entries.slice(0, 5);
}

function renderMobileBottomNav({ onModeChange } = {}) {
  if (!mobileBottomNav || !mobileNavSheet || !mobileNavSheetBackdrop) return;
  const entries = getMobileEntries();

  mobileBottomNav.classList.remove("hidden");
  mobileBottomNav.innerHTML = "";

  const menu = document.createElement("div");
  menu.className = "mobile-nav-menu";

  entries.forEach((entry) => {
    const hasSubmenu = (entry.modes || []).length > 1;
    const isHome = entry.key === "home";
    const isActive = isHome ? state.activeMode === "home" : state.nav.activePrimaryKey === entry.key;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `mobile-nav-btn ${isActive ? "active" : ""}`;
    btn.dataset.primary = entry.key;

    const icon = document.createElement("span");
    icon.className = "mobile-nav-icon";
    const iconImg = document.createElement("img");
    iconImg.className = "mobile-nav-icon-img";
    iconImg.src = mobileEntryIcon(entry.key);
    iconImg.alt = `${entry.label} 아이콘`;
    iconImg.loading = "lazy";
    icon.appendChild(iconImg);
    btn.appendChild(icon);

    const label = document.createElement("span");
    label.className = "mobile-nav-label";
    label.textContent = entry.label;
    btn.appendChild(label);

    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (isHome) {
        clearOpenPrimary();
        state.activeMode = "home";
        state.nav.activePrimaryKey = "";
        syncLegacyNavState();
        renderNav({ onModeChange });
        if (onModeChange) onModeChange("home");
        return;
      }

      state.nav.activePrimaryKey = entry.key;
      if (!hasSubmenu) {
        clearOpenPrimary();
        const target = entry.modes?.[0]?.key || "";
        if (!target) {
          renderNav({ onModeChange });
          return;
        }
        state.activeMode = target;
        syncLegacyNavState();
        renderNav({ onModeChange });
        if (onModeChange) onModeChange(target);
        return;
      }
      state.nav.openPrimaryKey = state.nav.openPrimaryKey === entry.key ? "" : entry.key;
      syncLegacyNavState();
      renderNav({ onModeChange });
    });

    menu.appendChild(btn);
  });

  mobileBottomNav.appendChild(menu);

  const activeSheetEntry = entries.find(
    (entry) => entry.key === state.nav.openPrimaryKey && (entry.modes || []).length > 1
  );

  if (!activeSheetEntry) {
    mobileNavSheet.classList.add("hidden");
    mobileNavSheetBackdrop.classList.add("hidden");
    mobileNavSheet.setAttribute("aria-hidden", "true");
    mobileNavSheet.innerHTML = "";
    return;
  }

  mobileNavSheetBackdrop.classList.remove("hidden");
  mobileNavSheet.classList.remove("hidden");
  mobileNavSheet.setAttribute("aria-hidden", "false");
  mobileNavSheet.innerHTML = "";

  const panel = document.createElement("div");
  panel.className = "mobile-nav-sheet-panel";

  const title = document.createElement("p");
  title.className = "mobile-nav-sheet-title";
  title.textContent = activeSheetEntry.label;
  panel.appendChild(title);

  const listWrap = document.createElement("div");
  listWrap.className = "mobile-nav-sheet-list";

  activeSheetEntry.modes.forEach((mode) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `mobile-nav-sheet-btn ${mode.key === state.activeMode ? "active" : ""}`;
    btn.textContent = mode.label;
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      state.activeMode = mode.key;
      state.nav.activePrimaryKey = activeSheetEntry.key;
      clearOpenPrimary();
      syncLegacyNavState();
      renderNav({ onModeChange });
      if (onModeChange) onModeChange(mode.key);
    });
    listWrap.appendChild(btn);
  });

  panel.appendChild(listWrap);
  mobileNavSheet.appendChild(panel);
}

export function updateScrollTopButton() {
  if (!scrollTopBtn) return;
  const shouldShow = window.scrollY > 320;
  scrollTopBtn.classList.toggle("hidden", !shouldShow);
}

export function renderNav({ onModeChange } = {}) {
  if (!navDismissHandlersBound) {
    document.addEventListener("click", (e) => {
      const clickedInTopNav = topNav && topNav.contains(e.target);
      const clickedInBottomNav = mobileBottomNav && mobileBottomNav.contains(e.target);
      const clickedInSheet = mobileNavSheet && mobileNavSheet.contains(e.target);
      const clickedNavControl =
        e.target &&
        e.target.closest &&
        e.target.closest(".nav-trigger, .nav-submenu, .mobile-nav-btn, .mobile-nav-sheet-panel");
      if (!(clickedInTopNav || clickedInBottomNav || clickedInSheet) || !clickedNavControl) {
        clearOpenPrimary();
        const openItems = topNav ? topNav.querySelectorAll(".nav-item.open") : [];
        openItems.forEach((el) => el.classList.remove("open"));
        if (mobileNavSheet) mobileNavSheet.classList.add("hidden");
        if (mobileNavSheetBackdrop) mobileNavSheetBackdrop.classList.add("hidden");
      }
    });
    document.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      clearOpenPrimary();
      const openItems = topNav.querySelectorAll(".nav-item.open");
      openItems.forEach((el) => el.classList.remove("open"));
    });
    mobileNavQuery.addEventListener("change", () => {
      state.nav.isMobile = mobileNavQuery.matches;
      state.nav.isTapNav = tapNavQuery.matches || mobileNavQuery.matches;
      if (!state.nav.isTapNav) clearOpenPrimary();
      syncLegacyNavState();
      updateNavBreadcrumb();
      renderNav({ onModeChange });
    });
    tapNavQuery.addEventListener("change", () => {
      state.nav.isTapNav = tapNavQuery.matches || mobileNavQuery.matches;
      if (!state.nav.isTapNav) clearOpenPrimary();
      syncLegacyNavState();
      updateNavBreadcrumb();
      renderNav({ onModeChange });
    });
    if (mobileNavSheetBackdrop) {
      mobileNavSheetBackdrop.addEventListener("click", () => {
        clearOpenPrimary();
        syncLegacyNavState();
        renderNav({ onModeChange });
      });
    }
    navDismissHandlersBound = true;
  }

  state.nav.isMobile = mobileNavQuery.matches;
  state.nav.isTapNav = tapNavQuery.matches || mobileNavQuery.matches;
  state.nav.groups = buildNavGroups(state.navModes);
  syncActivePrimaryFromMode();
  if (!state.nav.isTapNav) clearOpenPrimary();
  syncLegacyNavState();
  updateNavBreadcrumb();

  if (state.nav.isMobile) {
    if (topNav) {
      topNav.innerHTML = "";
      topNav.classList.add("hidden");
    }
    renderMobileBottomNav({ onModeChange });
    return;
  }

  if (topNav) topNav.classList.remove("hidden");
  if (mobileBottomNav) {
    mobileBottomNav.classList.add("hidden");
    mobileBottomNav.innerHTML = "";
  }
  if (mobileNavSheet) {
    mobileNavSheet.classList.add("hidden");
    mobileNavSheet.innerHTML = "";
    mobileNavSheet.setAttribute("aria-hidden", "true");
  }
  if (mobileNavSheetBackdrop) mobileNavSheetBackdrop.classList.add("hidden");

  topNav.innerHTML = "";
  const menu = document.createElement("ul");
  menu.className = "nav-menu";

  state.nav.groups.forEach((group) => {
    const li = document.createElement("li");
    li.className = "nav-item";
    const modes = group.modes || [];
    const hasSubmenu = modes.length > 1;
    if (hasSubmenu) li.classList.add("has-submenu");
    if (group.key === state.nav.activePrimaryKey) li.classList.add("active");
    if (hasSubmenu && state.nav.openPrimaryKey === group.key) li.classList.add("open");

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "nav-trigger";
    trigger.dataset.primary = group.key;
    trigger.textContent = group.label;
    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      const prevOpenPrimary = state.nav.openPrimaryKey;
      state.nav.activePrimaryKey = group.key;
      if (group.key === "more" && !hasSubmenu) {
        clearOpenPrimary();
        syncLegacyNavState();
        updateNavBreadcrumb();
        renderNav({ onModeChange });
        return;
      }
      if (!hasSubmenu) {
        clearOpenPrimary();
        const target = modes[0]?.key || "";
        if (!target) return;
        state.activeMode = target;
        syncLegacyNavState();
        updateNavBreadcrumb();
        renderNav({ onModeChange });
        if (onModeChange) onModeChange(target);
        return;
      }
      if (!state.nav.isTapNav) return;
      state.nav.openPrimaryKey = prevOpenPrimary === group.key ? "" : group.key;
      syncLegacyNavState();
      renderNav({ onModeChange });
    });
    li.appendChild(trigger);

    if (hasSubmenu) {
      const sub = document.createElement("div");
      sub.className = "nav-submenu";
      modes.forEach((mode) => {
        const subBtn = document.createElement("button");
        subBtn.type = "button";
        subBtn.className = `nav-sub-btn ${mode.key === state.activeMode ? "active" : ""}`;
        subBtn.dataset.mode = mode.key;
        subBtn.textContent = mode.label;
        subBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          state.activeMode = mode.key;
          state.nav.activePrimaryKey = group.key;
          clearOpenPrimary();
          syncLegacyNavState();
          updateNavBreadcrumb();
          renderNav({ onModeChange });
          if (onModeChange) onModeChange(mode.key);
        });
        sub.appendChild(subBtn);
      });
      li.appendChild(sub);
    } else {
      trigger.classList.add("single");
      trigger.classList.toggle("active", modes[0]?.key === state.activeMode);
    }

    menu.appendChild(li);
  });
  topNav.appendChild(menu);
}

export function updatePanels() {
  syncActivePrimaryFromMode();
  syncLegacyNavState();
  updateNavBreadcrumb();
  document.body.dataset.activeMode = String(state.activeMode || "");

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

  const token = ++villagerRenderToken;
  const batchSize = 60;
  let index = 0;

  const appendBatch = () => {
    if (token !== villagerRenderToken) return;
    const fragment = document.createDocumentFragment();
    const end = Math.min(index + batchSize, items.length);

    for (; index < end; index += 1) {
      const v = items[index];
      const node = villagerCardTemplate.content.cloneNode(true);
      const card = node.querySelector(".card");
      card.classList.add("clickable");
      const icon = node.querySelector(".icon");
      const nameKo = node.querySelector(".name-ko");
      const nameEn = node.querySelector(".name-en");
      const meta = node.querySelector(".meta");
      const birthday = node.querySelector(".birthday");
      const likedBtn = node.querySelector(".liked");
      const onIslandBtn = node.querySelector(".on-island");
      const formerResidentBtn = node.querySelector(".former-resident");

      icon.loading = "lazy";
      icon.decoding = "async";
      icon.src = v.icon_uri || v.image_uri || "";
      icon.addEventListener("error", () => {
        if (icon.src !== v.image_uri && v.image_uri) icon.src = v.image_uri;
      });

      nameKo.textContent = v.name_ko || v.name_en;
      nameEn.textContent = "";
      const subtype = String(v.sub_personality || "").trim();
      meta.textContent = subtype
        ? `${v.species_ko} | ${v.personality_ko} | ${subtype}`
        : `${v.species_ko} | ${v.personality_ko}`;
      const birthdayText = formatVillagerBirthday(v);
      birthday.textContent = birthdayText ? `생일: ${birthdayText}` : "";

      const syncVillagerToggleButtons = () => {
        if (likedBtn) likedBtn.classList.toggle("active", Boolean(v.liked));
        if (onIslandBtn) onIslandBtn.classList.toggle("active", Boolean(v.on_island));
        if (formerResidentBtn) formerResidentBtn.classList.toggle("active", Boolean(v.former_resident));
      };
      syncVillagerToggleButtons();

      likedBtn?.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!onToggleState) return;
        v.liked = !Boolean(v.liked);
        syncVillagerToggleButtons();
        await onToggleState(v.id, { liked: Boolean(v.liked) });
      });
      onIslandBtn?.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!onToggleState) return;
        v.on_island = !Boolean(v.on_island);
        syncVillagerToggleButtons();
        await onToggleState(v.id, { on_island: Boolean(v.on_island) });
      });
      formerResidentBtn?.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!onToggleState) return;
        v.former_resident = !Boolean(v.former_resident);
        syncVillagerToggleButtons();
        await onToggleState(v.id, { former_resident: Boolean(v.former_resident) });
      });

      card.addEventListener("click", (e) => {
        if (e.target && e.target.closest("input, label, button")) return;
        if (onOpenDetail) onOpenDetail(v);
      });

      fragment.appendChild(node);
    }

    list.appendChild(fragment);
    if (index < items.length) {
      window.requestAnimationFrame(appendBatch);
    }
  };

  window.requestAnimationFrame(appendBatch);
}

export function renderCatalog(items, statusLabel, options = {}, handlers = {}) {
  const forceFiveCols = ["bugs", "fish", "sea", "recipes"].includes(state.activeMode);
  const musicMode = state.activeMode === "music";
  const activeSourceFilter = String(state.sourceFilterByMode?.[state.activeMode] || "").trim();
  list.classList.toggle("grid-five-cols", forceFiveCols);
  list.classList.toggle("grid-music-cards", musicMode);
  list.dataset.catalogMode = String(state.activeMode || "");

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
    card.dataset.itemId = String(v.id || "");
    const icon = fragment.querySelector(".icon");
    const nameKo = fragment.querySelector(".name-ko");
    const nameEn = fragment.querySelector(".name-en");
    const meta = fragment.querySelector(".meta");
    const desc = fragment.querySelector(".description");
    const owned = fragment.querySelector(".owned");
    if (owned) {
      owned.dataset.itemId = String(v.id || "");
    }
    const donated = fragment.querySelector(".donated");
    const donatedWrap = fragment.querySelector(".donated-wrap");
    const ownedLabel = fragment.querySelector(".owned-label");
    const ownedWrapLabel = owned ? owned.closest("label") : null;
    const qtyWrap = fragment.querySelector(".owned-qty-wrap");
    const qtyInput = fragment.querySelector(".owned-qty");
    const toggles = fragment.querySelector(".toggles");
    const isArtMode = state.activeMode === "art";
    const isFurnitureMode = state.activeMode === "furniture";
    const isMuseumMode = ["bugs", "fish", "sea"].includes(state.activeMode);
    const isMusicMode = musicMode;
    const isRecipeMode = state.activeMode === "recipes";

    icon.src = v.image_url || "/static/no-image.svg";
    icon.loading = "lazy";
    icon.decoding = "async";
    icon.addEventListener("error", () => {
      icon.src = "/static/no-image.svg";
    });

    nameKo.textContent = v.name_ko || v.name_en;
    nameEn.textContent =
      isArtMode || isMusicMode || state.activeMode === "recipes"
        ? ""
        : v.name_en
          ? `EN: ${v.name_en}`
          : "";

    const category = v.category_ko || v.category || "분류 없음";
    const ownedCount = Number(v.variation_owned_count || 0);
    const variationTotal = Number(v.variation_total || 0);
    const variationQtyTotal = Number(v.variation_quantity_total || 0);
    const variationInfo = variationTotal ? ` | 변형: ${ownedCount}/${variationTotal}` : "";
    const authenticityInfo = v.authenticity_ko ? ` | ${v.authenticity_ko}` : "";
    meta.textContent = isArtMode || isMusicMode ? "" : `분류: ${category}${authenticityInfo}${variationInfo}`;

    if (isArtMode) {
      desc.textContent = "";
      card.classList.add("art-card");
      icon.classList.add("art-icon");
      nameKo.classList.add("art-title");
    } else if (isMusicMode) {
      const buyNum = Number(v.buy || 0);
      const buyPrice = buyNum > 0 ? buyNum.toLocaleString("ko-KR") : "-";
      if (v.not_for_sale) {
        desc.innerHTML = `<span class=\"music-pill-not-sale\">비매품</span>`;
      } else {
        desc.textContent = `구매가: ${buyPrice}벨`;
      }
      card.classList.add("music-card");
      icon.classList.add("music-icon");
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
      state.activeMode === "tools" ||
      state.activeMode === "recipes"
    ) {
      desc.innerHTML = "";
      const buildSourceNoteHint = (noteText) => {
        const safeNote = String(noteText || "").trim();
        if (!safeNote) return null;
        const note = document.createElement("span");
        note.className = "note-hint";
        note.textContent = " ⓘ";
        note.setAttribute("data-tooltip", safeNote);
        note.setAttribute("tabindex", "0");
        note.setAttribute("role", "button");
        note.setAttribute("aria-label", safeNote);
        note.addEventListener("click", (e) => e.stopPropagation());
        return note;
      };
      if (
        state.activeMode === "recipes"
        && (v.source || (Array.isArray(v.source_pairs) && v.source_pairs.length))
      ) {
        const label = document.createElement("span");
        label.textContent = "획득방법: ";
        desc.appendChild(label);
        const pairs = Array.isArray(v.source_pairs)
          ? v.source_pairs
            .map((p) => ({
              source: String(p?.source || "").trim(),
              note: String(p?.note || "").trim(),
            }))
            .filter((p) => p.source || p.note)
          : [];
        if (pairs.length) {
          pairs.forEach((pair, idx) => {
            if (pair.source) {
              const chip = document.createElement("button");
              chip.type = "button";
              chip.className = `source-chip ${activeSourceFilter === pair.source ? "active" : ""}`;
              chip.textContent = pair.source;
              chip.addEventListener("click", async (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (!handlers.onFilterBySource) return;
                await handlers.onFilterBySource(pair.source);
              });
              desc.appendChild(chip);
            }
            const noteHint = buildSourceNoteHint(pair.note);
            if (noteHint) {
              desc.appendChild(noteHint);
            }
            if (idx < pairs.length - 1) {
              desc.appendChild(document.createTextNode(", "));
            }
          });
        } else {
          const sources = String(v.source || "")
            .split(",")
            .map((x) => String(x || "").trim())
            .filter(Boolean);
          const noteHint = buildSourceNoteHint(v.source_notes);
          sources.forEach((src, idx) => {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = `source-chip ${activeSourceFilter === src ? "active" : ""}`;
            chip.textContent = src;
            chip.addEventListener("click", async (e) => {
              e.preventDefault();
              e.stopPropagation();
              if (!handlers.onFilterBySource) return;
              await handlers.onFilterBySource(src);
            });
            desc.appendChild(chip);
            if (idx === 0 && noteHint) {
              desc.appendChild(noteHint);
            }
            if (idx < sources.length - 1) {
              desc.appendChild(document.createTextNode(", "));
            }
          });
        }
      } else {
        const base = document.createElement("span");
        base.textContent = v.source ? `획득방법: ${v.source}` : "획득방법 정보 없음";
        desc.appendChild(base);
        const noteHint = buildSourceNoteHint(v.source_notes);
        if (noteHint) desc.appendChild(noteHint);
      }
      if (isRecipeMode && v.materials_preview) {
        const mat = document.createElement("div");
        mat.className = "recipe-materials";
        mat.textContent = `재료: ${v.materials_preview}`;
        desc.appendChild(document.createElement("br"));
        desc.appendChild(mat);
      }
    } else if (state.activeMode === "reactions") {
      const src = v.reaction_source || v.source || "획득방법 정보 없음";
      const parts = [`획득방법: ${src}`];
      if (v.event_type) parts.push(`연관 이벤트: ${v.event_type}`);
      if (v.date) parts.push(`버전: ${v.date}`);
      desc.textContent = parts.join(" | ");
    } else if (Array.isArray(v.styles_ko) && v.styles_ko.length) {
      const labelThemes =
        Array.isArray(v.label_themes_ko) && v.label_themes_ko.length ? v.label_themes_ko.join(", ") : "-";
      desc.textContent = `스타일: ${v.styles_ko.join(", ")} | 라벨: ${labelThemes}`;
    } else {
      desc.textContent = v.sell ? `판매가: ${v.sell}` : "";
    }
    if (v.not_for_sale && !isMusicMode && state.activeMode !== "recipes") {
      const tag = document.createElement("span");
      tag.className = "music-pill-not-sale";
      tag.textContent = "비매품";
      if (desc.firstChild) {
        desc.insertBefore(document.createTextNode(" "), desc.firstChild);
      }
      desc.insertBefore(tag, desc.firstChild);
    }

    const isPartialOwned = variationTotal > 0 && ownedCount > 0 && ownedCount < variationTotal;

    owned.checked = Boolean(v.owned);
    owned.indeterminate = isPartialOwned;
    if (isRecipeMode) {
      card.classList.add("recipe-card");
      if (ownedWrapLabel) {
        ownedWrapLabel.classList.add("owned-overlay");
        ownedWrapLabel.classList.toggle("checked", owned.checked);
      }
      if (ownedLabel) {
        ownedLabel.textContent = "✓";
      }
    }
    if (isMusicMode) {
      ownedLabel.textContent = owned.checked ? "보유" : "미보유";
    } else {
      ownedLabel.textContent = isPartialOwned ? "일부 보유" : statusLabel;
      if (isRecipeMode && ownedLabel) {
        ownedLabel.textContent = "✓";
      }
    }
    if (donatedWrap) {
      donatedWrap.classList.toggle("hidden", !isMuseumMode);
    }
    if (donated) {
      donated.checked = Boolean(v.donated);
    }
    if (qtyWrap) {
      qtyWrap.classList.toggle("hidden", !isFurnitureMode);
      qtyWrap.hidden = !isFurnitureMode;
      qtyWrap.style.display = isFurnitureMode ? "inline-flex" : "none";
    }
    const effectiveQty = variationTotal > 0 ? variationQtyTotal : Math.max(0, Number(v.quantity || 0));
    if (qtyInput) {
      qtyInput.value = String(effectiveQty);
      qtyInput.readOnly = variationTotal > 0;
      qtyInput.disabled = variationTotal > 0;
      qtyInput.title = variationTotal > 0 ? "변형별 수량 합계입니다. 상세에서 수정하세요." : "";
    }
    if (isPartialOwned) {
      card.classList.add("partially-owned");
    }
    owned.addEventListener("change", async () => {
      owned.indeterminate = false;
      ownedLabel.textContent = isMusicMode ? (owned.checked ? "보유" : "미보유") : statusLabel;
      if (isRecipeMode && ownedWrapLabel) {
        ownedWrapLabel.classList.toggle("checked", owned.checked);
      }
      if (isRecipeMode && ownedLabel) {
        ownedLabel.textContent = "✓";
      }
      card.classList.remove("partially-owned");
      if (isFurnitureMode && qtyInput && variationTotal === 0) {
        const nextQty = owned.checked ? Math.max(1, Number(qtyInput.value || 0)) : 0;
        qtyInput.value = String(nextQty);
      }
      if (!handlers.onToggleOwned) return;
      await handlers.onToggleOwned(v.id, owned.checked, {
        quantity:
          isFurnitureMode && qtyInput && variationTotal === 0
            ? Math.max(0, Number(qtyInput.value || 0))
            : undefined,
      });
    });

    if (isMuseumMode && donated) {
      donated.addEventListener("change", async () => {
        if (!handlers.onToggleDonated) return;
        await handlers.onToggleDonated(v.id, donated.checked);
      });
    }

    if (isFurnitureMode && qtyInput && variationTotal === 0) {
      qtyInput.addEventListener("click", (e) => e.stopPropagation());
      qtyInput.addEventListener("change", async () => {
        const raw = Number(qtyInput.value || 0);
        const safeQty = Number.isFinite(raw) ? Math.max(0, Math.trunc(raw)) : 0;
        qtyInput.value = String(safeQty);
        owned.checked = safeQty > 0;
        owned.indeterminate = false;
        ownedLabel.textContent = statusLabel;
        if (!handlers.onUpdateQuantity) return;
        await handlers.onUpdateQuantity(v.id, safeQty);
      });
    }

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
  subCategoryTabs.classList.toggle(
    "is-slider",
    catalogType === "recipes" || catalogType === "special_items"
  );
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
      if (catalogType === "recipes" && state.sourceFilterByMode) {
        state.sourceFilterByMode[catalogType] = "";
      }
      Array.from(subCategoryTabs.querySelectorAll(".tab")).forEach((el) => {
        el.classList.toggle("active", el === btn);
      });
      if (onCategoryChange) onCategoryChange(row.en);
    });
    subCategoryTabs.appendChild(btn);
  });
}
