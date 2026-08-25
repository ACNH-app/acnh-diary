import { ChevronRight, Plus, Trash2, X } from "lucide-react";
import { useCallback, useEffect } from "react";

import { getIslandProfile } from "../../api/islands";
import { Button } from "../../components/ui/Button";
import { Pill } from "../../components/ui/Pill";
import type { Island } from "../../api/islands";
import { useAsync } from "../../hooks/useAsync";

type IslandSidebarProps = {
  open: boolean;
  activeIslandId: number;
  islands: Island[];
  islandName: string;
  onClose: () => void;
  onSelectIsland: (islandId: number) => void;
  onAddIsland: () => void;
  onDeleteIsland: () => void;
};

export function IslandSidebar({
  open,
  activeIslandId,
  islands,
  islandName,
  onClose,
  onSelectIsland,
  onAddIsland,
  onDeleteIsland,
}: IslandSidebarProps) {
  const loadProfile = useCallback(() => getIslandProfile(activeIslandId), [activeIslandId]);
  const profileState = useAsync(loadProfile);
  const profile = profileState.status === "success" ? profileState.data : null;

  useEffect(() => {
    function handleProfileUpdated(event: Event) {
      const islandEvent = event as CustomEvent<{ islandId?: number }>;
      if (islandEvent.detail?.islandId === activeIslandId) profileState.reload();
    }
    window.addEventListener("acnh-diary.profile-updated", handleProfileUpdated);
    return () => window.removeEventListener("acnh-diary.profile-updated", handleProfileUpdated);
  }, [activeIslandId]);

  return (
    <aside className={open ? "island-sidebar is-open" : "island-sidebar"} aria-label="섬 정보">
      <div className="sidebar-scrim" onClick={onClose} />
      <div className="island-panel">
        <button className="drawer-close" onClick={onClose} title="닫기" type="button">
          <X aria-hidden="true" size={20} />
        </button>

        <label className="current-island">
          <span className="island-badge">섬</span>
          <span>
            <small>현재 섬</small>
            <strong>{islandName}</strong>
          </span>
          <ChevronRight aria-hidden="true" size={20} />
          <select aria-label="활성 섬 선택" value={activeIslandId} onChange={(event) => onSelectIsland(Number(event.target.value))}>
            {islands.map((island) => <option key={island.id} value={island.id}>{island.name}</option>)}
          </select>
        </label>

        <section className="island-info-card">
          <h2>섬 정보</h2>
          <div className="profile-card">
            <small>섬 이름</small>
            <strong>{islandName}</strong>
            <div className="profile-divider" />
            <dl>
              <div>
                <dt>친구</dt>
                <dd>
                  <Pill tone="mint">{profile?.hemisphere === "south" ? "남반구" : "북반구"}</Pill>
                </dd>
              </div>
              <div>
                <dt>대표 과일</dt>
                <dd>
                  <Pill tone="sun">{profile?.representative_fruit || "—"}</Pill>
                </dd>
              </div>
              <div>
                <dt>자생 꽃</dt>
                <dd>
                  <Pill tone="violet">{profile?.representative_flower || "—"}</Pill>
                </dd>
              </div>
              <div>
                <dt>주민대표</dt>
                <dd>{profile?.nickname || "—"}</dd>
              </div>
              <div>
                <dt>생일</dt>
                <dd>{profile?.birthday || "—"}</dd>
              </div>
            </dl>
            <Button className="profile-edit" variant="secondary">
              섬 정보 수정
            </Button>
          </div>
        </section>

        <section className="island-actions">
          <h2>섬 관리</h2>
          <button className="action-row action-row--add" onClick={onAddIsland} type="button">
            <Plus aria-hidden="true" size={22} />
            <span>새 섬 추가</span>
            <ChevronRight aria-hidden="true" size={20} />
          </button>
          <button className="action-row action-row--delete" disabled={islands.length <= 1} onClick={onDeleteIsland} type="button">
            <Trash2 aria-hidden="true" size={22} />
            <span>현재 섬 삭제</span>
            <ChevronRight aria-hidden="true" size={20} />
          </button>
        </section>

        <p className="drawer-hint">바깥을 누르면 메뉴가 닫혀요</p>
      </div>
    </aside>
  );
}
