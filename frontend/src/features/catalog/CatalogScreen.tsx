import { Bug, Fish, Search, Shirt, Sofa, Utensils } from "lucide-react";

import type { AppTab } from "../../components/layout/BottomNavigation";
import { BottomNavigation, type BottomNavItem } from "../../components/layout/BottomNavigation";
import { MobileScreen } from "../../components/layout/MobileScreen";
import { Pill } from "../../components/ui/Pill";
import { SearchField } from "../../components/ui/SearchField";

type CatalogScreenProps = {
  navItems: BottomNavItem[];
  currentTab: AppTab;
  onTabChange: (tab: AppTab) => void;
};

const rows = [
  { name: "청새치", meta: "바다 · 16:00-09:00", price: "4,000벨", icon: Fish, tone: "mint" },
  { name: "송사리", meta: "연못 · 종일", price: "300벨", icon: Fish, tone: "mint" },
  { name: "풍이", meta: "나무 · 08:00-17:00", price: "160벨", icon: Bug, tone: "violet" },
];

export function CatalogScreen({ navItems, currentTab, onTabChange }: CatalogScreenProps) {
  return (
    <MobileScreen
      action={
        <button className="round-action" title="검색" type="button">
          <Search aria-hidden="true" size={22} />
        </button>
      }
      footer={<BottomNavigation items={navItems} onChange={onTabChange} value={currentTab} />}
      subtitle="섬에서 만난 것들을 차곡차곡 기록해요."
      title="도감"
      tone="yellow"
    >
      <section className="collection-card">
        <div>
          <p>나의 수집 현황</p>
          <strong>128 <span>/ 524개</span></strong>
          <small>전체 수집률 24.4%</small>
        </div>
        <div className="donut-progress">24%<span>달성</span></div>
        <div className="wide-progress">
          <span style={{ width: "39%" }} />
        </div>
      </section>

      <SearchField placeholder="도감에서 찾아보기" />

      <div className="category-tabs">
        <button className="is-active" type="button">생물</button>
        <button type="button">화석</button>
        <button type="button">아이템</button>
        <button type="button">레시피</button>
      </div>

      <section className="catalog-list-section">
        <div className="section-row">
          <h2>생물</h2>
          <span>128 / 236</span>
        </div>
        <div className="segmented">
          <button className="is-active" type="button">전체</button>
          <button type="button">물고기</button>
          <button type="button">곤충</button>
          <button type="button">해산물</button>
        </div>
        <div className="catalog-list">
          {rows.map((row) => {
            const Icon = row.icon;
            return (
              <article className="catalog-row" key={row.name}>
                <span className={`catalog-row__icon catalog-row__icon--${row.tone}`}>
                  <Icon aria-hidden="true" size={22} />
                </span>
                <span>
                  <strong>{row.name}</strong>
                  <small>{row.meta}</small>
                </span>
                <Pill tone={row.tone === "violet" ? "violet" : "mint"}>{row.price}</Pill>
              </article>
            );
          })}
        </div>
      </section>

      <div className="floating-icons" aria-hidden="true">
        <Sofa />
        <Shirt />
        <Utensils />
      </div>
    </MobileScreen>
  );
}
