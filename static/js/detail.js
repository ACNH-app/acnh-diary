import {
  detailBackdrop,
  detailCloseBtn,
  detailExtraImages,
  detailExtraImagesSection,
  detailFields,
  detailImage,
  detailModal,
  detailNotForSaleTag,
  detailNavHint,
  detailNextBtn,
  detailPrevBtn,
  detailRawFields,
  detailSourceHint,
  detailTitle,
  detailVariationsSection,
  detailVariations,
  variationMarkAllBtn,
  variationUnmarkAllBtn,
} from "./dom.js";
import { state } from "./state.js";

/**
 * Detail modal controller for catalog item details and variation ownership state.
 * @param {{
 *   getJSON: (url: string, options?: RequestInit) => Promise<any>,
 *   updateCatalogState: (catalogType: string, itemId: string, payload: { owned?: boolean }) => Promise<any>,
 *   updateCatalogVariationState: (catalogType: string, itemId: string, variationId: string, payload: { owned?: boolean, quantity?: number }) => Promise<any>,
 *   updateCatalogVariationStateBatch: (catalogType: string, itemId: string, items: Array<{ variation_id: string, owned: boolean, quantity?: number }>) => Promise<any>,
 *   scheduleCatalogRefresh: (delayMs?: number) => void
 * }} deps
 */
export function createDetailController({
  getJSON,
  updateCatalogState,
  updateCatalogVariationState,
  updateCatalogVariationStateBatch,
  scheduleCatalogRefresh,
}) {
  const villagerImageCache = new Set();
  let photoCatalogRowsPromise = null;
  let villagerPhotoPosterRenderToken = 0;
  const favoriteColorMeta = {
    Aqua: { ko: "아쿠아", swatch: "#59dbe0" },
    Beige: { ko: "베이지", swatch: "#d9c7a4" },
    Black: { ko: "검정", swatch: "#222222" },
    Blue: { ko: "파랑", swatch: "#3b82f6" },
    Brown: { ko: "갈색", swatch: "#8b5a2b" },
    Colorful: {
      ko: "컬러풀",
      swatch: "linear-gradient(90deg,#ef4444,#f59e0b,#eab308,#22c55e,#3b82f6,#8b5cf6)",
    },
    Gray: { ko: "회색", swatch: "#8c8f98" },
    Green: { ko: "초록", swatch: "#22a34a" },
    Orange: { ko: "주황", swatch: "#f97316" },
    Pink: { ko: "분홍", swatch: "#ec4899" },
    Purple: { ko: "보라", swatch: "#8b5cf6" },
    Red: { ko: "빨강", swatch: "#ef4444" },
    White: { ko: "흰색", swatch: "#f8fafc" },
    Yellow: { ko: "노랑", swatch: "#eab308" },
  };
  const personalityActivityMeta = {
    Jock: {
      group_ko: "남성",
      personality_ko: "운동광",
      wake_up: "오전 6:30",
      sleep: "오전 12:30",
      note: "가장 먼저 일어나 운동을 시작합니다.",
    },
    Lazy: {
      group_ko: "남성",
      personality_ko: "먹보",
      wake_up: "오전 8:00",
      sleep: "오후 11:00",
      note: "느긋하게 일어나 일찍 잠드는 편입니다.",
    },
    Smug: {
      group_ko: "남성",
      personality_ko: "느끼함",
      wake_up: "오전 7:00",
      sleep: "오전 2:00",
      note: "활동 시간이 꽤 긴 편입니다.",
    },
    Cranky: {
      group_ko: "남성",
      personality_ko: "무뚝뚝",
      wake_up: "오전 9:00",
      sleep: "오전 3:30",
      note: "아주 늦게 일어나고 아주 늦게 잡니다.",
    },
    Normal: {
      group_ko: "여성",
      personality_ko: "친절함",
      wake_up: "오전 6:00",
      sleep: "오전 12:00",
      note: "섬에서 가장 먼저 일어나는 성격입니다.",
    },
    Peppy: {
      group_ko: "여성",
      personality_ko: "아이돌",
      wake_up: "오전 7:00",
      sleep: "오전 1:30",
      note: "아침 일찍부터 활동적입니다.",
    },
    Snooty: {
      group_ko: "여성",
      personality_ko: "성숙함",
      wake_up: "오전 8:30",
      sleep: "오전 2:30",
      note: "밤늦게까지 산책하는 모습을 자주 보입니다.",
    },
    Sisterly: {
      group_ko: "여성",
      personality_ko: "단순활발",
      wake_up: "오전 9:30",
      sleep: "오전 3:00",
      note: "가장 늦게 일어나는 '늦잠꾸러기'입니다.",
    },
    "Big sister": {
      group_ko: "여성",
      personality_ko: "단순활발",
      wake_up: "오전 9:30",
      sleep: "오전 3:00",
      note: "가장 늦게 일어나는 '늦잠꾸러기'입니다.",
    },
    Uchi: {
      group_ko: "여성",
      personality_ko: "단순활발",
      wake_up: "오전 9:30",
      sleep: "오전 3:00",
      note: "가장 늦게 일어나는 '늦잠꾸러기'입니다.",
    },
  };

  function getPersonalityActivity(v) {
    const keyEn = String(v.personality || "").trim();
    const keyKo = String(v.personality_ko || "").trim();
    const byEn = personalityActivityMeta[keyEn];
    if (byEn) return byEn;
    return Object.values(personalityActivityMeta).find((x) => x.personality_ko === keyKo) || null;
  }

  function preloadImage(url) {
    const src = String(url || "").trim();
    if (!src || villagerImageCache.has(src)) return;
    const img = new Image();
    img.onload = () => {
      villagerImageCache.add(src);
    };
    img.onerror = () => {};
    img.src = src;
  }

  function prefetchNeighborVillagerImages() {
    const idx = getActiveDetailIndex();
    if (idx < 0) return;
    const neighbors = [state.renderedVillagers?.[idx - 1], state.renderedVillagers?.[idx + 1]].filter(Boolean);
    neighbors.forEach((v) => {
      preloadImage(v.icon_uri);
      preloadImage(v.image_uri);
      preloadImage(v.house_exterior_url);
      preloadImage(v.house_interior_url);
    });
  }

  function setVillagerDetailImage(v, currentVillagerId) {
    const lowRes = v.icon_uri || v.image_uri || "/static/no-image.svg";
    const highRes = v.image_uri || "";
    detailImage.src = lowRes;
    detailImage.onerror = () => {
      detailImage.src = "/static/no-image.svg";
    };
    preloadImage(lowRes);
    if (!highRes || highRes === lowRes) return;
    if (villagerImageCache.has(highRes)) {
      detailImage.src = highRes;
      return;
    }
    const hi = new Image();
    hi.onload = () => {
      villagerImageCache.add(highRes);
      if (state.activeDetailItemId === currentVillagerId) {
        detailImage.src = highRes;
      }
    };
    hi.onerror = () => {};
    hi.src = highRes;
  }

  function normalizeLooseText(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9가-힣]/g, "");
  }

  function detectPhotoPosterKind(row) {
    const category = String(row?.category || "").trim().toLowerCase();
    const nameEn = String(row?.name_en || "").trim().toLowerCase();
    const nameKo = String(row?.name_ko || "").trim();
    if (category.includes("poster") || nameEn.includes("poster") || nameKo.includes("포스터")) {
      return "poster";
    }
    if (category.includes("photo") || nameEn.includes("photo") || nameKo.includes("사진")) {
      return "photo";
    }
    return "";
  }

  async function ensurePhotoCatalogRows() {
    if (!photoCatalogRowsPromise) {
      photoCatalogRowsPromise = getJSON("/api/catalog/photos?sort_by=name&sort_order=asc&page=1&page_size=5000")
        .then((payload) => (Array.isArray(payload?.items) ? payload.items : []))
        .catch((err) => {
          console.error(err);
          return [];
        });
    }
    return photoCatalogRowsPromise;
  }

  function findVillagerPhotoPosterRows(villager, rows) {
    const villagerNameKo = String(villager?.name_ko || "").trim();
    const villagerNameEn = String(villager?.name_en || "").trim();
    const villagerNameKoNorm = normalizeLooseText(villagerNameKo);
    const villagerNameEnNorm = normalizeLooseText(villagerNameEn);
    const out = [];

    for (const row of rows || []) {
      const kind = detectPhotoPosterKind(row);
      if (!kind) continue;
      const rowNameKo = String(row?.name_ko || row?.name || "").trim();
      const rowNameEn = String(row?.name_en || row?.name || "").trim();
      const rowKoNorm = normalizeLooseText(rowNameKo);
      const rowEnNorm = normalizeLooseText(rowNameEn);
      const matchedKo = villagerNameKoNorm && rowKoNorm.includes(villagerNameKoNorm);
      const matchedEn = villagerNameEnNorm && rowEnNorm.includes(villagerNameEnNorm);
      if (!(matchedKo || matchedEn)) continue;
      out.push({
        ...row,
        _kind: kind,
      });
    }

    // 같은 종류에서 중복이 있을 수 있으므로 id 기준 중복 제거
    const byId = new Map();
    out.forEach((row) => {
      const id = String(row?.id || "").trim();
      if (!id) return;
      if (!byId.has(id)) byId.set(id, row);
    });
    return Array.from(byId.values()).sort((a, b) => {
      const ak = a._kind === "photo" ? 0 : 1;
      const bk = b._kind === "photo" ? 0 : 1;
      if (ak !== bk) return ak - bk;
      return String(a?.name_ko || a?.name_en || "").localeCompare(
        String(b?.name_ko || b?.name_en || ""),
        "ko"
      );
    });
  }

  function formatBells(value) {
    const n = Number(value || 0);
    if (!Number.isFinite(n) || n <= 0) return "-";
    return `${n.toLocaleString("ko-KR")}벨`;
  }

  function formatAcquireText(item) {
    const pairs = Array.isArray(item?.source_pairs)
      ? item.source_pairs
        .map((p) => ({
          source: String(p?.source || "").trim(),
          note: String(p?.note || "").trim(),
        }))
        .filter((p) => p.source || p.note)
      : [];
    if (pairs.length) {
      return pairs
        .map((p) => {
          if (p.source && p.note) return `${p.source} (${p.note})`;
          return p.source || p.note;
        })
        .join(", ");
    }
    const source = String(item?.source || "").trim();
    const note = String(item?.source_notes || "").trim();
    if (source && note) return `${source} (${note})`;
    return source || note || "-";
  }

  async function renderVillagerPhotoPosterSection(v, currentVillagerId) {
    const token = ++villagerPhotoPosterRenderToken;
    const rows = await ensurePhotoCatalogRows();
    if (
      token !== villagerPhotoPosterRenderToken
      || state.activeDetailType !== "villager"
      || state.activeDetailItemId !== currentVillagerId
    ) {
      return;
    }

    const items = findVillagerPhotoPosterRows(v, rows);
    if (!items.length) return;

    const section = document.createElement("section");
    section.className = "detail-villager-photo-section";

    const title = document.createElement("p");
    title.className = "detail-field";
    title.textContent = "주민 사진/포스터";
    section.appendChild(title);

    const listWrap = document.createElement("div");
    listWrap.className = "detail-villager-photo-list";

    items.forEach((item) => {
      const card = document.createElement("article");
      card.className = "detail-villager-photo-card";

      const img = document.createElement("img");
      img.className = "detail-villager-photo-image";
      img.src = String(item?.image_url || "/static/no-image.svg");
      img.alt = String(item?.name_ko || item?.name_en || "아이템");
      img.loading = "lazy";
      img.decoding = "async";
      img.onerror = () => {
        img.src = "/static/no-image.svg";
      };

      const body = document.createElement("div");
      body.className = "detail-villager-photo-body";

      const itemName = document.createElement("p");
      itemName.className = "detail-villager-photo-name";
      const kindLabel = item?._kind === "poster" ? "포스터" : "사진";
      itemName.textContent = `${kindLabel}: ${item?.name_ko || item?.name_en || "-"}`;

      const sell = document.createElement("p");
      sell.className = "detail-villager-photo-meta";
      sell.textContent = `판매가: ${formatBells(item?.sell)}`;

      const buy = document.createElement("p");
      buy.className = "detail-villager-photo-meta";
      buy.textContent = item?.not_for_sale
        ? "구매가: 비매품"
        : `구매가: ${formatBells(item?.buy)}`;

      const source = document.createElement("p");
      source.className = "detail-villager-photo-meta";
      source.textContent = `획득방법: ${formatAcquireText(item)}`;

      const control = document.createElement("button");
      control.type = "button";
      control.className = `detail-villager-photo-owned ${item?.owned ? "active" : ""}`;
      control.textContent = item?.owned ? "보유" : "미보유";
      control.addEventListener("click", async () => {
        const nextOwned = !Boolean(item?.owned);
        control.disabled = true;
        try {
          await updateCatalogState("photos", String(item?.id || ""), { owned: nextOwned });
          item.owned = nextOwned;
          const targetId = String(item?.id || "");
          rows.forEach((row) => {
            if (String(row?.id || "") === targetId) {
              row.owned = nextOwned;
            }
          });
          control.classList.toggle("active", nextOwned);
          control.textContent = nextOwned ? "보유" : "미보유";
          scheduleCatalogRefresh(150);
        } catch (err) {
          console.error(err);
        } finally {
          control.disabled = false;
        }
      });

      body.appendChild(itemName);
      body.appendChild(sell);
      body.appendChild(buy);
      body.appendChild(source);
      body.appendChild(control);

      card.appendChild(img);
      card.appendChild(body);
      listWrap.appendChild(card);
    });

    section.appendChild(listWrap);
    detailFields.appendChild(section);
  }

  function renderFavoriteColorChips(colors) {
    if (!Array.isArray(colors) || !colors.length) return;
    const row = document.createElement("div");
    row.className = "detail-color-row";

    const label = document.createElement("p");
    label.className = "detail-field";
    label.textContent = "좋아하는 색";
    row.appendChild(label);

    const chips = document.createElement("div");
    chips.className = "detail-color-chips";
    colors.forEach((color) => {
      const meta = favoriteColorMeta[color] || { ko: "", swatch: "#cbd5e1" };
      const chip = document.createElement("span");
      chip.className = "detail-color-chip";

      const swatch = document.createElement("span");
      swatch.className = "detail-color-swatch";
      swatch.style.background = meta.swatch;

      const text = document.createElement("span");
      const ko = meta.ko ? `${meta.ko} ` : "";
      text.textContent = `${ko}(${color})`;

      chip.appendChild(swatch);
      chip.appendChild(text);
      chips.appendChild(chip);
    });
    row.appendChild(chips);
    detailFields.appendChild(row);
  }

  function getDetailModeCache(mode) {
    if (!state.detailCacheByMode[mode]) state.detailCacheByMode[mode] = new Map();
    return state.detailCacheByMode[mode];
  }

  function getActiveDetailIndex() {
    if (!state.activeDetailItemId || !state.activeCatalogItemIds.length) return -1;
    return state.activeCatalogItemIds.indexOf(state.activeDetailItemId);
  }

  function syncDetailNavState() {
    const isOpen = !detailModal.classList.contains("hidden");
    const hasItems = state.activeCatalogItemIds.length > 0;
    const idx = getActiveDetailIndex();
    const canPrev = isOpen && hasItems && idx > 0;
    const canNext = isOpen && hasItems && idx >= 0 && idx < state.activeCatalogItemIds.length - 1;

    if (detailPrevBtn) detailPrevBtn.disabled = !canPrev;
    if (detailNextBtn) detailNextBtn.disabled = !canNext;

    if (detailNavHint) {
      detailNavHint.textContent = isOpen && idx >= 0 ? `${idx + 1} / ${state.activeCatalogItemIds.length}` : "";
    }
  }

  function closeDetailModal() {
    detailModal.classList.add("hidden");
    detailModal.setAttribute("aria-hidden", "true");
    state.activeDetailType = "";
    state.activeDetailItemId = "";
    state.activeDetailVariations = [];
    state.activeDetailPayload = null;
    syncDetailNavState();
  }

  async function fetchCatalogDetail(itemId, { force = false } = {}) {
    const mode = state.activeMode;
    const cache = getDetailModeCache(mode);
    if (!force && cache.has(itemId)) return cache.get(itemId);
    const detail = await getJSON(`/api/catalog/${mode}/${itemId}/detail`);
    cache.set(itemId, detail);
    return detail;
  }

  function prefetchNeighborDetails() {
    if (!state.activeMode || state.activeMode === "villagers") return;
    const mode = state.activeMode;
    const cache = getDetailModeCache(mode);
    const idx = getActiveDetailIndex();
    if (idx < 0) return;
    const targets = [state.activeCatalogItemIds[idx - 1], state.activeCatalogItemIds[idx + 1]].filter(Boolean);
    targets.forEach((id) => {
      if (cache.has(id)) return;
      getJSON(`/api/catalog/${mode}/${id}/detail`)
        .then((payload) => cache.set(id, payload))
        .catch((err) => console.error(err));
    });
  }

  function openDetailModal(payload) {
    state.activeDetailType = "catalog";
    state.activeDetailPayload = payload;
    const isRecipeMode = state.activeMode === "recipes";
    const hideVariationInfoMode = state.activeMode === "recipes" || state.activeMode === "reactions";
    const summary = payload.summary || {};
    const nameKo = String(payload.item?.name_ko || payload.item?.name || "").trim();
    const nameEn = String(summary.name_en || payload.item?.name_en || "").trim();
    if (nameKo && nameEn && nameKo !== nameEn) {
      detailTitle.textContent = `${nameKo} (${nameEn})`;
    } else {
      detailTitle.textContent = nameKo || nameEn || "상세 정보";
    }
    const isArtMode = state.activeMode === "art";
    const detailImageUrl = isArtMode
      ? summary.art_real_image_url || summary.image_url
      : summary.image_url;
    const isNotForSale = Boolean(summary.not_for_sale);
    detailImage.src = detailImageUrl || "/static/no-image.svg";
    detailImage.onerror = () => {
      detailImage.src = "/static/no-image.svg";
    };
    detailSourceHint.textContent = payload.from_single_endpoint
      ? "single API 상세 데이터"
      : "목록 API 상세 데이터(대체)";
    if (detailNotForSaleTag) {
      detailNotForSaleTag.classList.toggle("hidden", !isNotForSale);
    }

    detailFields.innerHTML = "";
    const detailFieldsRows = Array.isArray(payload.fields) ? payload.fields : [];
    const filteredDetailFields = hideVariationInfoMode
      ? detailFieldsRows.filter((field) => {
          const label = String(field?.label || "");
          return !/(색|패턴|변형|color|pattern|variation)/i.test(label);
        })
      : detailFieldsRows;
    filteredDetailFields.forEach((field) => {
      const row = document.createElement("p");
      row.className = "detail-field";
      row.textContent = `${field.label}: ${field.value}`;
      detailFields.appendChild(row);
    });

    if (detailExtraImagesSection) detailExtraImagesSection.classList.add("hidden");
    if (detailExtraImages) detailExtraImages.innerHTML = "";
    if (state.activeMode === "art" && detailExtraImagesSection && detailExtraImages) {
      const realImage = String(summary.art_real_image_url || "").trim();
      const fakeImage = String(summary.art_fake_image_url || "").trim();
      const rows = [
        ["진품 이미지", realImage],
        ["가품 이미지", fakeImage],
      ].filter(([, url]) => url);
      if (rows.length) {
        detailExtraImagesSection.classList.remove("hidden");
        rows.forEach(([label, url]) => {
          const box = document.createElement("article");
          box.className = "variation-card static";
          const img = document.createElement("img");
          img.className = "variation-image detail-extra-image";
          img.src = url;
          img.alt = label;
          img.onerror = () => {
            img.src = "/static/no-image.svg";
          };
          const title = document.createElement("p");
          title.className = "variation-title";
          title.textContent = label;
          box.appendChild(img);
          box.appendChild(title);
          detailExtraImages.appendChild(box);
        });
      }
    }

    detailVariations.innerHTML = "";
    const variations = payload.variations || [];
    if (variationMarkAllBtn) variationMarkAllBtn.classList.toggle("hidden", hideVariationInfoMode);
    if (variationUnmarkAllBtn) variationUnmarkAllBtn.classList.toggle("hidden", hideVariationInfoMode);
    if (detailVariationsSection) detailVariationsSection.classList.toggle("hidden", hideVariationInfoMode);
    if (hideVariationInfoMode) {
      detailVariations.classList.add("hidden");
      state.activeDetailVariations = [];
    } else {
      detailVariations.classList.remove("hidden");
      state.activeDetailVariations = variations;
      if (!variations.length) {
        const empty = document.createElement("p");
        empty.className = "detail-empty";
        empty.textContent = "변형 정보가 없습니다.";
        detailVariations.appendChild(empty);
      } else {
      variations.forEach((v) => {
        const box = document.createElement("article");
        box.className = `variation-card ${v.owned ? "owned" : ""}`;
        const img = document.createElement("img");
        img.className = "variation-image";
        img.src = v.image_url || "/static/no-image.svg";
        img.alt = v.label || "variation";
        img.onerror = () => {
          img.src = "/static/no-image.svg";
        };

        const title = document.createElement("p");
        title.className = "variation-title";
        title.textContent = v.label || "-";

        const meta = document.createElement("p");
        meta.className = "variation-meta";
        const parts = [];
        if (v.color1) parts.push(`색1: ${v.color1}`);
        if (v.color2) parts.push(`색2: ${v.color2}`);
        if (v.pattern) parts.push(`패턴: ${v.pattern}`);
        if (v.price) parts.push(`가격: ${v.price}`);
        meta.textContent = parts.join(" | ") || "-";

        const stateRow = document.createElement("p");
        stateRow.className = "variation-state";
        stateRow.textContent = v.owned ? "보유됨" : "미보유";

        const qtyWrap = document.createElement("label");
        qtyWrap.className = "variation-qty-wrap";
        qtyWrap.textContent = "개수";
        const qtyInput = document.createElement("input");
        qtyInput.type = "number";
        qtyInput.min = "0";
        qtyInput.step = "1";
        qtyInput.className = "variation-qty-input";
        qtyInput.value = String(Math.max(0, Number(v.quantity || 0)));
        qtyInput.addEventListener("click", (e) => e.stopPropagation());
        qtyInput.addEventListener("change", async (e) => {
          e.stopPropagation();
          const safeQty = Math.max(0, Math.trunc(Number(qtyInput.value || 0)));
          qtyInput.value = String(safeQty);
          const nextOwned = safeQty > 0;
          try {
            await updateCatalogVariationState(state.activeMode, state.activeDetailItemId, v.id, {
              quantity: safeQty,
              owned: nextOwned,
            });
            v.quantity = safeQty;
            v.owned = nextOwned;
            stateRow.textContent = nextOwned ? "보유됨" : "미보유";
            box.classList.toggle("owned", nextOwned);
            state.activeDetailVariations = state.activeDetailVariations.map((x) =>
              x.id === v.id ? { ...x, owned: nextOwned, quantity: safeQty } : x
            );
            if (state.activeDetailPayload && Array.isArray(state.activeDetailPayload.variations)) {
              state.activeDetailPayload.variations = state.activeDetailPayload.variations.map((x) =>
                x.id === v.id ? { ...x, owned: nextOwned, quantity: safeQty } : x
              );
              getDetailModeCache(state.activeMode).set(state.activeDetailItemId, state.activeDetailPayload);
            }
            scheduleCatalogRefresh(200);
          } catch (err) {
            console.error(err);
          }
        });
        qtyWrap.appendChild(qtyInput);

        box.addEventListener("click", async () => {
          const nextOwned = !Boolean(v.owned);
          const nextQty = nextOwned ? Math.max(1, Number(v.quantity || 0)) : 0;
          try {
            await updateCatalogVariationState(state.activeMode, state.activeDetailItemId, v.id, {
              owned: nextOwned,
              quantity: nextQty,
            });
            v.owned = nextOwned;
            v.quantity = nextQty;
            qtyInput.value = String(nextQty);
            stateRow.textContent = nextOwned ? "보유됨" : "미보유";
            box.classList.toggle("owned", nextOwned);
            state.activeDetailVariations = state.activeDetailVariations.map((x) =>
              x.id === v.id ? { ...x, owned: nextOwned, quantity: nextQty } : x
            );
            if (state.activeDetailPayload && Array.isArray(state.activeDetailPayload.variations)) {
              state.activeDetailPayload.variations = state.activeDetailPayload.variations.map((x) =>
                x.id === v.id ? { ...x, owned: nextOwned, quantity: nextQty } : x
              );
              getDetailModeCache(state.activeMode).set(state.activeDetailItemId, state.activeDetailPayload);
            }
            scheduleCatalogRefresh(250);
          } catch (err) {
            console.error(err);
          }
        });

        box.appendChild(img);
        box.appendChild(title);
        box.appendChild(meta);
        box.appendChild(stateRow);
        box.appendChild(qtyWrap);
        detailVariations.appendChild(box);
      });
    }
    }

    detailRawFields.innerHTML = "";
    const rawRows = Array.isArray(payload.raw_fields) ? payload.raw_fields : [];
    const filteredRawRows = hideVariationInfoMode
      ? rawRows.filter((row) => {
          const key = String(row?.key || "");
          return !/(색|패턴|변형|color|pattern|variation)/i.test(key);
        })
      : rawRows;
    filteredRawRows.forEach((row) => {
      const p = document.createElement("p");
      p.className = "raw-field";
      p.textContent = `${row.key}: ${row.value}`;
      detailRawFields.appendChild(p);
    });

    detailModal.classList.remove("hidden");
    detailModal.setAttribute("aria-hidden", "false");
    syncDetailNavState();
  }

  function openVillagerDetail(villager, options = {}) {
    const v = villager || {};
    const currentVillagerId = String(v.id || "");
    const contextVillagers = Array.isArray(options.contextVillagers) ? options.contextVillagers : null;
    const mergeKoEn = (ko, en) => {
      const koText = String(ko || "").trim();
      const enText = String(en || "").trim();
      if (koText && enText && koText !== enText) return `${koText} (${enText})`;
      return koText || enText;
    };
    const asText = (val) => {
      if (Array.isArray(val)) return val.filter(Boolean).join(", ");
      if (typeof val === "boolean") return val ? "예" : "아니오";
      return val || "";
    };
    const appendRows = (rows) => {
      rows.forEach(([label, value]) => {
        const rendered = asText(value);
        if (!rendered) return;
        const row = document.createElement("p");
        row.className = "detail-field";
        row.textContent = `${label}: ${rendered}`;
        detailFields.appendChild(row);
      });
    };

    state.activeDetailItemId = currentVillagerId;
    state.activeDetailType = "villager";
    if (contextVillagers && contextVillagers.length) {
      state.renderedVillagers = contextVillagers.slice();
      state.activeCatalogItemIds = state.renderedVillagers.map((x) => String(x.id || ""));
    }
    detailTitle.textContent = v.name_ko || v.name_en || "주민 상세 정보";
    if (detailNotForSaleTag) {
      detailNotForSaleTag.classList.add("hidden");
    }
    if (variationMarkAllBtn) variationMarkAllBtn.classList.add("hidden");
    if (variationUnmarkAllBtn) variationUnmarkAllBtn.classList.add("hidden");
    if (detailVariationsSection) detailVariationsSection.classList.add("hidden");
    detailVariations.classList.add("hidden");
    setVillagerDetailImage(v, currentVillagerId);
    detailSourceHint.textContent = "주민 데이터 상세 정보";

    detailFields.innerHTML = "";
    const activity = getPersonalityActivity(v);
    appendRows([
      ["이름", mergeKoEn(v.name_ko, v.name_en)],
      ["종", mergeKoEn(v.species_ko, v.species)],
      ["성격", mergeKoEn(v.personality_ko, v.personality)],
      ["성격 구분", activity?.group_ko || ""],
      [
        "활동시간",
        activity?.wake_up && activity?.sleep ? `${activity.wake_up} ~ ${activity.sleep}` : "",
      ],
      ["성격 서브타입", v.sub_personality || ""],
      ["성별", v.gender || ""],
      ["취미", v.hobby || ""],
      ["생일", v.birthday || ""],
      ["별자리", v.sign || ""],
      ["등장 작품", v.appearances || []],
      ["데뷔작", v.debut || ""],
      ["섬 주민 가능", v.islander],
    ]);

    appendRows([
      ["말버릇(한글)", v.catchphrase_ko || ""],
      ["말버릇(기본)", v.phrase || ""],
      ["과거 말버릇", v.prev_phrases || []],
      ["좋아하는 말", mergeKoEn(v.saying_ko, v.saying)],
    ]);

    appendRows([
      ["좋아하는 스타일", v.favorite_styles || []],
      ["기본 옷", v.default_clothing || ""],
      ["기본 옷 변형", v.default_clothing_variation || ""],
      ["기본 우산", v.default_umbrella || ""],
    ]);
    renderFavoriteColorChips(v.favorite_colors || []);

    appendRows([
      ["좋아하는 음악", mergeKoEn(v.house_music_ko, v.house_music)],
      ["하우스 음악 메모", v.house_music_note || ""],
      ["하우스 벽지", v.house_wallpaper || ""],
      ["하우스 바닥", v.house_flooring || ""],
      ["하우스 외관 이미지", v.house_exterior_url || ""],
      ["하우스 내부 이미지", v.house_interior_url || ""],
      ["주민 사진 URL", v.photo_url || ""],
      ["타이틀 색상", v.title_color || ""],
      ["텍스트 색상", v.text_color || ""],
    ]);
    renderVillagerPhotoPosterSection(v, currentVillagerId).catch((err) => console.error(err));

    if (detailExtraImagesSection && detailExtraImages) {
      detailExtraImages.innerHTML = "";
      const extraImages = [
        ["하우스 외관", v.house_exterior_url || ""],
        ["하우스 내관", v.house_interior_url || ""],
      ].filter(([, url]) => url);

      if (extraImages.length) {
        detailExtraImagesSection.classList.remove("hidden");
        extraImages.forEach(([label, url]) => {
          const box = document.createElement("article");
          box.className = "variation-card static";

          const img = document.createElement("img");
          img.className = "variation-image detail-extra-image";
          img.src = url;
          img.alt = label;
          img.onerror = () => {
            img.src = "/static/no-image.svg";
          };

          const title = document.createElement("p");
          title.className = "variation-title";
          title.textContent = label;

          box.appendChild(img);
          box.appendChild(title);
          detailExtraImages.appendChild(box);
        });
      } else {
        detailExtraImagesSection.classList.add("hidden");
      }
    }

    detailVariations.innerHTML = "";

    detailRawFields.innerHTML = "";
    const raw = [
      ["id", v.id],
      ["name_ko", v.name_ko],
      ["name_en", v.name_en],
      ["species", v.species],
      ["species_ko", v.species_ko],
      ["personality", v.personality],
      ["personality_ko", v.personality_ko],
      ["personality_activity_group_ko", activity?.group_ko || ""],
      [
        "personality_activity_time",
        activity?.wake_up && activity?.sleep ? `${activity.wake_up} ~ ${activity.sleep}` : "",
      ],
      ["sub_personality", v.sub_personality],
      ["gender", v.gender],
      ["hobby", v.hobby],
      ["sign", v.sign],
      ["debut", v.debut],
      ["title_color", v.title_color],
      ["text_color", v.text_color],
      ["birthday", v.birthday],
      ["birthday_month", v.birthday_month],
      ["birthday_day", v.birthday_day],
      ["phrase", v.phrase],
      ["prev_phrases", asText(v.prev_phrases)],
      ["catchphrase_ko", v.catchphrase_ko],
      ["catchphrase", v.catchphrase],
      ["saying_ko", v.saying_ko],
      ["saying", v.saying],
      ["favorite_colors", asText(v.favorite_colors)],
      ["favorite_styles", asText(v.favorite_styles)],
      ["default_clothing", v.default_clothing],
      ["default_clothing_variation", v.default_clothing_variation],
      ["default_umbrella", v.default_umbrella],
      ["islander", asText(v.islander)],
      ["appearances", asText(v.appearances)],
      ["photo_url", v.photo_url],
      ["house_exterior_url", v.house_exterior_url],
      ["house_interior_url", v.house_interior_url],
      ["house_wallpaper", v.house_wallpaper],
      ["house_flooring", v.house_flooring],
      ["house_music_ko", v.house_music_ko],
      ["house_music", v.house_music],
      ["house_music_note", v.house_music_note],
      ["liked", v.liked],
      ["on_island", v.on_island],
      ["former_resident", v.former_resident],
    ];
    raw.forEach(([k, val]) => {
      if (val === undefined || val === null || val === "") return;
      const p = document.createElement("p");
      p.className = "raw-field";
      p.textContent = `${k}: ${String(val)}`;
      detailRawFields.appendChild(p);
    });

    if (!state.activeCatalogItemIds.length && Array.isArray(state.renderedVillagers)) {
      state.activeCatalogItemIds = state.renderedVillagers.map((x) => String(x.id || ""));
    }
    state.activeDetailVariations = [];
    state.activeDetailPayload = null;
    detailModal.classList.remove("hidden");
    detailModal.setAttribute("aria-hidden", "false");
    syncDetailNavState();
    prefetchNeighborVillagerImages();
  }

  async function openCatalogDetail(itemId, options = {}) {
    if (!state.activeMode || state.activeMode === "villagers") return;
    state.activeDetailItemId = itemId;
    const detail = await fetchCatalogDetail(itemId, options);
    openDetailModal(detail);
    prefetchNeighborDetails();
  }

  async function moveDetail(offset) {
    if (detailModal.classList.contains("hidden")) return;
    const idx = getActiveDetailIndex();
    if (idx < 0) return;
    const nextIdx = idx + offset;
    if (nextIdx < 0 || nextIdx >= state.activeCatalogItemIds.length) return;
    const nextId = state.activeCatalogItemIds[nextIdx];
    if (state.activeDetailType === "villager") {
      const nextVillager = state.renderedVillagers?.[nextIdx] || null;
      if (!nextVillager) return;
      openVillagerDetail(nextVillager);
      return;
    }
    await openCatalogDetail(nextId);
  }

  function bindEvents() {
    detailBackdrop.addEventListener("click", closeDetailModal);
    detailCloseBtn.addEventListener("click", closeDetailModal);
    if (detailPrevBtn) {
      detailPrevBtn.addEventListener("click", () => {
        moveDetail(-1).catch((err) => console.error(err));
      });
    }
    if (detailNextBtn) {
      detailNextBtn.addEventListener("click", () => {
        moveDetail(1).catch((err) => console.error(err));
      });
    }
    variationMarkAllBtn.addEventListener("click", async () => {
      if (!state.activeDetailItemId || !state.activeDetailVariations.length) return;
      try {
        await updateCatalogVariationStateBatch(
          state.activeMode,
          state.activeDetailItemId,
          state.activeDetailVariations.map((v) => ({
            variation_id: v.id,
            owned: true,
            quantity: Math.max(1, Number(v.quantity || 0)),
          }))
        );
        await openCatalogDetail(state.activeDetailItemId, { force: true });
        scheduleCatalogRefresh(250);
      } catch (err) {
        console.error(err);
      }
    });
    variationUnmarkAllBtn.addEventListener("click", async () => {
      if (!state.activeDetailItemId || !state.activeDetailVariations.length) return;
      try {
        await updateCatalogVariationStateBatch(
          state.activeMode,
          state.activeDetailItemId,
          state.activeDetailVariations.map((v) => ({ variation_id: v.id, owned: false, quantity: 0 }))
        );
        await openCatalogDetail(state.activeDetailItemId, { force: true });
        scheduleCatalogRefresh(250);
      } catch (err) {
        console.error(err);
      }
    });
    document.addEventListener("keydown", (e) => {
      const isOpen = !detailModal.classList.contains("hidden");
      if (e.key === "Escape" && isOpen) {
        closeDetailModal();
        return;
      }
      if (!isOpen) return;
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        moveDetail(-1).catch((err) => console.error(err));
        return;
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        moveDetail(1).catch((err) => console.error(err));
      }
    });
  }

  return {
    bindEvents,
    closeDetailModal,
    moveDetail,
    openCatalogDetail,
    openVillagerDetail,
    syncDetailNavState,
  };
}
