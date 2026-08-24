import { ChevronRight, Plus, Trash2, X } from "lucide-react";

import { Button } from "../../components/ui/Button";
import { Pill } from "../../components/ui/Pill";

type IslandSidebarProps = {
  open: boolean;
  islandName: string;
  onClose: () => void;
};

export function IslandSidebar({ open, islandName, onClose }: IslandSidebarProps) {
  return (
    <aside className={open ? "island-sidebar is-open" : "island-sidebar"} aria-label="섬 정보">
      <div className="sidebar-scrim" onClick={onClose} />
      <div className="island-panel">
        <button className="drawer-close" onClick={onClose} title="닫기" type="button">
          <X aria-hidden="true" size={20} />
        </button>

        <button className="current-island" type="button">
          <span className="island-badge">섬</span>
          <span>
            <small>현재 섬</small>
            <strong>{islandName}</strong>
          </span>
          <ChevronRight aria-hidden="true" size={20} />
        </button>

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
                  <Pill tone="mint">북반구</Pill>
                </dd>
              </div>
              <div>
                <dt>대표 과일</dt>
                <dd>
                  <Pill tone="sun">복숭아</Pill>
                </dd>
              </div>
              <div>
                <dt>자생 꽃</dt>
                <dd>
                  <Pill tone="violet">코스모스</Pill>
                </dd>
              </div>
              <div>
                <dt>주민대표</dt>
                <dd>은하</dd>
              </div>
              <div>
                <dt>생일</dt>
                <dd>12월 8일</dd>
              </div>
            </dl>
            <Button className="profile-edit" variant="secondary">
              섬 정보 수정
            </Button>
          </div>
        </section>

        <section className="island-actions">
          <h2>섬 관리</h2>
          <button className="action-row action-row--add" type="button">
            <Plus aria-hidden="true" size={22} />
            <span>새 섬 추가</span>
            <ChevronRight aria-hidden="true" size={20} />
          </button>
          <button className="action-row action-row--delete" type="button">
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
