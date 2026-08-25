import { apiDelete, apiGet, apiPost } from "./client";

export type CalendarEntry = {
  id: number;
  visit_date: string;
  npc_name: string;
  note: string;
  checked: boolean;
};

export function getCalendarEntriesByDate(islandId: number, date: string) {
  return apiGet<CalendarEntry[]>(`/api/calendar/day?date=${encodeURIComponent(date)}`, { "X-Island-Id": String(islandId) });
}

export function saveCalendarEntry(islandId: number, payload: Omit<CalendarEntry, "id"> & { id?: number }) {
  return apiPost<CalendarEntry>("/api/calendar", payload, { "X-Island-Id": String(islandId) });
}

export function deleteCalendarEntry(islandId: number, entryId: number) {
  return apiDelete<{ deleted: boolean }>(`/api/calendar/${entryId}`, { "X-Island-Id": String(islandId) });
}

export async function getRecentCalendarEntries(islandId: number, endDate: string) {
  const end = new Date(`${endDate}T12:00:00`);
  const dates = Array.from({ length: 7 }, (_, index) => {
    const date = new Date(end);
    date.setDate(end.getDate() - index);
    return date.toISOString().slice(0, 10);
  });
  const batches = await Promise.all(dates.map((date) => getCalendarEntriesByDate(islandId, date)));
  return batches.flat().sort((a, b) => b.visit_date.localeCompare(a.visit_date) || b.id - a.id);
}
