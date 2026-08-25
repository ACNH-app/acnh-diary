import { Bug, Fish, Search, Shirt, Sofa, Utensils } from "lucide-react";
import { useCallback, useState } from "react";

import { getCatalog, getCatalogDetail, updateCatalogState, type CatalogDetail, type CatalogItem, type CatalogType } from "../../api/catalog";
import type { AppTab, BottomNavItem } from "../../components/layout/BottomNavigation";
import { BottomNavigation } from "../../components/layout/BottomNavigation";
import { MobileScreen } from "../../components/layout/MobileScreen";
import { SearchField } from "../../components/ui/SearchField";
import { useAsync } from "../../hooks/useAsync";

type CatalogScreenProps = {
  islandId: number;
  navItems: BottomNavItem[];
  currentTab: AppTab;
  onTabChange: (tab: AppTab) => void;
};

const typeLabels: Record<CatalogType, string> = {
  fish: "물고기",
  bugs: "곤충",
  sea: "해산물",
  fossils: "화석",
  items: "아이템",
  recipes: "레시피",
};

export function CatalogScreen({ islandId, navItems, currentTab, onTabChange }: CatalogScreenProps) {
  const [catalogType, setCatalogType] = useState<CatalogType>("fish");
  const [query, setQuery] = useState("");
  const [ownedFilter, setOwnedFilter] = useState<"all" | "owned" | "missing">("all");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [detail, setDetail] = useState<CatalogDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const loadCatalog = useCallback(() => getCatalog(catalogType, islandId, query, ownedFilter === "all" ? undefined : ownedFilter === "owned", sortOrder), [catalogType, islandId, ownedFilter, query, sortOrder]);
  const catalogState = useAsync(loadCatalog);
  const response = catalogState.status === "success" ? catalogState.data : null;
  const ownedCount = response?.items.filter((item) => item.owned).length ?? 0;
  const progress = response && response.total_count > 0 ? Math.round((ownedCount / response.total_count) * 100) : 0;
  const isCreatureGroup = ["fish", "bugs", "sea"].includes(catalogType);

  async function handleToggle(item: CatalogItem, key: "owned" | "donated") {
    try {
      await updateCatalogState(catalogType, item.id, islandId, { [key]: !item[key] });
      catalogState.reload();
    } catch {
      // The error state is shown by the next reload; keep the current row stable.
    }
  }

  async function openDetail(item: CatalogItem) {
    setDetailLoading(true);
    setDetailError("");
    try {
      setDetail(await getCatalogDetail(catalogType, item.id, islandId));
    } catch (cause) {
      setDetailError(cause instanceof Error ? cause.message : "상세 정보를 불러오지 못했어요.");
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <MobileScreen
      action={<button className="round-action" onClick={() => setQuery("")} title="검색 초기화" type="button"><Search aria-hidden="true" size={22} /></button>}
      footer={<BottomNavigation items={navItems} onChange={onTabChange} value={currentTab} />}
      subtitle="섬에서 만난 것들을 차곡차곡 기록해요."
      title="도감"
      tone="yellow"
    >
      {catalogState.status === "loading" ? <div className="screen-state">도감 데이터를 불러오는 중이에요…</div> : null}
      {catalogState.status === "error" ? <div className="screen-state screen-state--error" role="alert">도감 데이터를 불러오지 못했어요.<button className="retry-button" onClick={catalogState.reload} type="button">다시 시도</button></div> : null}

      <section className="collection-card">
        <div>
          <p>{typeLabels[catalogType]} 수집 현황</p>
          <strong>{ownedCount} <span>/ {response?.total_count ?? "—"}개</span></strong>
          <small>현재 검색 결과 기준 {progress}%</small>
        </div>
        <div className="donut-progress">{progress}%<span>달성</span></div>
        <div className="wide-progress"><span style={{ width: `${progress}%` }} /></div>
      </section>

      <SearchField onChange={setQuery} placeholder="도감에서 찾아보기" value={query} />
      <div className="filter-row">
        <select aria-label="수집 상태 필터" onChange={(event) => setOwnedFilter(event.target.value as "all" | "owned" | "missing")} value={ownedFilter}>
          <option value="all">전체 상태</option>
          <option value="owned">보유만</option>
          <option value="missing">미수집만</option>
        </select>
        <select aria-label="정렬 순서" onChange={(event) => setSortOrder(event.target.value as "asc" | "desc")} value={sortOrder}>
          <option value="asc">이름 오름차순</option>
          <option value="desc">이름 내림차순</option>
        </select>
      </div>

      <div className="category-tabs">
        <button className={isCreatureGroup ? "is-active" : ""} onClick={() => setCatalogType("fish")} type="button">생물</button>
        <button className={catalogType === "fossils" ? "is-active" : ""} onClick={() => setCatalogType("fossils")} type="button">화석</button>
        <button className={catalogType === "items" ? "is-active" : ""} onClick={() => setCatalogType("items")} type="button">아이템</button>
        <button className={catalogType === "recipes" ? "is-active" : ""} onClick={() => setCatalogType("recipes")} type="button">레시피</button>
      </div>

      {isCreatureGroup ? (
        <div className="segmented">
          {(["fish", "bugs", "sea"] as CatalogType[]).map((type) => (
            <button className={catalogType === type ? "is-active" : ""} key={type} onClick={() => setCatalogType(type)} type="button">{typeLabels[type]}</button>
          ))}
        </div>
      ) : null}

      <section className="catalog-list-section">
        <div className="section-row"><h2>{typeLabels[catalogType]}</h2><span>{response?.count ?? 0}개</span></div>
        <div className="catalog-list">
          {response?.items.map((item) => (
            <article className={item.owned ? "catalog-row catalog-row--owned" : "catalog-row"} key={item.id}>
              <span className={`catalog-row__icon catalog-row__icon--${isCreatureGroup ? "mint" : "violet"}`}>
                {item.image_url ? <img alt="" className="catalog-row__image" src={item.image_url} /> : catalogType === "bugs" ? <Bug aria-hidden="true" size={22} /> : catalogType === "fish" || catalogType === "sea" ? <Fish aria-hidden="true" size={22} /> : <Sofa aria-hidden="true" size={22} />}
              </span>
              <span><button className="catalog-detail-trigger" onClick={() => openDetail(item)} type="button"><strong>{item.name_ko || item.name_en}</strong><small>{item.category || typeLabels[catalogType]}</small></button></span>
              <div className="catalog-actions">
                <button aria-pressed={item.owned} className={item.owned ? "state-chip is-on" : "state-chip"} onClick={() => handleToggle(item, "owned")} type="button">보유</button>
                <button aria-pressed={item.donated} className={item.donated ? "state-chip is-on" : "state-chip"} onClick={() => handleToggle(item, "donated")} type="button">기증</button>
              </div>
            </article>
          ))}
          {catalogState.status === "success" && response?.items.length === 0 ? <div className="empty-state">검색 결과가 없어요.</div> : null}
        </div>
      </section>

      {detailLoading || detailError || detail ? (
        <div className="detail-overlay" onClick={() => setDetail(null)} role="presentation">
          <section className="detail-panel" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true" aria-label="도감 상세 정보">
            <button className="detail-close" onClick={() => setDetail(null)} type="button">닫기</button>
            {detailLoading ? <div className="screen-state">상세 정보를 불러오는 중이에요…</div> : null}
            {detailError ? <div className="screen-state screen-state--error">{detailError}</div> : null}
            {detail ? (
              <>
                {detail.summary.image_url ? <img alt={`${detail.item.name_ko || detail.item.name_en} 이미지`} className="detail-image" src={detail.summary.image_url} /> : null}
                <h2>{detail.item.name_ko || detail.item.name_en}</h2>
                <p className="detail-subtitle">{detail.summary.category || typeLabels[catalogType]}</p>
                <dl className="detail-fields">
                  {detail.fields.map((field) => <div key={`${field.label}-${field.value}`}><dt>{field.label}</dt><dd>{field.value}</dd></div>)}
                </dl>
                {detail.variations.length > 0 ? <div className="detail-variations"><strong>변형 {detail.variations.length}개</strong><span>{detail.variations.filter((variation) => variation.owned).length}개 보유</span></div> : null}
              </>
            ) : null}
          </section>
        </div>
      ) : null}

      <div className="floating-icons" aria-hidden="true"><Sofa /><Shirt /><Utensils /></div>
    </MobileScreen>
  );
}
