import {
  CalendarDays,
  Home,
  ListChecks,
  Settings,
  UsersRound,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { deleteIsland, getIslands, type Island } from "../api/islands";
import { AppShell, type NavItem } from "../components/layout/AppShell";
import { type AppTab, type BottomNavItem } from "../components/layout/BottomNavigation";
import { useAsync } from "../hooks/useAsync";
import { CatalogScreen } from "../features/catalog/CatalogScreen";
import { GuideScreen } from "../features/guide/GuideScreen";
import { IslandSetupScreen } from "../features/island/IslandSetupScreen";
import { IslandSidebar } from "../features/island/IslandSidebar";
import { MyIslandScreen } from "../features/island/MyIslandScreen";
import { ResidentsScreen } from "../features/residents/ResidentsScreen";
import { TodayScreen } from "../features/today/TodayScreen";

const islandStorageKey = "acnh-diary.active-island-id";

const bottomNavItems: BottomNavItem[] = [
  { value: "today", label: "오늘", icon: Home },
  { value: "catalog", label: "도감", icon: ListChecks },
  { value: "villagers", label: "주민", icon: UsersRound },
  { value: "island", label: "내 섬", icon: Settings },
];

const shellNavItems: NavItem[] = [
  { key: "/today", label: "오늘", icon: Home },
  { key: "/catalog", label: "도감", icon: ListChecks },
  { key: "/villagers", label: "주민", icon: UsersRound },
  { key: "/my-island", label: "내 섬", icon: Settings },
  { key: "/guide", label: "공략", icon: CalendarDays },
];

const routeByTab: Record<AppTab, string> = {
  today: "/today",
  catalog: "/catalog",
  villagers: "/villagers",
  island: "/my-island",
  guide: "/guide",
};

export function App() {
  return (
    <BrowserRouter>
      <AppRouter />
    </BrowserRouter>
  );
}

function AppRouter() {
  const location = useLocation();
  const navigate = useNavigate();
  const loadIslands = useCallback(() => getIslands(), []);
  const islandsState = useAsync(loadIslands);
  const [activeIslandId, setActiveIslandId] = useState<number | null>(() => readStoredIslandId());
  const [createdIsland, setCreatedIsland] = useState<Island | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    function handleProfileUpdated() {
      islandsState.reload();
    }
    window.addEventListener("acnh-diary.profile-updated", handleProfileUpdated);
    return () => window.removeEventListener("acnh-diary.profile-updated", handleProfileUpdated);
  }, []);

  useEffect(() => {
    if (islandsState.status !== "success") {
      return;
    }

    const islands = islandsState.data;
    if (islands.length === 0) {
      if (location.pathname !== "/onboarding") {
        navigate("/onboarding", { replace: true });
      }
      return;
    }

    const storedIsland = islands.find((island) => island.id === activeIslandId);
    const justCreatedIsland = createdIsland?.id === activeIslandId ? createdIsland : undefined;
    const nextIsland = storedIsland ?? justCreatedIsland ?? islands[0];
    if (nextIsland.id !== activeIslandId) {
      setActiveIslandId(nextIsland.id);
      window.localStorage.setItem(islandStorageKey, String(nextIsland.id));
    }
    if (location.pathname === "/") {
      navigate("/today", { replace: true });
    }
  }, [activeIslandId, createdIsland, islandsState, location.pathname, navigate]);

  const activeIsland = useMemo(
    () => islandsState.status === "success"
      ? islandsState.data.find((island) => island.id === activeIslandId)
        ?? (createdIsland?.id === activeIslandId ? createdIsland : undefined)
        ?? islandsState.data[0]
      : undefined,
    [activeIslandId, islandsState],
  );

  if (location.pathname === "/onboarding") {
    return (
      <IslandSetupScreen
        onCreated={(island) => {
          setCreatedIsland(island);
          setActiveIslandId(island.id);
          window.localStorage.setItem(islandStorageKey, String(island.id));
          islandsState.reload();
          navigate("/today", { replace: true });
        }}
      />
    );
  }

  if (islandsState.status === "loading") {
    return <AppState message="섬 정보를 불러오는 중이에요…" />;
  }

  if (islandsState.status === "error") {
    return <AppState message="섬 정보를 불러오지 못했어요. 백엔드가 실행 중인지 확인해 주세요." onRetry={islandsState.reload} />;
  }

  if (!activeIsland) {
    return <AppState message="등록된 섬이 없어 온보딩으로 이동할게요." />;
  }

  const handleTabChange = (tab: AppTab) => navigate(routeByTab[tab]);
  const handleSelectIsland = (islandId: number) => {
    setActiveIslandId(islandId);
    window.localStorage.setItem(islandStorageKey, String(islandId));
    setSidebarOpen(false);
  };
  const handleDeleteIsland = async () => {
    if (islandsState.data.length <= 1 || !window.confirm("현재 섬과 기록을 모두 삭제할까요?")) return;
    await deleteIsland(activeIsland.id);
    const nextIsland = islandsState.data.find((island) => island.id !== activeIsland.id);
    if (nextIsland) {
      handleSelectIsland(nextIsland.id);
      islandsState.reload();
      navigate("/today", { replace: true });
    }
  };
  const currentTab = tabForPath(location.pathname);
  const handleShellNavigate = (key: string) => {
    if (key.startsWith("/")) {
      navigate(key);
    }
  };

  return (
    <AppShell
      activeKey={location.pathname}
      navItems={shellNavItems}
      onNavigate={handleShellNavigate}
    >
      <main className="today-stage">
        <Routes>
          <Route
            path="/today"
            element={
              <TodayScreen
                currentTab={currentTab}
                islandId={activeIsland.id}
                islandName={activeIsland.name}
                navItems={bottomNavItems}
                onOpenMenu={() => setSidebarOpen(true)}
                onTabChange={handleTabChange}
              />
            }
          />
          <Route
            path="/catalog"
            element={<CatalogScreen currentTab={currentTab} islandId={activeIsland.id} navItems={bottomNavItems} onTabChange={handleTabChange} />}
          />
          <Route
            path="/villagers"
            element={<ResidentsScreen currentTab={currentTab} islandId={activeIsland.id} navItems={bottomNavItems} onTabChange={handleTabChange} />}
          />
          <Route
            path="/my-island"
            element={
              <MyIslandScreen
                currentTab={currentTab}
                islandId={activeIsland.id}
                islandName={activeIsland.name}
                navItems={bottomNavItems}
                onOpenMenu={() => setSidebarOpen(true)}
                onTabChange={handleTabChange}
              />
            }
          />
          <Route
            path="/guide"
            element={<GuideScreen currentTab="guide" navItems={bottomNavItems} onTabChange={handleTabChange} />}
          />
          <Route path="*" element={<Navigate replace to="/today" />} />
        </Routes>
      </main>
      <IslandSidebar
        activeIslandId={activeIsland.id}
        islands={islandsState.data}
        islandName={activeIsland.name}
        onClose={() => setSidebarOpen(false)}
        onAddIsland={() => { setSidebarOpen(false); navigate("/onboarding"); }}
        onDeleteIsland={handleDeleteIsland}
        onSelectIsland={handleSelectIsland}
        open={sidebarOpen}
      />
    </AppShell>
  );
}

function readStoredIslandId(): number | null {
  const raw = window.localStorage.getItem(islandStorageKey);
  const id = Number(raw);
  return Number.isInteger(id) && id > 0 ? id : null;
}

function tabForPath(pathname: string): AppTab {
  if (pathname === "/catalog") return "catalog";
  if (pathname === "/villagers") return "villagers";
  if (pathname === "/my-island") return "island";
  if (pathname === "/guide") return "guide";
  return "today";
}

function AppState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <main className="app-state" role="status">
      <div className="app-state__card">
        <span className="island-badge">섬</span>
        <p>{message}</p>
        {onRetry ? <button className="retry-button" onClick={onRetry} type="button">다시 시도</button> : null}
      </div>
    </main>
  );
}
