import {
  addSubPlayerBtn,
  cancelSubPlayerBtn,
  clearPlayerFormBtn,
  birthdayDayInput,
  birthdayMonthInput,
  effectiveDateTimeText,
  gameDateTimeInput,
  hemisphereSelect,
  homeIslandNameText,
  homeIslandResidents,
  homeIslandResidentCountText,
  homeMainPlayerBirthdayText,
  homeMainPlayerText,
  homeResidentPickerBackdrop,
  homeResidentPickerCloseBtn,
  homeResidentPickerList,
  homeResidentPickerModal,
  homeResidentPickerStatus,
  homeResidentPersonalitySelect,
  homeResidentSearchInput,
  homeResidentSpeciesSelect,
  homeResidentStatus,
  islandNameInput,
  playerBirthdayDayInput,
  playerBirthdayMonthInput,
  playerList,
  playerNameInput,
  playerStatus,
  openSettingsModalBtn,
  settingsModal,
  settingsModalBackdrop,
  settingsModalCloseBtn,
  nicknameInput,
  openEventsFromHomeBtn,
  profileStatus,
  representativeFlowerInput,
  representativeFruitInput,
  setNowGameTimeBtn,
  saveProfileBtn,
  savePlayerBtn,
  summaryBloomingShrubs,
  summaryBloomingShrubsText,
  summaryCatalogProgress,
  homeCreatureTabs,
  homeCreatureOwnedFilter,
  homeCreatureDonatedFilter,
  homeCreatureStatus,
  homeCreatureTableBody,
  summaryNookShopping,
  summarySeasonText,
  summarySeasonalRecipes,
  summarySeasonalRecipesText,
  summaryUpcomingEvents,
  summaryZodiacText,
  subPlayerForm,
  timeTravelEnabledInput,
} from "./dom.js";
import { state } from "./state.js";
import { getEffectiveNow, normalizeMonthDay, toDateTimeLocalValue } from "./utils.js";

let effectiveTimer = null;
let editingPlayerId = null;
let residentActionBound = false;
let residentPickerMetaLoaded = false;
let homeResidentItems = [];
let homeCreatureActionBound = false;
let homeCreatureLoader = null;

function notifyEffectiveDateChanged() {
  window.dispatchEvent(new CustomEvent("acnh:effective-date-changed"));
}

function parseBoolFilter(value) {
  const text = String(value || "").trim().toLowerCase();
  if (text === "true") return true;
  if (text === "false") return false;
  return null;
}

function daysInMonth(monthValue) {
  const month = Number.parseInt(String(monthValue || ""), 10);
  if (!Number.isFinite(month) || month < 1 || month > 12) return 0;
  if (month === 2) return 29;
  if ([4, 6, 9, 11].includes(month)) return 30;
  return 31;
}

function fillMonthDayOptions(monthSelect, daySelect) {
  if (!monthSelect || !daySelect) return;
  if (monthSelect.options.length <= 1) {
    for (let month = 1; month <= 12; month += 1) {
      const opt = document.createElement("option");
      opt.value = String(month).padStart(2, "0");
      opt.textContent = `${month}월`;
      monthSelect.appendChild(opt);
    }
  }
  updateDayOptions(monthSelect, daySelect);
}

function updateDayOptions(monthSelect, daySelect) {
  if (!monthSelect || !daySelect) return;
  const maxDay = daysInMonth(monthSelect.value);
  const prev = String(daySelect.value || "");
  daySelect.innerHTML = '<option value="">일</option>';
  for (let day = 1; day <= maxDay; day += 1) {
    const opt = document.createElement("option");
    opt.value = String(day).padStart(2, "0");
    opt.textContent = `${day}일`;
    daySelect.appendChild(opt);
  }
  if (prev && Number(prev) <= maxDay) {
    daySelect.value = prev;
  }
}

function setMonthDayValue(monthSelect, daySelect, monthDay) {
  const normalized = normalizeMonthDay(monthDay);
  if (!normalized) {
    monthSelect.value = "";
    daySelect.value = "";
    return;
  }
  const [month, day] = normalized.split("-");
  monthSelect.value = month || "";
  updateDayOptions(monthSelect, daySelect);
  daySelect.value = day || "";
}

function getMonthDayValue(monthSelect, daySelect) {
  const month = String(monthSelect?.value || "");
  const day = String(daySelect?.value || "");
  if (!month || !day) return "";
  return `${month}-${day}`;
}

function openSettingsModal() {
  if (!settingsModal) return;
  settingsModal.classList.remove("hidden");
  settingsModal.setAttribute("aria-hidden", "false");
}

function closeSettingsModal() {
  if (!settingsModal) return;
  settingsModal.classList.add("hidden");
  settingsModal.setAttribute("aria-hidden", "true");
}

function renderEffectiveDateTime() {
  const now = getEffectiveNow(state);
  const source = state.timeTravelEnabled ? "타임슬립 기준" : "실시간 기준";
  effectiveDateTimeText.textContent = `${source}: ${now.toLocaleString("ko-KR")}`;
}

function renderHomeSimpleOverview() {
  homeIslandNameText.textContent = `섬 이름: ${state.homeIslandName || "미설정"}`;
  const mainPlayer = (state.players || []).find((p) => p.is_main) || null;
  const repName = mainPlayer?.name || state.homeRepresentativeName || "미등록";
  const repBirthday = mainPlayer?.birthday || state.homeRepresentativeBirthday || "-";
  homeMainPlayerText.textContent = `주민대표: ${repName}`;
  homeMainPlayerBirthdayText.textContent = `주민대표 생일: ${repBirthday}`;
}

function renderHomeIslandResidents(
  payload,
  { onOpenVillagerDetail, onRemoveResident, onOpenPicker, onReorder } = {}
) {
  const items = Array.isArray(payload?.items) ? payload.items : [];
  if (homeIslandResidentCountText) {
    homeIslandResidentCountText.textContent = `${items.length}/10`;
  }
  homeIslandResidents.innerHTML = "";
  if (!items.length) {
    const p = document.createElement("p");
    p.className = "profile-status";
    p.textContent = "현재 섬 주민이 없습니다.";
    homeIslandResidents.appendChild(p);
  } else {
    items.forEach((v, idx) => {
      const card = document.createElement("article");
      card.className = "home-resident-card clickable";
      const cardId = String(v.id || "");
      card.dataset.villagerId = cardId;
      card.draggable = Boolean(onReorder);
      const img = document.createElement("img");
      img.alt = "주민 이미지";
      img.src = v.icon_uri || v.image_uri || "/static/no-image.svg";
      img.addEventListener("error", () => {
        img.src = "/static/no-image.svg";
      });
      const thumbWrap = document.createElement("div");
      thumbWrap.className = "home-resident-thumb-wrap";
      const name = document.createElement("p");
      name.textContent = v.name_ko || v.name_en || "-";
      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "home-resident-remove-btn";
      removeBtn.setAttribute("aria-label", "섬 주민 삭제");
      removeBtn.textContent = "×";
      removeBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        if (onRemoveResident) await onRemoveResident(v);
      });
      if (onReorder) {
        card.addEventListener("dragstart", (e) => {
          card.classList.add("dragging");
          if (e.dataTransfer) {
            e.dataTransfer.effectAllowed = "move";
            e.dataTransfer.setData("text/plain", cardId);
          }
        });
        card.addEventListener("dragend", () => {
          card.classList.remove("dragging");
        });
        card.addEventListener("dragover", (e) => {
          e.preventDefault();
          card.classList.add("drag-over");
        });
        card.addEventListener("dragleave", () => {
          card.classList.remove("drag-over");
        });
        card.addEventListener("drop", async (e) => {
          e.preventDefault();
          e.stopPropagation();
          card.classList.remove("drag-over");
          const fromId = String(e.dataTransfer?.getData("text/plain") || "");
          const toId = cardId;
          if (!fromId || fromId === toId) return;
          const orderedIds = items.map((x) => String(x.id || ""));
          const from = orderedIds.indexOf(fromId);
          const to = orderedIds.indexOf(toId);
          if (from < 0 || to < 0) return;
          const [moved] = orderedIds.splice(from, 1);
          orderedIds.splice(to, 0, moved);
          await onReorder(orderedIds);
        });
      }
      card.addEventListener("click", () => {
        if (onOpenVillagerDetail) onOpenVillagerDetail(v, items);
      });
      thumbWrap.append(img, removeBtn);
      card.append(thumbWrap, name);
      homeIslandResidents.appendChild(card);
    });
  }

  if (items.length < 10) {
    const addCard = document.createElement("button");
    addCard.type = "button";
    addCard.className = "home-resident-add-card";
    addCard.setAttribute("aria-label", "섬 주민 추가");
    addCard.textContent = "+";
    addCard.addEventListener("click", () => {
      if (onOpenPicker) onOpenPicker();
    });
    homeIslandResidents.appendChild(addCard);
  }
}

function openResidentPickerModal() {
  if (!homeResidentPickerModal) return;
  homeResidentPickerModal.classList.remove("hidden");
  homeResidentPickerModal.setAttribute("aria-hidden", "false");
}

function closeResidentPickerModal() {
  if (!homeResidentPickerModal) return;
  homeResidentPickerModal.classList.add("hidden");
  homeResidentPickerModal.setAttribute("aria-hidden", "true");
}

function fillResidentPickerSelect(selectEl, firstLabel, rows) {
  if (!selectEl) return;
  selectEl.innerHTML = "";
  const first = document.createElement("option");
  first.value = "";
  first.textContent = firstLabel;
  selectEl.appendChild(first);
  rows.forEach((row) => {
    const opt = document.createElement("option");
    opt.value = row.en;
    opt.textContent = `${row.ko} (${row.en})`;
    selectEl.appendChild(opt);
  });
}

function renderResidentPickerList(items, { onAdd } = {}) {
  if (!homeResidentPickerList) return;
  const residents = Array.isArray(homeResidentItems) ? homeResidentItems : [];
  const residentIds = new Set(residents.map((x) => String(x.id || "")));
  const candidates = (Array.isArray(items) ? items : []).filter(
    (v) => !residentIds.has(String(v.id || ""))
  );
  homeResidentPickerList.innerHTML = "";
  if (!candidates.length) {
    const p = document.createElement("p");
    p.className = "profile-status";
    p.textContent = "조건에 맞는 주민이 없습니다.";
    homeResidentPickerList.appendChild(p);
    return;
  }
  candidates.forEach((v) => {
    const card = document.createElement("article");
    card.className = "home-resident-picker-card";

    const img = document.createElement("img");
    img.alt = "주민 이미지";
    img.src = v.icon_uri || v.image_uri || "/static/no-image.svg";
    img.addEventListener("error", () => {
      img.src = "/static/no-image.svg";
    });

    const nameKo = document.createElement("p");
    nameKo.className = "name-ko";
    nameKo.textContent = v.name_ko || v.name_en || "-";

    const nameEn = document.createElement("p");
    nameEn.className = "name-en";
    nameEn.textContent = v.name_en ? `EN: ${v.name_en}` : "";

    const meta = document.createElement("p");
    meta.className = "meta";
    meta.textContent = `${v.species_ko || v.species || "-"} | ${v.personality_ko || v.personality || "-"}`;

    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.textContent = "등록";
    addBtn.disabled = residents.length >= 10;
    addBtn.addEventListener("click", async () => {
      if (onAdd) await onAdd(v);
    });

    card.append(img, nameKo, nameEn, meta, addBtn);
    homeResidentPickerList.appendChild(card);
  });
}

export function applyIslandProfile(profile) {
  const p = profile || {};
  const nowLocal = toDateTimeLocalValue(new Date());
  fillMonthDayOptions(birthdayMonthInput, birthdayDayInput);
  fillMonthDayOptions(playerBirthdayMonthInput, playerBirthdayDayInput);
  islandNameInput.value = p.island_name || "";
  state.homeIslandName = p.island_name || "";
  state.homeRepresentativeName = p.nickname || "";
  state.homeRepresentativeBirthday = normalizeMonthDay(p.birthday || "");
  nicknameInput.value = p.nickname || "";
  representativeFruitInput.value = p.representative_fruit || "";
  representativeFlowerInput.value = p.representative_flower || "";
  setMonthDayValue(birthdayMonthInput, birthdayDayInput, p.birthday || "");
  hemisphereSelect.value = p.hemisphere === "south" ? "south" : "north";
  state.timeTravelEnabled = Boolean(p.time_travel_enabled);
  state.gameDateTime = p.game_datetime || nowLocal;
  timeTravelEnabledInput.checked = state.timeTravelEnabled;
  gameDateTimeInput.value = state.gameDateTime;
  gameDateTimeInput.disabled = !state.timeTravelEnabled;
  renderEffectiveDateTime();
  notifyEffectiveDateChanged();
  renderHomeSimpleOverview();
}

export async function loadIslandProfile(getIslandProfile) {
  const profile = await getIslandProfile();
  applyIslandProfile(profile);
  state.islandProfileLoaded = true;
}

function resetPlayerForm() {
  editingPlayerId = null;
  playerNameInput.value = "";
  setMonthDayValue(playerBirthdayMonthInput, playerBirthdayDayInput, "");
  savePlayerBtn.textContent = "부주 등록";
}

function openSubPlayerForm() {
  if (!subPlayerForm) return;
  subPlayerForm.classList.remove("hidden");
}

function closeSubPlayerForm() {
  if (!subPlayerForm) return;
  subPlayerForm.classList.add("hidden");
  resetPlayerForm();
}

function renderPlayerList(players, handlers = {}) {
  const rows = (Array.isArray(players) ? players : []).filter((p) => Boolean(p?.is_sub));
  playerList.innerHTML = "";
  if (!rows.length) {
    const li = document.createElement("li");
    li.textContent = "등록된 부주 플레이어가 없습니다.";
    playerList.appendChild(li);
    return;
  }

  rows.forEach((p) => {
    const li = document.createElement("li");
    const parts = [];
    parts.push(p.name || "-");
    if (p.birthday) parts.push(`(생일: ${p.birthday})`);
    li.append(document.createTextNode(parts.join(" ")));

    const editBtn = document.createElement("button");
    editBtn.type = "button";
    editBtn.textContent = "편집";
    editBtn.addEventListener("click", () => {
      openSubPlayerForm();
      editingPlayerId = p.id;
      playerNameInput.value = p.name || "";
      setMonthDayValue(playerBirthdayMonthInput, playerBirthdayDayInput, p.birthday || "");
      savePlayerBtn.textContent = "부주 수정";
    });

    const delBtn = document.createElement("button");
    delBtn.type = "button";
    delBtn.textContent = "삭제";
    delBtn.addEventListener("click", async () => {
      if (handlers.onDelete) await handlers.onDelete(p.id);
    });

    li.append(" ", editBtn, " ", delBtn);
    playerList.appendChild(li);
  });
}

export async function loadPlayers(getPlayers, handlers = {}) {
  const players = await getPlayers();
  state.players = players;
  renderPlayerList(players, handlers);
  renderHomeSimpleOverview();
}

function renderHomeSummary(summary) {
  const data = summary || {};
  summarySeasonText.textContent = data.season_ko || "-";
  summaryZodiacText.textContent = data.zodiac_ko || "-";

  const renderEventList = (target, rows, emptyText) => {
    target.innerHTML = "";
    if (!rows.length) {
      const li = document.createElement("li");
      li.textContent = emptyText;
      target.appendChild(li);
      return;
    }
    rows.forEach((row) => {
      const li = document.createElement("li");
      const name = row.name_ko || row.name_en || "-";
      const date = row.date || "-";
      const dday = Number.isFinite(row.delta_days) ? `D-${row.delta_days}` : "";
      li.textContent = `${name} | ${date} ${dday}`.trim();
      target.appendChild(li);
    });
  };

  const events = Array.isArray(data.upcoming_events) ? data.upcoming_events : [];
  renderEventList(summaryUpcomingEvents, events, "예정 이벤트 없음");

  const shopping = Array.isArray(data.nook_shopping_today) ? data.nook_shopping_today : [];
  renderEventList(summaryNookShopping, shopping, "오늘 너굴 쇼핑 항목 없음");

  const toRecipeLabel = (value) => {
    if (!value) return "";
    if (typeof value === "string") return value;
    if (typeof value === "object") {
      return String(value.name_ko || value.name_en || value.name || value.theme || "").trim();
    }
    return String(value).trim();
  };

  const recipes = (Array.isArray(data.seasonal_recipes_now) ? data.seasonal_recipes_now : [])
    .map((x) => toRecipeLabel(x))
    .filter(Boolean);
  summarySeasonalRecipes.innerHTML = "";
  if (!recipes.length) {
    const li = document.createElement("li");
    li.textContent = "현재 가능한 시즌 레시피 없음";
    summarySeasonalRecipes.appendChild(li);
  } else {
    recipes.forEach((name) => {
      const li = document.createElement("li");
      li.textContent = String(name);
      summarySeasonalRecipes.appendChild(li);
    });
  }
  if (summarySeasonalRecipesText) {
    const recipeNames = recipes.slice(0, 2).map((name) => String(name)).filter(Boolean);
    summarySeasonalRecipesText.textContent = recipeNames.length
      ? recipeNames.join(", ")
      : "없음";
  }

  summaryBloomingShrubs.innerHTML = "";
  const shrubs = Array.isArray(data.blooming_shrubs_now) ? data.blooming_shrubs_now : [];
  if (summaryBloomingShrubsText) {
    summaryBloomingShrubsText.textContent = shrubs.length ? shrubs.join(", ") : "없음";
  }
  if (!shrubs.length) {
    const li = document.createElement("li");
    li.textContent = "현재 개화 중인 낮은 나무 없음";
    summaryBloomingShrubs.appendChild(li);
  } else {
    shrubs.forEach((name) => {
      const li = document.createElement("li");
      li.textContent = String(name);
      summaryBloomingShrubs.appendChild(li);
    });
  }

  summaryCatalogProgress.innerHTML = "";
  const progressRows = Array.isArray(data.catalog_progress) ? data.catalog_progress : [];
  progressRows.forEach((row) => {
    const item = document.createElement("article");
    item.className = "progress-item";
    item.title = "클릭하면 해당 카탈로그로 이동";
    item.addEventListener("click", () => {
      const mode = String(row.catalog_type || "");
      window.dispatchEvent(new CustomEvent("acnh:navigate-mode", { detail: { mode } }));
    });

    const label = document.createElement("p");
    label.className = "label";
    label.textContent = `${row.label || row.catalog_type || "-"}`;
    const meta = document.createElement("p");
    meta.className = "meta";
    const owned = Number(row.owned || 0);
    const total = Number(row.total || 0);
    const partial = Number(row.partial || 0);
    const rate = Number(row.completion_rate || 0);
    meta.textContent = `${owned}/${total} (${rate}%) | 일부 보유 ${partial}`;
    item.append(label, meta);
    summaryCatalogProgress.appendChild(item);
  });
}

export async function loadHomeSummary(getHomeSummary) {
  const summary = await getHomeSummary();
  renderHomeSummary(summary);
}

function renderHomeCreatureRows(payload) {
  if (!homeCreatureTableBody) return;
  const rows = Array.isArray(payload?.items) ? payload.items : [];
  homeCreatureTableBody.innerHTML = "";

  if (!rows.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 8;
    td.className = "home-creature-empty";
    td.textContent = "조건에 맞는 출현 생물이 없습니다.";
    tr.appendChild(td);
    homeCreatureTableBody.appendChild(tr);
  } else {
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      const typeLabelMap = { bugs: "곤충", fish: "물고기", sea: "해산물" };
      const typeLabel = typeLabelMap[String(row.catalog_type || "")] || "-";

      const nameTd = document.createElement("td");
      nameTd.textContent = `${row.name_ko || row.name_en || "-"} (${typeLabel})`;

      const iconTd = document.createElement("td");
      const icon = document.createElement("img");
      icon.className = "home-creature-icon";
      icon.loading = "lazy";
      icon.decoding = "async";
      icon.alt = row.name_ko || row.name_en || "생물";
      icon.src = row.icon_url || "/static/no-image.svg";
      icon.addEventListener("error", () => {
        icon.src = "/static/no-image.svg";
      });
      iconTd.appendChild(icon);

      const sizeTd = document.createElement("td");
      sizeTd.textContent = row.size || "-";
      const locationTd = document.createElement("td");
      locationTd.textContent = row.location || "-";
      const timeTd = document.createElement("td");
      timeTd.textContent = row.time || "-";
      const monthsTd = document.createElement("td");
      monthsTd.textContent = row.months || "-";
      const ownedTd = document.createElement("td");
      ownedTd.textContent = row.owned ? "예" : "아니오";
      const donatedTd = document.createElement("td");
      donatedTd.textContent = row.donated ? "예" : "아니오";

      tr.append(nameTd, iconTd, sizeTd, locationTd, timeTd, monthsTd, ownedTd, donatedTd);
      homeCreatureTableBody.appendChild(tr);
    });
  }

  if (homeCreatureStatus) {
    const count = Number(payload?.count || rows.length || 0);
    const dt = String(payload?.effective_datetime || "").trim();
    homeCreatureStatus.textContent = `총 ${count}종${dt ? ` | 기준 시각: ${dt}` : ""}`;
  }
}

export async function loadHomeCreaturesNow(getHomeCreaturesNow) {
  if (typeof getHomeCreaturesNow !== "function") return;
  const params = { catalog_type: state.homeCreatureType || "all" };
  const ownedFilter = parseBoolFilter(state.homeCreatureOwnedFilter);
  const donatedFilter = parseBoolFilter(state.homeCreatureDonatedFilter);
  if (ownedFilter !== null) params.owned = ownedFilter;
  if (donatedFilter !== null) params.donated = donatedFilter;
  if (homeCreatureStatus) homeCreatureStatus.textContent = "출현 생물 로딩 중...";
  const payload = await getHomeCreaturesNow(params);
  renderHomeCreatureRows(payload);
}

export async function loadHomeIslandResidents(
  getHomeIslandResidents,
  {
    onOpenVillagerDetail,
    getVillagerMeta,
    getVillagers,
    updateVillagerState,
    updateIslandResidentOrder,
  } = {}
) {
  const refresh = async () =>
    loadHomeIslandResidents(getHomeIslandResidents, {
      onOpenVillagerDetail,
      getVillagerMeta,
      getVillagers,
      updateVillagerState,
      updateIslandResidentOrder,
    });

  const ensureResidentPickerMeta = async () => {
    if (residentPickerMetaLoaded || !getVillagerMeta) return;
    const meta = await getVillagerMeta();
    fillResidentPickerSelect(homeResidentPersonalitySelect, "성격 전체", meta.personalities || []);
    const species = [...(meta.species || [])].sort((a, b) =>
      (a.ko || a.en).localeCompare(b.ko || b.en, "ko")
    );
    fillResidentPickerSelect(homeResidentSpeciesSelect, "종 전체", species);
    residentPickerMetaLoaded = true;
  };

  const reloadPicker = async () => {
    if (!getVillagers) return;
    const data = await getVillagers({
      on_island: false,
      q: homeResidentSearchInput?.value?.trim() || "",
      personality: homeResidentPersonalitySelect?.value || "",
      species: homeResidentSpeciesSelect?.value || "",
    });
    renderResidentPickerList(data?.items || [], {
      onAdd: async (villager) => {
        if (!updateVillagerState) return;
        homeResidentPickerStatus.textContent = "";
        try {
          await updateVillagerState(String(villager.id || ""), { on_island: true });
          await refresh();
          await reloadPicker();
        } catch (err) {
          const msg = String(err?.message || "");
          if (msg.includes("최대 10명")) {
            homeResidentPickerStatus.textContent = "현재 섬 주민은 최대 10명까지 등록할 수 있습니다.";
          } else {
            homeResidentPickerStatus.textContent = "주민 등록에 실패했습니다.";
          }
        }
      },
    });
  };

  const openPicker = async () => {
    await ensureResidentPickerMeta();
    openResidentPickerModal();
    await reloadPicker();
  };

  const payload = await getHomeIslandResidents();
  const residents = Array.isArray(payload?.items) ? payload.items : [];
  homeResidentItems = residents;
  renderHomeIslandResidents(payload, {
    onOpenVillagerDetail,
    onOpenPicker: () => {
      openPicker().catch((err) => console.error(err));
    },
    onRemoveResident: async (villager) => {
      if (!updateVillagerState) return;
      homeResidentStatus.textContent = "";
      try {
        await updateVillagerState(String(villager.id || ""), { on_island: false });
        await refresh();
      } catch (err) {
        homeResidentStatus.textContent = "주민 삭제에 실패했습니다.";
      }
    },
    onReorder: async (orderedIds) => {
      if (!updateIslandResidentOrder) return;
      try {
        await updateIslandResidentOrder(orderedIds);
        await refresh();
      } catch (err) {
        homeResidentStatus.textContent = "주민 순서 변경에 실패했습니다.";
      }
    },
  });

  if (!residentActionBound) {
    residentActionBound = true;
    if (homeResidentPickerCloseBtn) {
      homeResidentPickerCloseBtn.addEventListener("click", closeResidentPickerModal);
    }
    if (homeResidentPickerBackdrop) {
      homeResidentPickerBackdrop.addEventListener("click", closeResidentPickerModal);
    }
    if (homeResidentSearchInput) {
      homeResidentSearchInput.addEventListener("input", () => {
        reloadPicker().catch((err) => console.error(err));
      });
    }
    if (homeResidentPersonalitySelect) {
      homeResidentPersonalitySelect.addEventListener("change", () => {
        reloadPicker().catch((err) => console.error(err));
      });
    }
    if (homeResidentSpeciesSelect) {
      homeResidentSpeciesSelect.addEventListener("change", () => {
        reloadPicker().catch((err) => console.error(err));
      });
    }
  }
}

export function bindHomeEvents({
  updateIslandProfile,
  getHomeSummary,
  getHomeCreaturesNow,
  getPlayers,
  savePlayer,
  deletePlayer,
}) {
  if (typeof getHomeCreaturesNow === "function") {
    homeCreatureLoader = getHomeCreaturesNow;
  }
  fillMonthDayOptions(birthdayMonthInput, birthdayDayInput);
  fillMonthDayOptions(playerBirthdayMonthInput, playerBirthdayDayInput);
  resetPlayerForm();
  birthdayMonthInput.addEventListener("change", () => updateDayOptions(birthdayMonthInput, birthdayDayInput));
  playerBirthdayMonthInput.addEventListener("change", () =>
    updateDayOptions(playerBirthdayMonthInput, playerBirthdayDayInput)
  );
  const saveProfile = async () => {
    const saved = await updateIslandProfile({
      island_name: islandNameInput.value.trim(),
      nickname: nicknameInput.value.trim(),
      representative_fruit: representativeFruitInput.value,
      representative_flower: representativeFlowerInput.value,
      birthday: getMonthDayValue(birthdayMonthInput, birthdayDayInput),
      hemisphere: hemisphereSelect.value === "south" ? "south" : "north",
      time_travel_enabled: Boolean(timeTravelEnabledInput.checked),
      game_datetime: gameDateTimeInput.value || "",
    });
    applyIslandProfile(saved);
    if (getHomeSummary) {
      await loadHomeSummary(getHomeSummary);
    }
    if (homeCreatureLoader) {
      await loadHomeCreaturesNow(homeCreatureLoader);
    }
  };

  if (!effectiveTimer) {
    effectiveTimer = setInterval(renderEffectiveDateTime, 1000);
  }
  if (openSettingsModalBtn) {
    openSettingsModalBtn.addEventListener("click", openSettingsModal);
  }
  if (settingsModalBackdrop) {
    settingsModalBackdrop.addEventListener("click", closeSettingsModal);
  }
  if (settingsModalCloseBtn) {
    settingsModalCloseBtn.addEventListener("click", closeSettingsModal);
  }
  if (openEventsFromHomeBtn) {
    openEventsFromHomeBtn.addEventListener("click", () => {
      window.dispatchEvent(new CustomEvent("acnh:navigate-mode", { detail: { mode: "events" } }));
    });
  }
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && settingsModal && !settingsModal.classList.contains("hidden")) {
      closeSettingsModal();
    }
  });
  timeTravelEnabledInput.addEventListener("change", () => {
    state.timeTravelEnabled = Boolean(timeTravelEnabledInput.checked);
    if (state.timeTravelEnabled && !gameDateTimeInput.value) {
      const now = toDateTimeLocalValue(new Date());
      gameDateTimeInput.value = now;
      state.gameDateTime = now;
    }
    gameDateTimeInput.disabled = !state.timeTravelEnabled;
    renderEffectiveDateTime();
    notifyEffectiveDateChanged();
    if (homeCreatureLoader) {
      loadHomeCreaturesNow(homeCreatureLoader).catch((err) => console.error(err));
    }
  });
  gameDateTimeInput.addEventListener("change", () => {
    state.gameDateTime = gameDateTimeInput.value || "";
    renderEffectiveDateTime();
    notifyEffectiveDateChanged();
    if (homeCreatureLoader) {
      loadHomeCreaturesNow(homeCreatureLoader).catch((err) => console.error(err));
    }
  });
  setNowGameTimeBtn.addEventListener("click", () => {
    profileStatus.textContent = "저장 중...";
    const now = toDateTimeLocalValue(new Date());
    gameDateTimeInput.value = now;
    state.gameDateTime = now;
    renderEffectiveDateTime();
    notifyEffectiveDateChanged();
    if (homeCreatureLoader) {
      loadHomeCreaturesNow(homeCreatureLoader).catch((err) => console.error(err));
    }
    saveProfile()
      .then(() => {
        profileStatus.textContent = "현재 시간으로 저장되었습니다.";
        setTimeout(() => {
          if (profileStatus.textContent === "현재 시간으로 저장되었습니다.") profileStatus.textContent = "";
        }, 1500);
      })
      .catch((err) => {
        console.error(err);
        profileStatus.textContent = `저장에 실패했습니다. ${err?.message || ""}`.trim();
      });
  });

  saveProfileBtn.addEventListener("click", async () => {
    profileStatus.textContent = "저장 중...";
    try {
      await saveProfile();
      profileStatus.textContent = "저장되었습니다.";
      setTimeout(() => {
        if (profileStatus.textContent === "저장되었습니다.") profileStatus.textContent = "";
      }, 1500);
    } catch (err) {
      console.error(err);
      profileStatus.textContent = `저장에 실패했습니다. ${err?.message || ""}`.trim();
    }
  });

  const reloadPlayers = async () => {
    await loadPlayers(getPlayers, {
      onDelete: async (playerId) => {
        await deletePlayer(playerId);
        await reloadPlayers();
      },
    });
  };

  if (subPlayerForm) {
    subPlayerForm.classList.add("hidden");
  }
  addSubPlayerBtn.addEventListener("click", () => {
    const subCount = (state.players || []).filter((p) => Boolean(p?.is_sub)).length;
    if (subCount >= 7 && !editingPlayerId) {
      playerStatus.textContent = "부주 플레이어는 최대 7명까지 등록할 수 있습니다.";
      return;
    }
    playerStatus.textContent = "";
    resetPlayerForm();
    openSubPlayerForm();
  });
  cancelSubPlayerBtn.addEventListener("click", () => {
    playerStatus.textContent = "";
    closeSubPlayerForm();
  });

  savePlayerBtn.addEventListener("click", async () => {
    playerStatus.textContent = "저장 중...";
    try {
      await savePlayer({
        id: editingPlayerId,
        name: playerNameInput.value.trim(),
        birthday: getMonthDayValue(playerBirthdayMonthInput, playerBirthdayDayInput),
        is_main: false,
        is_sub: true,
      });
      await reloadPlayers();
      closeSubPlayerForm();
      playerStatus.textContent = "부주 플레이어가 저장되었습니다.";
      setTimeout(() => {
        if (playerStatus.textContent === "부주 플레이어가 저장되었습니다.") playerStatus.textContent = "";
      }, 1500);
    } catch (err) {
      console.error(err);
      playerStatus.textContent = `부주 저장 실패: ${err?.message || ""}`.trim();
    }
  });

  clearPlayerFormBtn.addEventListener("click", () => {
    resetPlayerForm();
    playerStatus.textContent = "";
  });

  if (!homeCreatureActionBound) {
    homeCreatureActionBound = true;
    homeCreatureTabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        state.homeCreatureType = String(tab.dataset.type || "all");
        homeCreatureTabs.forEach((x) => x.classList.toggle("active", x === tab));
        if (homeCreatureLoader) {
          loadHomeCreaturesNow(homeCreatureLoader).catch((err) => console.error(err));
        }
      });
    });
    homeCreatureOwnedFilter?.addEventListener("change", () => {
      state.homeCreatureOwnedFilter = String(homeCreatureOwnedFilter.value || "");
      if (homeCreatureLoader) {
        loadHomeCreaturesNow(homeCreatureLoader).catch((err) => console.error(err));
      }
    });
    homeCreatureDonatedFilter?.addEventListener("change", () => {
      state.homeCreatureDonatedFilter = String(homeCreatureDonatedFilter.value || "");
      if (homeCreatureLoader) {
        loadHomeCreaturesNow(homeCreatureLoader).catch((err) => console.error(err));
      }
    });
  }
}
