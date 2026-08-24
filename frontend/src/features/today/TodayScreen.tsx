import {
  CalendarDays,
  Check,
  Fish,
  Home,
  Leaf,
  ListChecks,
  Menu,
  Settings,
  UsersRound,
} from "lucide-react";
import type { ReactNode } from "react";
import { useCallback, useState } from "react";

import { getHomeSummary, getNav } from "../../api/home";
import { AppShell } from "../../components/layout/AppShell";
import { BottomNavigation, type AppTab, type BottomNavItem } from "../../components/layout/BottomNavigation";
import { MobileScreen } from "../../components/layout/MobileScreen";
import { Button } from "../../components/ui/Button";
import { Pill } from "../../components/ui/Pill";
import { CatalogScreen } from "../catalog/CatalogScreen";
import { GuideScreen } from "../guide/GuideScreen";
import { IslandSidebar } from "../island/IslandSidebar";
import { MyIslandScreen } from "../island/MyIslandScreen";
import { useAsync } from "../../hooks/useAsync";

const fallbackNav: BottomNavItem[] = [
  { value: "today", label: "오늘", icon: Home },
  { value: "catalog", label: "도감", icon: ListChecks },
  { value: "guide", label: "공략", icon: CalendarDays },
  { value: "island", label: "내 섬", icon: UsersRound },
];

export function TodayScreen() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentTab, setCurrentTab] = useState<AppTab>("today");
  const loadNav = useCallback(() => getNav(), []);
  const loadSummary = useCallback(() => getHomeSummary(), []);
  const navState = useAsync(loadNav);
  const summaryState = useAsync(loadSummary);

  const summary = summaryState.status === "success" ? summaryState.data : null;
  const islandName = summary?.island?.island_name || "왓섬";

  const shellNavItems =
    navState.status === "success" && navState.data.length > 0
      ? navState.data.map((item) => ({
          key: item.key,
          label: item.label,
          icon:
            item.key === "catalog"
              ? ListChecks
              : item.key === "calendar"
                ? CalendarDays
                : item.key === "villagers"
                  ? UsersRound
                  : item.key === "settings"
                    ? Settings
                    : Home,
        }))
      : fallbackNav.map((item) => ({ key: item.value, label: item.label, icon: item.icon }));

  const screen =
    currentTab === "catalog" ? (
      <CatalogScreen currentTab={currentTab} navItems={fallbackNav} onTabChange={setCurrentTab} />
    ) : currentTab === "guide" ? (
      <GuideScreen currentTab={currentTab} navItems={fallbackNav} onTabChange={setCurrentTab} />
    ) : currentTab === "island" ? (
      <MyIslandScreen
        currentTab={currentTab}
        islandName={islandName}
        navItems={fallbackNav}
        onOpenMenu={() => setSidebarOpen(true)}
        onTabChange={setCurrentTab}
      />
    ) : (
      <TodayHomeScreen
        currentTab={currentTab}
        navItems={fallbackNav}
        onOpenMenu={() => setSidebarOpen(true)}
        onTabChange={setCurrentTab}
      />
    );

  return (
    <AppShell navItems={shellNavItems}>
      <main className="today-stage">
        {screen}

        <aside className="tablet-context">
          <Pill tone="leaf">Tablet preview</Pill>
          <h2>모바일 감성, 태블릿 밀도</h2>
          <p>메인 작업은 가운데 휴대폰 폭으로 유지하고, 태블릿에서는 섬 정보와 빠른 관리 패널을 함께 보여줍니다.</p>
          <Button
            icon={<Settings aria-hidden="true" size={18} />}
            onClick={() => setSidebarOpen(true)}
            variant="secondary"
          >
            섬 정보 열기
          </Button>
        </aside>
      </main>
      <IslandSidebar islandName={islandName} onClose={() => setSidebarOpen(false)} open={sidebarOpen} />
    </AppShell>
  );
}

type TodayHomeScreenProps = {
  navItems: BottomNavItem[];
  currentTab: AppTab;
  onTabChange: (tab: AppTab) => void;
  onOpenMenu: () => void;
};

function TodayHomeScreen({ navItems, currentTab, onTabChange, onOpenMenu }: TodayHomeScreenProps) {
  return (
    <MobileScreen
      action={
        <button className="menu-button" onClick={onOpenMenu} title="섬 정보" type="button">
          <Menu aria-hidden="true" size={22} />
        </button>
      }
      footer={<BottomNavigation items={navItems} onChange={onTabChange} value={currentTab} />}
      subtitle="왓섬의 오늘을 차분하게 준비해요."
      title="오늘"
      tone="yellow"
    >
      <section className="date-card">
        <div className="date-card__chips">
          <Pill tone="mint">북반구 8월</Pill>
          <Pill tone="sun">왓섬 · 14:30</Pill>
          <Pill tone="sky">맑음</Pill>
        </div>
        <h2>8월 24일 월요일</h2>
        <p>오늘도 섬 산책하기 좋은 날이에요.</p>
        <div className="date-card__tags">
          <Pill tone="leaf">마수리 출중</Pill>
          <Pill tone="violet">이벤트 1건</Pill>
          <Pill tone="sun">레시피 60%</Pill>
        </div>
      </section>

      <section className="task-card">
        <div className="section-label section-label--orange">오늘의 루틴</div>
        <div className="progress-row">
          <span className="progress-track">
            <span style={{ width: "56%" }} />
          </span>
          <strong>4 / 7 완료</strong>
        </div>
        <ul className="routine-list">
          <Routine done label="화석 찾기" />
          <Routine done label="돈나무 심기" />
          <Routine label="주민에게 선물 주기" />
        </ul>
      </section>

      <section className="creature-card">
        <div className="section-label section-label--green">지금 가능한 생물</div>
        <p>현재 시간대에 맞는 미수집 생물</p>
        <Creature icon={<Fish size={18} />} name="청새치" place="바다 · 16:00-09:00" price="4,000벨" />
        <Creature icon={<Fish size={18} />} name="황금연어" place="강 상류 · 종일" price="15,000벨" />
      </section>

      <div className="shortcut-grid">
        <button className="shortcut-card" type="button">
          <strong>다가오는 이벤트</strong>
          <span>8월 22일 곤충 채집 대회</span>
        </button>
        <button className="shortcut-card" type="button">
          <strong>오늘의 팁</strong>
          <span>비 오는 날은 실러캔스 확인</span>
        </button>
      </div>
    </MobileScreen>
  );
}

type RoutineProps = {
  done?: boolean;
  label: string;
};

function Routine({ done = false, label }: RoutineProps) {
  return (
    <li className={done ? "routine is-done" : "routine"}>
      <span>{done ? <Check aria-hidden="true" size={14} /> : null}</span>
      <strong>{label}</strong>
    </li>
  );
}

type CreatureProps = {
  icon: ReactNode;
  name: string;
  place: string;
  price: string;
};

function Creature({ icon, name, place, price }: CreatureProps) {
  return (
    <article className="creature-row">
      <span className="creature-icon">{icon}</span>
      <span>
        <strong>{name}</strong>
        <small>{place}</small>
      </span>
      <Pill tone="mint">{price}</Pill>
    </article>
  );
}
