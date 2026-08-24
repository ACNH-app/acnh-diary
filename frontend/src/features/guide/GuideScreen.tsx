import { ChevronDown, Search } from "lucide-react";

import type { AppTab } from "../../components/layout/BottomNavigation";
import { BottomNavigation, type BottomNavItem } from "../../components/layout/BottomNavigation";
import { MobileScreen } from "../../components/layout/MobileScreen";
import { SearchField } from "../../components/ui/SearchField";

type GuideScreenProps = {
  navItems: BottomNavItem[];
  currentTab: AppTab;
  onTabChange: (tab: AppTab) => void;
};

const guideCards = [
  ["시작하기", "처음 섬에 온 날부터", "sun"],
  ["섬 생활", "매일 하면 좋은 일들", "mint"],
  ["주민", "이사와 친밀도 관리", "rose"],
  ["돈벌이", "벨을 모으는 다양한 방법", "violet"],
  ["꽃 교배", "희귀한 꽃을 피우는 법", "green"],
  ["생물 채집", "물고기와 곤충 잡기", "sky"],
  ["NPC / 방문객", "요일별 방문객 정보", "sun"],
  ["이벤트", "시즌별 행사와 보상", "violet"],
  ["해피홈 파라다이스", "별장 꾸미기 기록", "rose"],
  ["꿀팁", "알아두면 편한 정보", "neutral"],
];

export function GuideScreen({ navItems, currentTab, onTabChange }: GuideScreenProps) {
  return (
    <MobileScreen
      action={
        <button className="round-action" title="검색" type="button">
          <Search aria-hidden="true" size={22} />
        </button>
      }
      footer={<BottomNavigation items={navItems} onChange={onTabChange} value={currentTab} />}
      subtitle="섬 생활에 필요한 정보만 골라서 찾아봐요."
      title="공략"
      tone="blue"
    >
      <SearchField placeholder="공략 검색" />
      <section className="guide-section">
        <h2>주제별 공략</h2>
        <div className="guide-grid">
          {guideCards.map(([title, body, tone]) => (
            <button className={`guide-card guide-card--${tone}`} key={title} type="button">
              <span>
                <strong>{title}</strong>
                <small>{body}</small>
              </span>
              <ChevronDown aria-hidden="true" size={18} />
            </button>
          ))}
        </div>
      </section>
    </MobileScreen>
  );
}
