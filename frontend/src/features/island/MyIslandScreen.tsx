import { BriefcaseBusiness, ChevronDown, Menu, UserRound } from "lucide-react";

import type { AppTab } from "../../components/layout/BottomNavigation";
import { BottomNavigation, type BottomNavItem } from "../../components/layout/BottomNavigation";
import { MobileScreen } from "../../components/layout/MobileScreen";
import { Button } from "../../components/ui/Button";
import { Pill } from "../../components/ui/Pill";

type MyIslandScreenProps = {
  navItems: BottomNavItem[];
  currentTab: AppTab;
  islandName: string;
  onTabChange: (tab: AppTab) => void;
  onOpenMenu: () => void;
};

export function MyIslandScreen({ navItems, currentTab, islandName, onTabChange, onOpenMenu }: MyIslandScreenProps) {
  return (
    <MobileScreen
      action={
        <button className="menu-button is-filled" onClick={onOpenMenu} title="섬 관리" type="button">
          <Menu aria-hidden="true" size={22} />
        </button>
      }
      footer={<BottomNavigation items={navItems} onChange={onTabChange} value={currentTab} />}
      subtitle="나의 섬 정보를 한눈에 관리해요."
      title="내 섬"
      tone="green"
    >
      <section className="island-passport">
        <div className="passport-card-header">
          <Pill tone="mint">섬 여권</Pill>
          <Button size="sm" variant="ghost">정보 수정</Button>
        </div>
        <div className="passport-main">
          <span className="passport-icon">
            <BriefcaseBusiness aria-hidden="true" size={30} />
          </span>
          <div>
            <small>나의 섬</small>
            <strong>{islandName}</strong>
          </div>
        </div>
        <dl className="passport-grid">
          <div><dt>섬 이름</dt><dd>{islandName}</dd></div>
          <div><dt>대표 과일</dt><dd>복숭아</dd></div>
          <div><dt>자생 꽃</dt><dd>장미</dd></div>
          <div><dt>반구</dt><dd>북반구</dd></div>
          <div><dt>주민대표</dt><dd>김태민</dd></div>
          <div><dt>생일</dt><dd>8월 19일</dd></div>
        </dl>
      </section>

      <section className="resident-strip">
        <div className="section-row">
          <h2>섬 주민</h2>
          <strong>8명</strong>
        </div>
        <article className="resident-card resident-card--compact">
          <span className="avatar avatar--rose"><UserRound aria-hidden="true" size={28} /></span>
          <span><strong>쭈니</strong><small>느끼함 · 토끼</small></span>
          <span className="avatar avatar--sky"><UserRound aria-hidden="true" size={28} /></span>
          <span><strong>비앙카</strong><small>성숙함 · 늑대</small></span>
          <button title="전체 보기" type="button"><ChevronDown aria-hidden="true" size={18} /></button>
        </article>
      </section>

      <section className="records-section">
        <div className="section-row">
          <h2>나의 기록</h2>
          <span>한 화면에서 확인해요</span>
        </div>
        <div className="record-grid">
          <RecordCard title="수집 현황" meta="전체 128 / 524개" tone="violet" progress="28%" />
          <RecordCard title="박물관 기증" meta="31 / 80개 기증" tone="sky" progress="42%" />
          <RecordCard title="루틴 기록" meta="이번 주 24 / 35 완료" tone="mint" progress="68%" />
          <RecordCard title="즐겨찾기" meta="저장한 항목 12개" tone="sun" progress="34%" />
        </div>
      </section>
    </MobileScreen>
  );
}

function RecordCard({ title, meta, tone, progress }: { title: string; meta: string; tone: string; progress: string }) {
  return (
    <article className={`record-card record-card--${tone}`}>
      <strong>{title}</strong>
      <small>{meta}</small>
      <span className="mini-progress"><span style={{ width: progress }} /></span>
    </article>
  );
}
