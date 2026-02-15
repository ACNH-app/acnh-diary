import {
  calendarCheckedInput,
  calendarEntryList,
  calendarGrid,
  calendarMonthLabel,
  calendarNextBtn,
  calendarNoteInput,
  calendarPrevBtn,
  calendarSelectedDate,
  npcPicker,
} from "./dom.js";
import { state } from "./state.js";
import { getEffectiveNow } from "./utils.js";

const CALENDAR_NPC_OPTIONS = [
  { name: "여욱", night: false },
  { name: "사하라", night: false },
  { name: "패트릭", night: false },
  { name: "저스틴", night: false },
  { name: "레온", night: false },
  { name: "여울", night: false },
  { name: "고숙이", night: false },
  { name: "케이트", night: false },
  { name: "무파니", night: false },
  { name: "K.K.", night: false },
  { name: "부옥", night: true },
  { name: "깨빈", night: true },
];

const WEEKLY_DEFAULT_NPCS = {
  0: "무파니", // Sunday
  6: "K.K.", // Saturday
};

function pad2(v) {
  return String(v).padStart(2, "0");
}

function toMonth(dateStr) {
  return String(dateStr || "").slice(0, 7);
}

function parseYmd(dateStr) {
  const [yRaw, mRaw, dRaw] = String(dateStr || "").split("-");
  const y = Number(yRaw);
  const m = Number(mRaw);
  const d = Number(dRaw);
  if (!Number.isFinite(y) || !Number.isFinite(m) || !Number.isFinite(d)) return null;
  return { y, m, d };
}

function normalizeNpcName(name) {
  return String(name || "")
    .trim()
    .toLowerCase()
    .replace(/[.\s]/g, "");
}

function isNightNpc(name) {
  const key = normalizeNpcName(name);
  return key === normalizeNpcName("부옥") || key === normalizeNpcName("깨빈");
}

function todayIso() {
  const now = getEffectiveNow(state);
  return `${now.getFullYear()}-${pad2(now.getMonth() + 1)}-${pad2(now.getDate())}`;
}

function shiftMonth(month, delta) {
  const [yRaw, mRaw] = String(month || "").split("-");
  const y = Number(yRaw);
  const m = Number(mRaw);
  if (!Number.isFinite(y) || !Number.isFinite(m)) return month;
  const dt = new Date(y, m - 1 + delta, 1);
  return `${dt.getFullYear()}-${pad2(dt.getMonth() + 1)}`;
}

function getDefaultNpcByDate(dateStr) {
  const parsed = parseYmd(dateStr);
  if (!parsed) return "";
  const day = new Date(parsed.y, parsed.m - 1, parsed.d).getDay();
  return WEEKLY_DEFAULT_NPCS[day] || "";
}

function mergeWithWeeklyDefaultsForDate(dateStr, entries) {
  const rows = Array.isArray(entries) ? [...entries] : [];
  const defaultNpc = getDefaultNpcByDate(dateStr);
  if (!defaultNpc) return rows;
  const already = rows.some((row) => normalizeNpcName(row?.npc_name) === normalizeNpcName(defaultNpc));
  if (!already) {
    rows.push({
      id: `default-${dateStr}-${normalizeNpcName(defaultNpc)}`,
      visit_date: dateStr,
      npc_name: defaultNpc,
      note: "기본 방문",
      checked: true,
      is_default: true,
    });
  }
  return rows;
}

function mergeWithWeeklyDefaultsForMonth(month, entries) {
  const [yRaw, mRaw] = String(month || "").split("-");
  const y = Number(yRaw);
  const m = Number(mRaw);
  if (!Number.isFinite(y) || !Number.isFinite(m)) return Array.isArray(entries) ? [...entries] : [];
  const byDate = new Map();
  (Array.isArray(entries) ? entries : []).forEach((row) => {
    const date = String(row?.visit_date || "");
    if (!date) return;
    const arr = byDate.get(date) || [];
    arr.push(row);
    byDate.set(date, arr);
  });

  const daysInMonth = new Date(y, m, 0).getDate();
  for (let day = 1; day <= daysInMonth; day += 1) {
    const date = `${y}-${pad2(m)}-${pad2(day)}`;
    const merged = mergeWithWeeklyDefaultsForDate(date, byDate.get(date) || []);
    if (merged.length) byDate.set(date, merged);
  }

  const out = [];
  byDate.forEach((arr) => out.push(...arr));
  return out;
}

function buildEntryMap(entries) {
  const dayEntries = new Map();
  (entries || []).forEach((row) => {
    const d = String(row.visit_date || "");
    if (!d) return;
    const arr = dayEntries.get(d) || [];
    arr.push(row);
    dayEntries.set(d, arr);
  });
  return dayEntries;
}

function buildDayEventsPreview(entries) {
  const counts = new Map();
  const order = [];
  (entries || []).forEach((entry) => {
    const name = String(entry?.npc_name || "").trim();
    if (!name) return;
    if (!counts.has(name)) order.push(name);
    counts.set(name, (counts.get(name) || 0) + 1);
  });
  return order.map((name) => {
    const count = counts.get(name) || 0;
    return {
      text: count > 1 ? `${name} x${count}` : name,
      kind: isNightNpc(name) ? "night" : "npc",
    };
  });
}

function buildAnnotationMap(rows) {
  const byDate = new Map();
  (Array.isArray(rows) ? rows : []).forEach((row) => {
    const date = String(row?.date || "");
    if (!date) return;
    const arr = byDate.get(date) || [];
    arr.push(row);
    byDate.set(date, arr);
  });
  return byDate;
}

function buildAnnotationPreviewItems(rows) {
  const out = [];
  (Array.isArray(rows) ? rows : []).forEach((row) => {
    const type = String(row?.type || "");
    const label = String(row?.label || "").trim();
    if (!label) return;
    if (type === "birthday") {
      out.push({ text: label, kind: "birthday" });
      return;
    }
    out.push({ text: label, kind: "event" });
  });
  return out;
}

function renderGrid() {
  if (!calendarGrid || !calendarMonthLabel) return;
  const [yearRaw, monthRaw] = String(state.calendarMonth || "").split("-");
  const year = Number(yearRaw);
  const month = Number(monthRaw);
  if (!Number.isFinite(year) || !Number.isFinite(month)) return;

  calendarGrid.innerHTML = "";
  calendarMonthLabel.textContent = `${year}년 ${month}월`;

  const weekdayOfFirst = new Date(year, month - 1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();
  const dayEntries = buildEntryMap(state.calendarMonthEntries);
  const dayAnnotations = buildAnnotationMap(state.calendarMonthAnnotations);

  for (let i = 0; i < weekdayOfFirst; i += 1) {
    const blank = document.createElement("div");
    blank.className = "calendar-day empty";
    calendarGrid.appendChild(blank);
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const date = `${year}-${pad2(month)}-${pad2(day)}`;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "calendar-day";
    btn.dataset.date = date;
    if (date === state.calendarSelectedDate) btn.classList.add("selected");
    const entries = dayEntries.get(date) || [];
    if (entries.length > 0) btn.classList.add("has-entry");

    const dayNum = document.createElement("span");
    dayNum.className = "calendar-day-num";
    dayNum.textContent = String(day);
    btn.appendChild(dayNum);

    const previewItems = [
      ...buildDayEventsPreview(entries),
      ...buildAnnotationPreviewItems(dayAnnotations.get(date) || []),
    ];
    if (previewItems.length > 0) {
      const preview = document.createElement("div");
      preview.className = "calendar-day-events";
      previewItems.slice(0, 3).forEach((item) => {
        const pill = document.createElement("span");
        pill.className = "calendar-event-pill";
        pill.textContent = item.text;
        if (item.kind === "night") pill.classList.add("night");
        if (item.kind === "birthday") pill.classList.add("birthday");
        if (item.kind === "event") pill.classList.add("event");
        preview.appendChild(pill);
      });
      if (previewItems.length > 3) {
        const more = document.createElement("span");
        more.className = "calendar-event-more";
        more.textContent = `+${previewItems.length - 3}`;
        preview.appendChild(more);
      }
      btn.appendChild(preview);
    }

    calendarGrid.appendChild(btn);
  }
}

function renderDayEntries(onToggleChecked, onDelete) {
  calendarEntryList.innerHTML = "";
  const hasNpcEntries = state.calendarDayEntries.length > 0;
  const hasAnnotations = state.calendarDayAnnotations.length > 0;
  if (!hasNpcEntries && !hasAnnotations) {
    const li = document.createElement("li");
    li.textContent = "기록 없음";
    calendarEntryList.appendChild(li);
    return;
  }

  state.calendarDayEntries.forEach((entry) => {
    const li = document.createElement("li");
    const check = document.createElement("input");
    check.type = "checkbox";
    check.checked = Boolean(entry.checked);
    check.disabled = Boolean(entry.is_default);
    if (!entry.is_default) {
      check.addEventListener("change", async () => {
        await onToggleChecked(entry.id, check.checked);
      });
    }

    const text = document.createElement("span");
    const note = entry.note ? ` - ${entry.note}` : "";
    const defaultMark = entry.is_default ? " (기본)" : "";
    const nightMark = isNightNpc(entry.npc_name) ? " (야간)" : "";
    const displayNote = `${note}${defaultMark}${nightMark}`;
    text.textContent = ` ${entry.npc_name}${displayNote} `;

    li.append(check, text);
    if (!entry.is_default) {
      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.textContent = "삭제";
      delBtn.addEventListener("click", async () => {
        await onDelete(entry.id);
      });
      li.append(delBtn);
    }

    calendarEntryList.appendChild(li);
  });

  state.calendarDayAnnotations.forEach((item) => {
    const li = document.createElement("li");
    li.className = "calendar-annotation-item";
    const text = document.createElement("span");
    const type = String(item?.type || "");
    const label = String(item?.label || "");
    if (type === "birthday") {
      text.textContent = `[생일] ${label}`;
      li.classList.add("birthday");
    } else {
      text.textContent = `[이벤트] ${label}`;
      li.classList.add("event");
    }
    li.append(text);
    calendarEntryList.appendChild(li);
  });
}

function renderNpcPicker(onPickNpc) {
  if (!npcPicker) return;
  npcPicker.innerHTML = "";
  CALENDAR_NPC_OPTIONS.forEach((item) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "npc-chip";
    if (item.night) btn.classList.add("night");
    btn.textContent = item.name;
    btn.addEventListener("click", async () => {
      await onPickNpc(item.name);
    });
    npcPicker.appendChild(btn);
  });
}

export function initializeCalendarState() {
  const today = todayIso();
  if (!state.calendarMonth) state.calendarMonth = toMonth(today);
  if (!state.calendarSelectedDate) state.calendarSelectedDate = today;
  if (calendarSelectedDate) calendarSelectedDate.value = state.calendarSelectedDate;
}

export async function loadCalendarMonth(getCalendarEntries, getCalendarAnnotations) {
  const rows = await getCalendarEntries(state.calendarMonth);
  state.calendarMonthEntries = mergeWithWeeklyDefaultsForMonth(state.calendarMonth, rows);
  state.calendarMonthAnnotations = getCalendarAnnotations ? await getCalendarAnnotations(state.calendarMonth) : [];
  renderGrid();
}

export function createDayLoader({
  getCalendarEntriesByDate,
  setCalendarEntryChecked,
  deleteCalendarEntry,
  reloadMonth,
}) {
  return async function loadDay() {
    const rows = await getCalendarEntriesByDate(state.calendarSelectedDate);
    state.calendarDayEntries = mergeWithWeeklyDefaultsForDate(state.calendarSelectedDate, rows);
    state.calendarDayAnnotations = (state.calendarMonthAnnotations || []).filter(
      (x) => String(x?.date || "") === String(state.calendarSelectedDate || "")
    );
    renderDayEntries(
      async (entryId, checked) => {
        await setCalendarEntryChecked(entryId, checked);
        await reloadMonth();
        await loadDay();
      },
      async (entryId) => {
        await deleteCalendarEntry(entryId);
        await reloadMonth();
        await loadDay();
      }
    );
  };
}

export function bindCalendarEvents({ saveCalendarEntry, reloadMonth, loadDay }) {
  if (!calendarPrevBtn || !calendarNextBtn || !calendarSelectedDate || !calendarGrid) return;

  const syncMonthFromSelectedDate = () => {
    const selected = String(state.calendarSelectedDate || "");
    const selectedMonth = toMonth(selected);
    if (selectedMonth) state.calendarMonth = selectedMonth;
  };

  const selectDate = async (date) => {
    if (!date) return;
    state.calendarSelectedDate = date;
    calendarSelectedDate.value = date;
    syncMonthFromSelectedDate();
    await reloadMonth();
    await loadDay();
  };

  calendarPrevBtn.addEventListener("click", async () => {
    state.calendarMonth = shiftMonth(state.calendarMonth, -1);
    if (toMonth(state.calendarSelectedDate) !== state.calendarMonth) {
      await selectDate(`${state.calendarMonth}-01`);
      return;
    }
    await reloadMonth();
  });

  calendarNextBtn.addEventListener("click", async () => {
    state.calendarMonth = shiftMonth(state.calendarMonth, 1);
    if (toMonth(state.calendarSelectedDate) !== state.calendarMonth) {
      await selectDate(`${state.calendarMonth}-01`);
      return;
    }
    await reloadMonth();
  });

  calendarGrid.addEventListener("click", async (e) => {
    const dayButton = e.target.closest(".calendar-day");
    if (!dayButton || dayButton.classList.contains("empty")) return;
    const date = dayButton.dataset.date || "";
    await selectDate(date);
  });

  calendarSelectedDate.addEventListener("change", async () => {
    await selectDate(calendarSelectedDate.value);
  });

  renderNpcPicker(async (npcName) => {
    const visitDate = calendarSelectedDate.value || state.calendarSelectedDate;
    if (!visitDate) {
      window.alert("날짜를 먼저 선택해 주세요.");
      return;
    }
    await saveCalendarEntry({
      visit_date: visitDate,
      npc_name: npcName,
      note: String(calendarNoteInput.value || "").trim(),
      checked: Boolean(calendarCheckedInput.checked),
    });
    calendarNoteInput.value = "";
    calendarCheckedInput.checked = false;
    await selectDate(visitDate);
  });
}
