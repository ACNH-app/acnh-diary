const STORAGE_KEY = "acnh-villager-tracker-state-v1";
const collator = new Intl.Collator("ko");

const STATUS_META = [
  { key: "wish", short: "W", label: "위시 주민" },
  { key: "island", short: "I", label: "섬 주민" },
  { key: "camping", short: "C", label: "캠핑장 방문" },
  { key: "movedOut", short: "M", label: "이사간 주민" },
  { key: "photoGifted", short: "P", label: "사진 선물 받음" },
];

const elements = {
  summaryGrid: document.getElementById("summaryGrid"),
  resetStorageButton: document.getElementById("resetStorageButton"),
  searchInput: document.getElementById("searchInput"),
  groupBySelect: document.getElementById("groupBySelect"),
  personalityFilter: document.getElementById("personalityFilter"),
  speciesFilter: document.getElementById("speciesFilter"),
  statusFilter: document.getElementById("statusFilter"),
  activeFilters: document.getElementById("activeFilters"),
  listMeta: document.getElementById("listMeta"),
  groupList: document.getElementById("groupList"),
  detailBackdrop: document.getElementById("detailBackdrop"),
  detailPanel: document.getElementById("detailPanel"),
  detailContent: document.getElementById("detailContent"),
  closeDetailButton: document.getElementById("closeDetailButton"),
};

const appState = {
  villagers: [],
  villagerMap: new Map(),
  toggles: loadToggleState(),
  filters: {
    q: "",
    groupBy: "personality",
    personality: "",
    species: "",
    status: "",
  },
  detailId: null,
};

init().catch((error) => {
  console.error(error);
  elements.groupList.innerHTML = '<div class="empty-state">주민 데이터를 불러오지 못했습니다.</div>';
});

async function init() {
  bindEvents();
  const response = await fetch("./data/villagers.json");
  const payload = await response.json();
  appState.villagers = Array.isArray(payload?.items) ? payload.items : [];
  appState.villagerMap = new Map(appState.villagers.map((villager) => [String(villager.id), villager]));
  populateSelectOptions();
  render();
}

function bindEvents() {
  elements.searchInput.addEventListener("input", (event) => {
    appState.filters.q = String(event.target.value || "").trim();
    render();
  });

  elements.groupBySelect.addEventListener("change", (event) => {
    appState.filters.groupBy = String(event.target.value || "personality");
    render();
  });

  elements.personalityFilter.addEventListener("change", (event) => {
    appState.filters.personality = String(event.target.value || "");
    render();
  });

  elements.speciesFilter.addEventListener("change", (event) => {
    appState.filters.species = String(event.target.value || "");
    render();
  });

  elements.statusFilter.addEventListener("change", (event) => {
    appState.filters.status = String(event.target.value || "");
    render();
  });

  elements.resetStorageButton.addEventListener("click", () => {
    if (!window.confirm("저장된 주민 체크 상태를 모두 초기화할까요?")) return;
    appState.toggles = {};
    persistToggleState();
    render();
    if (appState.detailId) renderDetail(appState.detailId);
  });

  elements.groupList.addEventListener("click", (event) => {
    const toggleButton = event.target.closest("[data-toggle-key]");
    if (toggleButton) {
      const villagerId = String(toggleButton.dataset.villagerId || "");
      const toggleKey = String(toggleButton.dataset.toggleKey || "");
      if (villagerId && toggleKey) {
        updateToggle(villagerId, toggleKey);
      }
      return;
    }

    const detailButton = event.target.closest("[data-detail-id]");
    if (detailButton) {
      openDetail(String(detailButton.dataset.detailId || ""));
    }
  });

  elements.closeDetailButton.addEventListener("click", closeDetail);
  elements.detailBackdrop.addEventListener("click", closeDetail);
}

function loadToggleState() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch (error) {
    console.warn("Failed to parse localStorage state", error);
    return {};
  }
}

function persistToggleState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(appState.toggles));
}

function getVillagerState(villagerId) {
  return {
    wish: false,
    island: false,
    camping: false,
    movedOut: false,
    photoGifted: false,
    ...(appState.toggles[villagerId] || {}),
  };
}

function updateToggle(villagerId, toggleKey) {
  const current = getVillagerState(villagerId);
  const next = { ...current, [toggleKey]: !current[toggleKey] };

  if (toggleKey === "island" && next.island) next.movedOut = false;
  if (toggleKey === "movedOut" && next.movedOut) next.island = false;

  appState.toggles[villagerId] = next;
  persistToggleState();
  render();
  if (appState.detailId === villagerId) renderDetail(villagerId);
}

function populateSelectOptions() {
  const personalities = uniqueSorted(appState.villagers.map((villager) => villager.personalityKo));
  const species = uniqueSorted(appState.villagers.map((villager) => villager.speciesKo));

  personalities.forEach((value) => {
    elements.personalityFilter.appendChild(new Option(value, value));
  });

  species.forEach((value) => {
    elements.speciesFilter.appendChild(new Option(value, value));
  });
}

function uniqueSorted(values) {
  return [...new Set(values.filter(Boolean))].sort((a, b) => collator.compare(a, b));
}

function render() {
  renderSummary();
  renderActiveFilters();
  renderVillagerGroups();
}

function renderSummary() {
  const total = appState.villagers.length;
  const counts = STATUS_META.reduce((acc, item) => {
    acc[item.key] = 0;
    return acc;
  }, {});

  Object.keys(appState.toggles).forEach((villagerId) => {
    const state = getVillagerState(villagerId);
    STATUS_META.forEach((item) => {
      if (state[item.key]) counts[item.key] += 1;
    });
  });

  const cards = [
    { label: "전체 주민", value: total },
    { label: "위시 주민", value: counts.wish },
    { label: "섬 주민", value: counts.island },
    { label: "캠핑장 방문", value: counts.camping },
    { label: "이사간 주민", value: counts.movedOut },
    { label: "사진 선물 받음", value: counts.photoGifted },
  ];

  elements.summaryGrid.innerHTML = cards
    .map(
      (card) => `
        <article class="summary-card">
          <span class="label">${escapeHtml(card.label)}</span>
          <strong>${card.value}</strong>
        </article>
      `
    )
    .join("");
}

function renderActiveFilters() {
  const chips = [];
  if (appState.filters.groupBy === "personality") chips.push("성격별 보기");
  if (appState.filters.groupBy === "species") chips.push("동물종별 보기");
  if (appState.filters.q) chips.push(`검색: ${appState.filters.q}`);
  if (appState.filters.personality) chips.push(`성격: ${appState.filters.personality}`);
  if (appState.filters.species) chips.push(`동물종: ${appState.filters.species}`);

  const statusMeta = STATUS_META.find((item) => item.key === appState.filters.status);
  if (statusMeta) chips.push(`상태: ${statusMeta.label}`);

  elements.activeFilters.innerHTML = chips.length
    ? chips.map((chip) => `<span class="filter-pill">${escapeHtml(chip)}</span>`).join("")
    : '<span class="filter-pill">전체 주민 표시 중</span>';
}

function renderVillagerGroups() {
  const filtered = getFilteredVillagers();
  elements.listMeta.textContent = `${filtered.length}명의 주민이 현재 조건에 맞습니다.`;

  if (!filtered.length) {
    elements.groupList.innerHTML = '<div class="empty-state">조건에 맞는 주민이 없습니다.</div>';
    return;
  }

  const grouped = groupVillagers(filtered, appState.filters.groupBy);
  elements.groupList.innerHTML = grouped
    .map(([groupLabel, villagers]) => {
      const cards = villagers.map((villager) => renderVillagerCard(villager)).join("");
      return `
        <section class="group-section">
          <div class="group-head">
            <h3>${escapeHtml(groupLabel)}</h3>
            <span class="group-count">${villagers.length}명</span>
          </div>
          <div class="card-grid">${cards}</div>
        </section>
      `;
    })
    .join("");
}

function getFilteredVillagers() {
  const query = appState.filters.q.toLowerCase();
  return appState.villagers
    .filter((villager) => {
      if (
        query &&
        !`${villager.nameKo} ${villager.nameEn}`.toLowerCase().includes(query)
      ) {
        return false;
      }
      if (appState.filters.personality && villager.personalityKo !== appState.filters.personality) return false;
      if (appState.filters.species && villager.speciesKo !== appState.filters.species) return false;
      if (appState.filters.status && !getVillagerState(String(villager.id))[appState.filters.status]) return false;
      return true;
    })
    .sort((a, b) => collator.compare(a.nameKo || a.nameEn, b.nameKo || b.nameEn));
}

function groupVillagers(villagers, groupBy) {
  const map = new Map();
  villagers.forEach((villager) => {
    const key = groupBy === "species" ? villager.speciesKo : villager.personalityKo;
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(villager);
  });
  return [...map.entries()].sort((a, b) => collator.compare(a[0], b[0]));
}

function renderVillagerCard(villager) {
  const villagerId = String(villager.id);
  const state = getVillagerState(villagerId);
  const toggles = STATUS_META.map((item) => {
    const active = state[item.key] ? "active" : "";
    return `
      <button
        type="button"
        class="toggle-button ${active}"
        data-villager-id="${villagerId}"
        data-toggle-key="${item.key}"
        aria-label="${escapeHtml(item.label)}"
        title="${escapeHtml(item.label)}"
      >
        ${item.short}
      </button>
    `;
  }).join("");

  return `
    <article class="villager-card" style="--accent:${escapeHtml(villager.bubbleColor || "#2d7d52")}">
      <img class="villager-thumb" src="${escapeHtml(villager.imagePath)}" alt="${escapeHtml(villager.nameKo)}" loading="lazy" />
      <div class="villager-body">
        <div class="villager-name-row">
          <h4 class="villager-name">${escapeHtml(villager.nameKo)}</h4>
          <button type="button" class="detail-trigger" data-detail-id="${villagerId}">상세</button>
        </div>
        <p class="villager-subname">${escapeHtml(villager.nameEn)}</p>
        <p class="villager-meta">${escapeHtml(villager.personalityKo)} · ${escapeHtml(villager.speciesKo)} · ${escapeHtml(villager.gender)}</p>
        <p class="villager-birthday">생일 ${escapeHtml(villager.birthdayText || "-")}</p>
        <div class="status-strip">${toggles}</div>
      </div>
    </article>
  `;
}

function openDetail(villagerId) {
  appState.detailId = villagerId;
  renderDetail(villagerId);
  elements.detailBackdrop.classList.remove("hidden");
  elements.detailPanel.classList.remove("hidden");
  elements.detailPanel.setAttribute("aria-hidden", "false");
}

function closeDetail() {
  appState.detailId = null;
  elements.detailBackdrop.classList.add("hidden");
  elements.detailPanel.classList.add("hidden");
  elements.detailPanel.setAttribute("aria-hidden", "true");
}

function renderDetail(villagerId) {
  const villager = appState.villagerMap.get(String(villagerId));
  if (!villager) return;

  const state = getVillagerState(String(villagerId));
  const statusRow = STATUS_META.map((item) => {
    const active = state[item.key] ? "active" : "";
    return `<button type="button" class="detail-status ${active}" data-villager-id="${villagerId}" data-toggle-key="${item.key}">${escapeHtml(item.label)}</button>`;
  }).join("");

  const items = [
    ["성격", villager.personalityKo],
    ["동물종", villager.speciesKo],
    ["성별", villager.gender],
    ["취미", villager.hobby],
    ["생일", villager.birthdayText],
    ["말버릇", villager.catchphraseKo || villager.catchphraseEn || "-"],
    ["좌우명", villager.sayingKo || villager.sayingEn || "-"],
    ["영문 이름", villager.nameEn],
  ];

  elements.detailContent.innerHTML = `
    <section class="detail-hero">
      <img class="detail-image" src="${escapeHtml(villager.imagePath)}" alt="${escapeHtml(villager.nameKo)}" />
      <div>
        <h2 class="detail-name">${escapeHtml(villager.nameKo)}</h2>
        <p class="detail-subname">${escapeHtml(villager.nameEn)}</p>
        <p class="detail-copy">${escapeHtml(villager.personalityKo)} 성격의 ${escapeHtml(villager.speciesKo)} 주민입니다.</p>
        <div class="detail-status-row">${statusRow}</div>
      </div>
    </section>
    <section class="detail-grid">
      ${items
        .map(
          ([label, value]) => `
            <article class="detail-item">
              <span class="label">${escapeHtml(label)}</span>
              <strong>${escapeHtml(value || "-")}</strong>
            </article>
          `
        )
        .join("")}
    </section>
  `;

  elements.detailContent.querySelectorAll("[data-toggle-key]").forEach((button) => {
    button.addEventListener("click", () => {
      updateToggle(String(button.dataset.villagerId || ""), String(button.dataset.toggleKey || ""));
    });
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
