export type Routine = {
  id: string;
  title: string;
  done: boolean;
  count: number;
  target: number;
  icon_url?: string;
};

export type RoutineTemplate = {
  id: string;
  title: string;
  target: number;
  icon_url: string;
};

const defaultRoutineTemplates: RoutineTemplate[] = [
  { id: "fossil", title: "화석 찾기", target: 1, icon_url: "/static/icons/museum_donated_icon.png" },
  { id: "money-tree", title: "돈나무 심기", target: 1, icon_url: "/static/icons/nook_miles_icon.png" },
  { id: "gift", title: "주민에게 선물 주기", target: 1, icon_url: "/static/icons/nav-villager-face.svg" },
  { id: "message-bottle", title: "해변 메시지 보틀 확인", target: 1, icon_url: "/static/icons/nav-more-bell.svg" },
  { id: "diy", title: "주민 DIY 레시피 확인", target: 1, icon_url: "/static/icons/diy_icon.png" },
  { id: "shop", title: "너굴상점 확인", target: 1, icon_url: "/static/icons/shopping_icon.png" },
  { id: "museum", title: "박물관 둘러보기", target: 1, icon_url: "/static/icons/critterpedia_icon.png" },
  { id: "weeds", title: "잡초 정리하기", target: 10, icon_url: "/static/icons/nook_miles_icon.png" },
];

function storageKey(islandId: number, date: string) {
  return `acnh-diary.routines.${islandId}.${date}`;
}

function templateStorageKey(islandId: number) {
  return `acnh-diary.routine-templates.${islandId}`;
}

export function getDefaultRoutineTemplates() {
  return defaultRoutineTemplates.map((template) => ({ ...template }));
}

export function getDefaultSelectedRoutineTemplates() {
  return getDefaultRoutineTemplates().slice(0, 3);
}

export function loadRoutineTemplates(islandId: number): RoutineTemplate[] {
  const raw = window.localStorage.getItem(templateStorageKey(islandId));
  if (raw === null) return getDefaultSelectedRoutineTemplates();
  try {
    const parsed = JSON.parse(raw) as Partial<RoutineTemplate>[];
    if (!Array.isArray(parsed)) return getDefaultSelectedRoutineTemplates();
    return parsed
      .filter((template) => template && String(template.id || "").trim() && String(template.title || "").trim())
      .map((template) => ({
        id: String(template.id),
        title: String(template.title),
        target: Math.max(1, Number(template.target) || 1),
        icon_url: String(template.icon_url || "/static/icons/nook_miles_icon.png"),
      }));
  } catch {
    return getDefaultSelectedRoutineTemplates();
  }
}

export function saveRoutineTemplates(islandId: number, templates: RoutineTemplate[]) {
  window.localStorage.setItem(templateStorageKey(islandId), JSON.stringify(templates));
}

export function loadRoutines(islandId: number, date: string): Routine[] {
  const templates = loadRoutineTemplates(islandId);
  const fallback: Routine[] = templates.map((template) => ({ ...template, done: false, count: 0 }));
  const raw = window.localStorage.getItem(storageKey(islandId, date));
  if (!raw) return fallback;
  try {
    const parsed = JSON.parse(raw) as Partial<Routine>[];
    if (!Array.isArray(parsed)) return fallback;
    return parsed
      .filter((routine) => routine && String(routine.id || "").trim() && String(routine.title || "").trim())
      .map((routine) => {
        const target = Math.max(1, Number(routine.target) || 1);
        const count = Math.min(target, Math.max(0, Number(routine.count) || (routine.done ? target : 0)));
        const template = templates.find((candidate) => candidate.id === String(routine.id));
        return {
          id: String(routine.id),
          title: String(routine.title),
          target,
          count,
          done: count >= target,
          icon_url: String(routine.icon_url || template?.icon_url || "/static/icons/nook_miles_icon.png"),
        };
      });
  } catch {
    return fallback;
  }
}

export function saveRoutines(islandId: number, date: string, routines: Routine[]) {
  window.localStorage.setItem(storageKey(islandId, date), JSON.stringify(routines));
}
