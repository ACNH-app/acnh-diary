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

export function toQuery(params) {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== "" && v !== null && v !== undefined) q.set(k, v);
  });
  return q.toString();
}

function pad2(value) {
  return String(value).padStart(2, "0");
}

export function toDateTimeLocalValue(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return "";
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}T${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
}

export function parseDateTimeLocalValue(value) {
  const text = String(value || "").trim();
  if (!text) return null;
  const date = new Date(text);
  if (Number.isNaN(date.getTime())) return null;
  return date;
}

export function getEffectiveNow(stateLike) {
  if (stateLike && stateLike.timeTravelEnabled) {
    const parsed = parseDateTimeLocalValue(stateLike.gameDateTime);
    if (parsed) return parsed;
  }
  return new Date();
}

export function normalizeMonthDay(value) {
  const src = String(value || "").trim();
  if (!src) return "";

  // YYYY-MM-DD
  let m = src.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (m) {
    const month = Number(m[2]);
    const day = Number(m[3]);
    if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
      return `${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    }
  }

  // MM-DD, M-D, MM/DD, M/D
  m = src.match(/^(\d{1,2})[-/.](\d{1,2})$/);
  if (m) {
    const month = Number(m[1]);
    const day = Number(m[2]);
    if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
      return `${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    }
  }

  return "";
}

function parseBirthdayRank(birthday) {
  if (!birthday) return 9999;
  const parts = String(birthday).trim().split(/\s+/);
  if (parts.length < 2) return 9999;
  const month = monthToNumber[(parts[0] || "").toLowerCase()] || 99;
  const day = Number.parseInt(parts[1], 10);
  return month * 100 + (Number.isFinite(day) ? day : 99);
}

function scriptRank(text) {
  const s = String(text || "").trim();
  if (!s) return 3;
  const ch = s[0];
  const code = ch.codePointAt(0) || 0;
  if (/[0-9]/.test(ch)) return 0;
  if (
    (code >= 0xac00 && code <= 0xd7a3) ||
    (code >= 0x1100 && code <= 0x11ff) ||
    (code >= 0x3130 && code <= 0x318f)
  ) {
    return 1;
  }
  if (/[A-Za-z]/.test(ch)) return 2;
  return 3;
}

export function compareNamePriority(aText, bText) {
  const a = String(aText || "").trim();
  const b = String(bText || "").trim();
  const rankDiff = scriptRank(a) - scriptRank(b);
  if (rankDiff !== 0) return rankDiff;
  return a.localeCompare(b, "ko");
}

export function sortVillagers(items, sortBy, order) {
  const direction = order === "desc" ? -1 : 1;

  return [...items].sort((a, b) => {
    if (sortBy === "birthday") {
      return (parseBirthdayRank(a.birthday) - parseBirthdayRank(b.birthday)) * direction;
    }
    if (sortBy === "species") {
      return ((a.species_ko || a.species || "").localeCompare(b.species_ko || b.species || "", "ko")) * direction;
    }
    if (sortBy === "personality") {
      return (
        (a.personality_ko || a.personality || "").localeCompare(
          b.personality_ko || b.personality || "",
          "ko"
        ) * direction
      );
    }
    return compareNamePriority(a.name_ko || a.name_en || "", b.name_ko || b.name_en || "") * direction;
  });
}
