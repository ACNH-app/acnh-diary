import { Check, Fish, Menu } from "lucide-react";
import type { ReactNode } from "react";
import { useCallback, useEffect, useState, type FormEvent } from "react";

import { deleteCalendarEntry, getCalendarEntriesByDate, saveCalendarEntry, type CalendarEntry } from "../../api/calendar";
import { getDefaultRoutineTemplates, loadRoutineTemplates, loadRoutines, saveRoutineTemplates, saveRoutines, type Routine as LocalRoutine, type RoutineTemplate } from "../../api/localRoutines";
import { getHomeCreaturesNow, getHomeSummary, type Creature, type HomeSummary } from "../../api/home";
import { getIslandProfile, type IslandProfile } from "../../api/islands";
import { BottomNavigation, type AppTab, type BottomNavItem } from "../../components/layout/BottomNavigation";
import { MobileScreen } from "../../components/layout/MobileScreen";
import { Pill } from "../../components/ui/Pill";
import { npcOptions } from "../../data/npcs";
import { useAsync } from "../../hooks/useAsync";

type TodayScreenProps = {
  islandId: number;
  islandName: string;
  navItems: BottomNavItem[];
  currentTab: AppTab;
  onTabChange: (tab: AppTab) => void;
  onOpenMenu: () => void;
};

type TodayData = {
  summary: HomeSummary;
  profile: IslandProfile;
  creatures: Creature[];
  visits: CalendarEntry[];
};

export function TodayScreen({
  islandId,
  islandName,
  navItems,
  currentTab,
  onTabChange,
  onOpenMenu,
}: TodayScreenProps) {
  const loadToday = useCallback(async (): Promise<TodayData> => {
    const [summary, profile, creatures] = await Promise.all([
      getHomeSummary(islandId),
      getIslandProfile(islandId),
      getHomeCreaturesNow(islandId),
    ]);
    const week = buildWeekDays(summary.effective_datetime.slice(0, 10));
    const visitBatches = await Promise.all(week.map((day) => getCalendarEntriesByDate(islandId, day.date)));
    const visits = visitBatches.flat().sort((a, b) => b.visit_date.localeCompare(a.visit_date) || b.id - a.id);
    return { summary, profile, creatures: creatures.items, visits };
  }, [islandId]);
  const todayState = useAsync(loadToday);
  const [visitSaving, setVisitSaving] = useState(false);
  const [routineManagerOpen, setRoutineManagerOpen] = useState(false);
  const [editingRoutineId, setEditingRoutineId] = useState<string | null>(null);
  const [editingRoutineTitle, setEditingRoutineTitle] = useState("");
  const [editingRoutineTarget, setEditingRoutineTarget] = useState("1");
  const today = todayState.status === "success" ? todayState.data : null;
  const summary = today?.summary;
  const profile = today?.profile;
  const hemisphereLabel = profile?.hemisphere === "south" ? "남반구" : "북반구";
  const effectiveDate = summary ? formatDate(summary.effective_datetime) : "오늘";
  const event = summary?.upcoming_events[0];
  const recipe = summary?.seasonal_recipes_now[0];
  const routineDate = summary?.effective_datetime.slice(0, 10) ?? new Date().toISOString().slice(0, 10);
  const npcWeek = buildWeekDays(routineDate);
  const [npcPickerDate, setNpcPickerDate] = useState<string | null>(null);
  const selectedNpcDay = npcPickerDate ? npcWeek.find((day) => day.date === npcPickerDate) ?? null : null;
  const [routineTemplates, setRoutineTemplates] = useState<RoutineTemplate[]>(() => loadRoutineTemplates(islandId));
  const [routines, setRoutines] = useState<LocalRoutine[]>(() => loadRoutines(islandId, routineDate));
  const allRoutineTemplates = [...getDefaultRoutineTemplates(), ...routineTemplates.filter((template) => !getDefaultRoutineTemplates().some((defaultTemplate) => defaultTemplate.id === template.id))];

  useEffect(() => {
    setRoutineTemplates(loadRoutineTemplates(islandId));
    setRoutines(loadRoutines(islandId, routineDate));
    setNpcPickerDate(null);
  }, [islandId, routineDate]);

  useEffect(() => {
    function handleProfileUpdated(event: Event) {
      const islandEvent = event as CustomEvent<{ islandId?: number }>;
      if (islandEvent.detail?.islandId === islandId) todayState.reload();
    }
    window.addEventListener("acnh-diary.profile-updated", handleProfileUpdated);
    return () => window.removeEventListener("acnh-diary.profile-updated", handleProfileUpdated);
  }, [islandId]);

  function toggleRoutine(id: string) {
    const next = routines.map((routine) => {
      if (routine.id !== id) return routine;
      const count = routine.done ? 0 : routine.target;
      return { ...routine, count, done: count >= routine.target };
    });
    setRoutines(next);
    saveRoutines(islandId, routineDate, next);
  }

  function changeRoutineCount(id: string, delta: number) {
    const next = routines.map((routine) => {
      if (routine.id !== id || routine.target <= 1) return routine;
      const count = Math.min(routine.target, Math.max(0, routine.count + delta));
      return { ...routine, count, done: count >= routine.target };
    });
    setRoutines(next);
    saveRoutines(islandId, routineDate, next);
  }

  function addRoutine(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const title = String(form.get("routine-title") || "").trim();
    if (!title) return;
    const target = Math.max(1, Number(form.get("routine-target")) || 1);
    const id = `custom-${Date.now()}`;
    const template = { id, title, target, icon_url: "/static/icons/nook_miles_icon.png" };
    const next = [...routines, { ...template, done: false, count: 0 }];
    const nextTemplates = [...routineTemplates, template];
    setRoutines(next);
    setRoutineTemplates(nextTemplates);
    saveRoutineTemplates(islandId, nextTemplates);
    saveRoutines(islandId, routineDate, next);
    event.currentTarget.reset();
  }

  function addRoutineTemplate(template: RoutineTemplate) {
    if (routineTemplates.some((item) => item.id === template.id)) return;
    const nextTemplates = [...routineTemplates, template];
    const nextRoutines = [...routines, { ...template, done: false, count: 0 }];
    setRoutineTemplates(nextTemplates);
    setRoutines(nextRoutines);
    saveRoutineTemplates(islandId, nextTemplates);
    saveRoutines(islandId, routineDate, nextRoutines);
  }

  function removeRoutine(id: string) {
    const next = routines.filter((routine) => routine.id !== id);
    const nextTemplates = routineTemplates.filter((template) => template.id !== id);
    setRoutines(next);
    setRoutineTemplates(nextTemplates);
    saveRoutineTemplates(islandId, nextTemplates);
    saveRoutines(islandId, routineDate, next);
  }

  function moveRoutine(id: string, direction: -1 | 1) {
    const index = routines.findIndex((routine) => routine.id === id);
    const nextIndex = index + direction;
    if (index < 0 || nextIndex < 0 || nextIndex >= routines.length) return;
    const next = [...routines];
    [next[index], next[nextIndex]] = [next[nextIndex], next[index]];
    const templateIndex = routineTemplates.findIndex((template) => template.id === id);
    const nextTemplateIndex = templateIndex + direction;
    const nextTemplates = [...routineTemplates];
    if (templateIndex >= 0 && nextTemplateIndex >= 0 && nextTemplateIndex < nextTemplates.length) {
      [nextTemplates[templateIndex], nextTemplates[nextTemplateIndex]] = [nextTemplates[nextTemplateIndex], nextTemplates[templateIndex]];
    }
    setRoutines(next);
    setRoutineTemplates(nextTemplates);
    saveRoutineTemplates(islandId, nextTemplates);
    saveRoutines(islandId, routineDate, next);
  }

  function startEditingRoutine(routine: LocalRoutine) {
    setEditingRoutineId(routine.id);
    setEditingRoutineTitle(routine.title);
    setEditingRoutineTarget(String(routine.target));
  }

  function saveRoutineTitle(id: string) {
    const title = editingRoutineTitle.trim();
    if (!title) return;
    const target = Math.max(1, Number(editingRoutineTarget) || 1);
    const next = routines.map((routine) => {
      if (routine.id !== id) return routine;
      const count = Math.min(target, routine.count);
      return { ...routine, title, target, count, done: count >= target };
    });
    const nextTemplates = routineTemplates.map((template) => template.id === id ? { ...template, title, target } : template);
    setRoutines(next);
    setRoutineTemplates(nextTemplates);
    saveRoutineTemplates(islandId, nextTemplates);
    saveRoutines(islandId, routineDate, next);
    setEditingRoutineId(null);
    setEditingRoutineTitle("");
    setEditingRoutineTarget("1");
  }

  async function toggleNpcVisit(visitDate: string, npcName: string) {
    if (!today) return;
    setVisitSaving(true);
    try {
      const matchingEntries = today.visits.filter((visit) => visit.visit_date === visitDate && normalizeNpcName(visit.npc_name) === normalizeNpcName(npcName));
      if (matchingEntries.length > 0) {
        await Promise.all(matchingEntries.map((visit) => deleteCalendarEntry(islandId, visit.id)));
      } else {
        await saveCalendarEntry(islandId, { visit_date: visitDate, npc_name: npcName, note: "", checked: false });
      }
      todayState.reload();
    } finally {
      setVisitSaving(false);
    }
  }

  async function handleDeleteVisit(entryId: number) {
    await deleteCalendarEntry(islandId, entryId);
    todayState.reload();
  }

  async function resetNpcWeek() {
    if (!today) return;
    const weekDates = new Set(npcWeek.map((day) => day.date));
    const weekVisits = today.visits.filter((visit) => weekDates.has(visit.visit_date));
    if (weekVisits.length === 0) return;
    if (!window.confirm("이번 주 NPC 방문 기록을 모두 초기화할까요?")) return;
    setVisitSaving(true);
    try {
      await Promise.all(weekVisits.map((visit) => deleteCalendarEntry(islandId, visit.id)));
      todayState.reload();
    } finally {
      setVisitSaving(false);
    }
  }

  return (
    <MobileScreen
      action={
        <button className="menu-button" onClick={onOpenMenu} title="섬 정보" type="button">
          <Menu aria-hidden="true" size={22} />
        </button>
      }
      footer={<BottomNavigation items={navItems} onChange={onTabChange} value={currentTab} />}
      subtitle={`${islandName}의 오늘을 차분하게 준비해요.`}
      title="오늘"
      tone="yellow"
    >
      {todayState.status === "loading" ? <div className="screen-state">오늘의 섬 정보를 불러오는 중이에요…</div> : null}
      {todayState.status === "error" ? (
        <div className="screen-state screen-state--error" role="alert">
          오늘 요약을 불러오지 못했어요. 백엔드 연결 상태를 확인해 주세요.
          <button className="retry-button" onClick={todayState.reload} type="button">다시 시도</button>
        </div>
      ) : null}

      <section className="date-card">
        <div className="date-card__chips">
          <Pill tone="mint">{hemisphereLabel} {summary ? `${dateMonth(summary.effective_datetime)}월` : ""}</Pill>
          <Pill tone="sun">{islandName} · {summary ? dateTime(summary.effective_datetime) : "—"}</Pill>
          <Pill tone="sky">{summary?.season_ko ?? "시즌 확인 중"}</Pill>
        </div>
        <h2>{effectiveDate}</h2>
        <p>{summary ? `${summary.zodiac_ko} · 오늘도 섬 산책하기 좋은 날이에요.` : "섬 정보를 준비하고 있어요."}</p>
        <div className="date-card__tags">
          <Pill tone="leaf">{summary?.blooming_shrubs_now[0] ?? "꽃 피는 시기 확인 중"}</Pill>
          <Pill tone="violet">{event ? `이벤트 ${event.delta_days === 0 ? "오늘" : `${event.delta_days}일 후`}` : "이벤트 없음"}</Pill>
          <Pill tone="sun">{recipe ?? "시즌 레시피 없음"}</Pill>
        </div>
      </section>

      <section className="task-card">
        <div className="routine-heading">
          <div className="section-label section-label--orange">오늘의 루틴</div>
          <button className="routine-manage-button" onClick={() => setRoutineManagerOpen(true)} type="button">루틴 관리</button>
        </div>
        <div className="progress-row">
          <span className="progress-track"><span style={{ width: `${routines.length ? (routines.filter((routine) => routine.done).length / routines.length) * 100 : 0}%` }} /></span>
          <strong>{routines.filter((routine) => routine.done).length} / {routines.length} 완료</strong>
        </div>
        <ul className="routine-list">
          {routines.map((routine) => (
            <Routine
              count={routine.count}
              done={routine.done}
              iconUrl={routine.icon_url}
              key={routine.id}
              label={routine.title}
              onCountChange={routine.target > 1 ? (delta) => changeRoutineCount(routine.id, delta) : undefined}
              onToggle={() => toggleRoutine(routine.id)}
              target={routine.target}
            />
          ))}
        </ul>
      </section>

      {routineManagerOpen ? (
        <div className="detail-overlay routine-manager-overlay" onClick={() => setRoutineManagerOpen(false)} role="presentation">
          <section className="routine-manager-modal" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true" aria-label="루틴 관리">
            <div className="routine-modal-header">
              <div>
                <h2>루틴 관리</h2>
                <p>오늘 화면에 표시할 루틴을 선택하세요.</p>
              </div>
              <button className="detail-close" onClick={() => setRoutineManagerOpen(false)} type="button">닫기</button>
            </div>
            <div className="routine-modal-section">
              <div className="routine-manager-header"><strong>표시 중인 루틴</strong><small>수정·삭제·순서 변경이 오늘부터 적용됩니다.</small></div>
              <ul className="routine-manage-list">
                {routineTemplates.map((template, index) => {
                  const routine = routines.find((item) => item.id === template.id);
                  if (!routine) return null;
                  const editing = editingRoutineId === routine.id;
                  return (
                    <li className="routine-manage-row" key={routine.id}>
                      <img alt="" src={routine.icon_url || template.icon_url} />
                      {editing ? (
                        <div className="routine-edit-fields">
                          <input aria-label={`${routine.title} 이름 수정`} onChange={(event) => setEditingRoutineTitle(event.target.value)} value={editingRoutineTitle} />
                          <input aria-label={`${routine.title} 목표 횟수 수정`} min="1" onChange={(event) => setEditingRoutineTarget(event.target.value)} type="number" value={editingRoutineTarget} />
                        </div>
                      ) : <span><strong>{routine.title}</strong><small>{routine.target > 1 ? `목표 ${routine.target}회` : "체크형 루틴"}</small></span>}
                      <div className="routine-manage-actions">
                        {editing ? <button onClick={() => saveRoutineTitle(routine.id)} type="button">저장</button> : <button onClick={() => startEditingRoutine(routine)} type="button">수정</button>}
                        <button disabled={index === 0} onClick={() => moveRoutine(routine.id, -1)} title="위로 이동" type="button">↑</button>
                        <button disabled={index === routineTemplates.length - 1} onClick={() => moveRoutine(routine.id, 1)} title="아래로 이동" type="button">↓</button>
                        <button className="routine-delete-button" onClick={() => removeRoutine(routine.id)} type="button">삭제</button>
                      </div>
                    </li>
                  );
                })}
                {routineTemplates.length === 0 ? <li className="routine-manager-empty">표시 중인 루틴이 없어요. 아래에서 추가해 주세요.</li> : null}
              </ul>
            </div>
            <div className="routine-modal-section">
              <div className="routine-manager-header"><strong>기본 루틴 추가</strong><small>원하는 항목을 눌러 오늘 화면에 표시하세요.</small></div>
              <div className="routine-template-list">
                {allRoutineTemplates.filter((template) => !routineTemplates.some((selected) => selected.id === template.id)).map((template) => (
                  <button className="routine-template" key={template.id} onClick={() => addRoutineTemplate(template)} type="button">
                    <img alt="" src={template.icon_url} />
                    <span>{template.title}</span>
                    <b>+</b>
                  </button>
                ))}
                {allRoutineTemplates.every((template) => routineTemplates.some((selected) => selected.id === template.id)) ? <span className="routine-manager-empty">추가할 기본 루틴이 없어요.</span> : null}
              </div>
            </div>
            <div className="routine-modal-section">
              <div className="routine-manager-header"><strong>내 루틴 직접 추가</strong><small>기본 목록에 없는 루틴도 만들 수 있어요.</small></div>
              <form className="routine-form" onSubmit={addRoutine}>
                <input aria-label="사용자 루틴 이름" name="routine-title" placeholder="예: 섬 한 바퀴 산책" />
                <input aria-label="사용자 루틴 목표 횟수" min="1" name="routine-target" type="number" defaultValue="1" />
                <button type="submit">추가</button>
              </form>
            </div>
          </section>
        </div>
      ) : null}

      <section className="creature-card">
        <div className="section-label section-label--green">지금 가능한 생물</div>
        <p>{today ? `미수집 생물 ${today.creatures.length}종` : "현재 시간대에 맞는 미수집 생물"}</p>
        {today?.creatures.slice(0, 4).map((creature) => (
          <Creature
            key={`${creature.catalog_type}-${creature.id}`}
            icon={creature.icon_url ? <img alt="" className="creature-image" src={creature.icon_url} /> : <Fish size={18} />}
            name={creature.name_ko || creature.name_en}
            place={`${creature.location} · ${creature.time}`}
            price={creature.catalog_type === "fish" ? "물고기" : creature.catalog_type === "bugs" ? "곤충" : "해산물"}
          />
        ))}
        {today && today.creatures.length === 0 ? <div className="empty-state">현재 시간대에 미수집 생물이 없어요.</div> : null}
      </section>

      <section className="npc-card">
        <div className="section-row"><h2>이번 주 NPC 방문</h2></div>
        <p className="npc-helper">월요일부터 일요일까지 요일을 누르면 그 자리에서 방문 NPC를 선택할 수 있어요.</p>
        <div className="npc-week-summary">
          {npcWeek.map((day) => {
            const dayVisits = today?.visits.filter((visit) => visit.visit_date === day.date) ?? [];
            const isOpen = npcPickerDate === day.date;
            return (
              <button aria-expanded={isOpen} aria-label={`${day.date} ${dayVisits.length ? `${dayVisits.map((visit) => visit.npc_name).join(", ")} 방문` : "방문 기록 없음"}`} className={isOpen ? "npc-day-summary is-active" : "npc-day-summary"} onClick={() => setNpcPickerDate(isOpen ? null : day.date)} key={day.date} type="button">
                <strong>{day.weekday}</strong>
                <small>{day.date.slice(5).replace("-", ".")}</small>
                <span className="npc-summary-icons">
                  {dayVisits.length > 0 ? dayVisits.slice(0, 3).map((visit) => <img alt="" key={visit.id} src={npcOptions.find((option) => normalizeNpcName(option.name) === normalizeNpcName(visit.npc_name))?.icon_url || "/static/icons/nav-more-bell.svg"} />) : <span className="npc-summary-placeholder">+</span>}
                </span>
                <em>{dayVisits.length ? `${dayVisits.length}명` : "선택"}</em>
              </button>
            );
          })}
        </div>
        {selectedNpcDay ? (
          <div className="npc-inline-picker">
            <div className="npc-inline-picker-header">
              <div>
                <strong>{selectedNpcDay.weekday} 방문 NPC</strong>
                <small>{selectedNpcDay.date.slice(5).replace("-", ".")} · 다시 누르면 해제</small>
              </div>
              <button className="npc-inline-close" onClick={() => setNpcPickerDate(null)} type="button">접기</button>
            </div>
            <div className="npc-picker-grid">
              {npcOptions.map((option) => {
                const dayVisits = today?.visits.filter((visit) => visit.visit_date === selectedNpcDay.date) ?? [];
                const selected = dayVisits.some((visit) => normalizeNpcName(visit.npc_name) === normalizeNpcName(option.name));
                return (
                  <button aria-pressed={selected} className={selected ? "npc-picker-chip is-selected" : "npc-picker-chip"} disabled={visitSaving} key={option.name} onClick={() => toggleNpcVisit(selectedNpcDay.date, option.name)} type="button">
                    <img alt="" src={option.icon_url} />
                    <span>{option.name}</span>
                  </button>
                );
              })}
            </div>
            {(today?.visits.filter((visit) => visit.visit_date === selectedNpcDay.date && !npcOptions.some((option) => normalizeNpcName(option.name) === normalizeNpcName(visit.npc_name))) ?? []).map((visit) => (
              <button className="npc-unknown-entry" key={visit.id} onClick={() => handleDeleteVisit(visit.id)} type="button">{visit.npc_name} ×</button>
            ))}
            <div className="npc-inline-picker-actions">
              <span>NPC를 누르면 선택·해제돼요.</span>
              <button className="npc-reset-button" disabled={visitSaving} onClick={resetNpcWeek} type="button">이번 주 초기화</button>
            </div>
          </div>
        ) : null}
        {today && today.visits.length === 0 ? <div className="empty-state">아직 선택된 NPC 방문 기록이 없어요.</div> : null}
      </section>

      <div className="shortcut-grid">
        <button className="shortcut-card" type="button">
          <strong>다가오는 이벤트</strong>
          <span>{event?.name_ko || "등록된 이벤트가 없어요"}</span>
        </button>
        <button className="shortcut-card" type="button">
          <strong>오늘의 계절 정보</strong>
          <span>{summary?.season_ko ?? "데이터를 불러오는 중이에요"}</span>
        </button>
      </div>
    </MobileScreen>
  );
}

function Routine({
  count,
  done,
  label,
  iconUrl,
  onCountChange,
  onToggle,
  target,
}: {
  count: number;
  done: boolean;
  label: string;
  iconUrl?: string;
  onCountChange?: (delta: number) => void;
  onToggle: () => void;
  target: number;
}) {
  return (
    <li className={done ? "routine is-done" : "routine"}>
      <button aria-label={`${label} ${done ? "완료 해제" : "완료 처리"}`} className="routine-icon-toggle" onClick={onToggle} type="button">
        <img alt="" className="routine-icon" src={iconUrl || "/static/icons/nook_miles_icon.png"} />
        {done ? <span className="routine-check"><Check aria-hidden="true" size={13} /></span> : null}
      </button>
      <strong>{label}</strong>
      {onCountChange ? <span className="routine-counter"><button aria-label={`${label} 횟수 줄이기`} disabled={count === 0} onClick={() => onCountChange(-1)} type="button">−</button><b>{count}/{target}</b><button aria-label={`${label} 횟수 늘리기`} disabled={count >= target} onClick={() => onCountChange(1)} type="button">+</button></span> : null}
    </li>
  );
}

function Creature({ icon, name, place, price }: { icon: ReactNode; name: string; place: string; price: string }) {
  return (
    <article className="creature-row">
      <span className="creature-icon">{icon}</span>
      <span><strong>{name}</strong><small>{place}</small></span>
      <Pill tone="mint">{price}</Pill>
    </article>
  );
}

function normalizeNpcName(name: string) {
  return name.trim().toLowerCase().replace(/[.\s]/g, "");
}

function buildWeekDays(endDate: string) {
  const end = new Date(`${endDate}T12:00:00`);
  const dayOfWeek = end.getDay();
  const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
  const monday = new Date(end);
  monday.setDate(end.getDate() + mondayOffset);
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(monday);
    date.setDate(monday.getDate() + index);
    return {
      date: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`,
      weekday: date.toLocaleDateString("ko-KR", { weekday: "short" }),
    };
  });
}

function parseDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function dateMonth(value: string) {
  const date = parseDate(value);
  return date ? String(date.getMonth() + 1) : "";
}

function dateTime(value: string) {
  const date = parseDate(value);
  return date ? date.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", hour12: false }) : "—";
}

function formatDate(value: string) {
  const date = parseDate(value);
  return date
    ? date.toLocaleDateString("ko-KR", { month: "long", day: "numeric", weekday: "long" })
    : "오늘";
}
