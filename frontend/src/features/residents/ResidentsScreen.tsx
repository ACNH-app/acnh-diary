import { Search, UserRound } from "lucide-react";

import type { AppTab } from "../../components/layout/BottomNavigation";
import { BottomNavigation, type BottomNavItem } from "../../components/layout/BottomNavigation";
import { MobileScreen } from "../../components/layout/MobileScreen";
import { Pill } from "../../components/ui/Pill";
import { SearchField } from "../../components/ui/SearchField";

type ResidentsScreenProps = {
  navItems: BottomNavItem[];
  currentTab: AppTab;
  onTabChange: (tab: AppTab) => void;
};

const residents = [
  ["쭈니", "느끼함 · 토끼", "rose"],
  ["비앙카", "성숙함 · 늑대", "sky"],
  ["나탈리", "성숙함 · 사슴", "violet"],
];

export function ResidentsScreen({ navItems, currentTab, onTabChange }: ResidentsScreenProps) {
  return (
    <MobileScreen
      action={<button className="round-action" title="검색" type="button"><Search size={22} /></button>}
      footer={<BottomNavigation items={navItems} onChange={onTabChange} value={currentTab} />}
      subtitle="보고 싶은 주민만 골라서 관리해요."
      title="주민"
      tone="rose"
    >
      <section className="resident-summary">
        <div>
          <p>내 주민 기록</p>
          <strong>8명 <span>섬에 살고 있어요</span></strong>
        </div>
        <Pill tone="rose">위시 6명</Pill>
      </section>
      <SearchField placeholder="주민 이름, 성격, 종 검색" />
      <div className="category-tabs">
        <button className="is-active" type="button">위시</button>
        <button type="button">캠핑장 방문</button>
        <button type="button">섬 주민</button>
        <button type="button">이사간 주민</button>
      </div>
      <section className="resident-list-section">
        <div className="section-row">
          <h2>위시 주민</h2>
          <strong>6명</strong>
        </div>
        <div className="resident-list">
          {residents.map(([name, meta, tone]) => (
            <article className="resident-row" key={name}>
              <span className={`avatar avatar--${tone}`}><UserRound aria-hidden="true" size={30} /></span>
              <span><strong>{name}</strong><small>{meta}</small></span>
              <Pill tone="rose">위시 등록</Pill>
            </article>
          ))}
        </div>
      </section>
    </MobileScreen>
  );
}
