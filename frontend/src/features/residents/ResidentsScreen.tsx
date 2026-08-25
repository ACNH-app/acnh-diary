import { Search, UserRound } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { getVillagerMeta, getVillagers, updateVillagerState, type Villager } from "../../api/villagers";
import type { AppTab, BottomNavItem } from "../../components/layout/BottomNavigation";
import { BottomNavigation } from "../../components/layout/BottomNavigation";
import { MobileScreen } from "../../components/layout/MobileScreen";
import { Pill } from "../../components/ui/Pill";
import { SearchField } from "../../components/ui/SearchField";
import { useAsync } from "../../hooks/useAsync";

type ResidentsScreenProps = {
  islandId: number;
  navItems: BottomNavItem[];
  currentTab: AppTab;
  onTabChange: (tab: AppTab) => void;
};

type ResidentView = "liked" | "camping" | "island" | "former";

export function ResidentsScreen({ islandId, navItems, currentTab, onTabChange }: ResidentsScreenProps) {
  const [view, setView] = useState<ResidentView>("liked");
  const [query, setQuery] = useState("");
  const [personality, setPersonality] = useState("");
  const [species, setSpecies] = useState("");
  const [subtype, setSubtype] = useState("");
  const [selectedVillager, setSelectedVillager] = useState<Villager | null>(null);
  const [photoOwners, setPhotoOwners] = useState<Set<string>>(() => loadPhotoOwners(islandId));
  const loadVillagers = useCallback(() => getVillagers(islandId, { q: query, personality, species, subtype }), [islandId, personality, query, species, subtype]);
  const villagersState = useAsync(loadVillagers);
  const metaState = useAsync(getVillagerMeta);
  const allVillagers = villagersState.status === "success" ? villagersState.data.items : [];
  const villagers = allVillagers.filter((villager) => {
    if (view === "liked") return villager.liked;
    if (view === "camping") return villager.camping_visited;
    if (view === "island") return villager.on_island;
    return villager.former_resident;
  });
  const islandCount = allVillagers.filter((villager) => villager.on_island).length;
  const likedCount = allVillagers.filter((villager) => villager.liked).length;

  useEffect(() => {
    setPhotoOwners(loadPhotoOwners(islandId));
  }, [islandId]);

  async function toggleState(villager: Villager, key: "liked" | "on_island" | "camping_visited" | "former_resident") {
    try {
      await updateVillagerState(islandId, villager.id, { [key]: !villager[key] });
      setSelectedVillager((current) => current?.id === villager.id ? { ...current, [key]: !villager[key] } : current);
      villagersState.reload();
    } catch {
      // The list remains unchanged and can be retried from the row controls.
    }
  }

  function togglePhoto(villager: Villager) {
    const next = new Set(photoOwners);
    if (next.has(villager.id)) next.delete(villager.id);
    else next.add(villager.id);
    setPhotoOwners(next);
    savePhotoOwners(islandId, next);
  }

  return (
    <MobileScreen
      action={<button className="round-action" onClick={() => setQuery("")} title="검색 초기화" type="button"><Search aria-hidden="true" size={22} /></button>}
      footer={<BottomNavigation items={navItems} onChange={onTabChange} value={currentTab} />}
      subtitle="보고 싶은 주민만 골라서 관리해요."
      title="주민"
      tone="rose"
    >
      {villagersState.status === "loading" ? <div className="screen-state">주민 목록을 불러오는 중이에요…</div> : null}
      {villagersState.status === "error" ? <div className="screen-state screen-state--error" role="alert">주민 목록을 불러오지 못했어요.<button className="retry-button" onClick={villagersState.reload} type="button">다시 시도</button></div> : null}

      <section className="resident-summary">
        <div><p>내 주민 기록</p><strong>{islandCount}명 <span>섬에 살고 있어요</span></strong></div>
        <Pill tone="rose">위시 {likedCount}명</Pill>
      </section>
      <SearchField onChange={setQuery} placeholder="주민 이름, 성격, 종 검색" value={query} />
      <div className="filter-row">
        <select aria-label="성격 필터" onChange={(event) => setPersonality(event.target.value)} value={personality}>
          <option value="">모든 성격</option>
          {metaState.status === "success" ? metaState.data.personalities.map((item) => <option key={item.en} value={item.en}>{item.ko}</option>) : null}
        </select>
        <select aria-label="종족 필터" onChange={(event) => setSpecies(event.target.value)} value={species}>
          <option value="">모든 종</option>
          {metaState.status === "success" ? metaState.data.species.map((item) => <option key={item.en} value={item.en}>{item.ko}</option>) : null}
        </select>
        <select aria-label="서브타입 필터" onChange={(event) => setSubtype(event.target.value)} value={subtype}>
          <option value="">모든 서브타입</option>
          {metaState.status === "success" ? metaState.data.subtypes?.map((item) => <option key={item.en} value={item.en}>{item.ko}</option>) : null}
        </select>
      </div>
      <div className="category-tabs">
        <button className={view === "liked" ? "is-active" : ""} onClick={() => setView("liked")} type="button">위시</button>
        <button className={view === "camping" ? "is-active" : ""} onClick={() => setView("camping")} type="button">캠핑장 방문</button>
        <button className={view === "island" ? "is-active" : ""} onClick={() => setView("island")} type="button">섬 주민</button>
        <button className={view === "former" ? "is-active" : ""} onClick={() => setView("former")} type="button">이사간 주민</button>
      </div>

      <section className="resident-list-section">
        <div className="section-row"><h2>{viewLabel(view)}</h2><strong>{villagers.length}명</strong></div>
        <div className="resident-list">
          {villagers.map((villager) => (
            <article className="resident-row resident-row--interactive" key={villager.id}>
              <span className="avatar avatar--rose">{villager.image_uri || villager.icon_uri ? <img alt="" className="resident-image" src={villager.image_uri || villager.icon_uri} /> : <UserRound aria-hidden="true" size={30} />}</span>
              <span><button className="resident-detail-trigger" onClick={() => setSelectedVillager(villager)} type="button"><strong>{villager.name_ko || villager.name_en}</strong><small>{villager.personality} · {villager.species}</small></button></span>
              <div className="resident-actions">
                <button className={villager.liked ? "state-chip is-on" : "state-chip"} onClick={() => toggleState(villager, "liked")} type="button">위시</button>
                <button className={villager.on_island ? "state-chip is-on" : "state-chip"} onClick={() => toggleState(villager, "on_island")} type="button">섬</button>
                <button className={photoOwners.has(villager.id) ? "state-chip is-on" : "state-chip"} onClick={() => togglePhoto(villager)} type="button">사진</button>
              </div>
            </article>
          ))}
          {villagersState.status === "success" && villagers.length === 0 ? <div className="empty-state">이 조건에 맞는 주민이 없어요.</div> : null}
        </div>
      </section>

      {selectedVillager ? (
        <div className="detail-overlay" onClick={() => setSelectedVillager(null)} role="presentation">
          <section className="detail-panel" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true" aria-label="주민 상세 정보">
            <button className="detail-close" onClick={() => setSelectedVillager(null)} type="button">닫기</button>
            {selectedVillager.image_uri || selectedVillager.icon_uri ? <img alt={`${selectedVillager.name_ko || selectedVillager.name_en} 이미지`} className="resident-detail-image" src={selectedVillager.image_uri || selectedVillager.icon_uri} /> : null}
            <h2>{selectedVillager.name_ko || selectedVillager.name_en}</h2>
            <p className="detail-subtitle">{selectedVillager.personality} · {selectedVillager.species}</p>
            <div className="resident-detail-states">
              <button className={selectedVillager.liked ? "state-chip is-on" : "state-chip"} onClick={() => toggleState(selectedVillager, "liked")} type="button">위시 {selectedVillager.liked ? "등록됨" : "등록"}</button>
              <button className={selectedVillager.on_island ? "state-chip is-on" : "state-chip"} onClick={() => toggleState(selectedVillager, "on_island")} type="button">섬 주민 {selectedVillager.on_island ? "등록됨" : "등록"}</button>
              <button className={selectedVillager.camping_visited ? "state-chip is-on" : "state-chip"} onClick={() => toggleState(selectedVillager, "camping_visited")} type="button">캠핑 방문 {selectedVillager.camping_visited ? "기록됨" : "기록"}</button>
              <button className={selectedVillager.former_resident ? "state-chip is-on" : "state-chip"} onClick={() => toggleState(selectedVillager, "former_resident")} type="button">과거 주민 {selectedVillager.former_resident ? "기록됨" : "기록"}</button>
              <button className={photoOwners.has(selectedVillager.id) ? "state-chip is-on" : "state-chip"} onClick={() => togglePhoto(selectedVillager)} type="button">사진 {photoOwners.has(selectedVillager.id) ? "보유" : "미보유"}</button>
            </div>
          </section>
        </div>
      ) : null}
    </MobileScreen>
  );
}

function photoStorageKey(islandId: number) {
  return `acnh-diary.villager-photos.${islandId}`;
}

function loadPhotoOwners(islandId: number) {
  try {
    const raw = window.localStorage.getItem(photoStorageKey(islandId));
    const parsed = raw ? JSON.parse(raw) : [];
    return new Set(Array.isArray(parsed) ? parsed.map(String) : []);
  } catch {
    return new Set<string>();
  }
}

function savePhotoOwners(islandId: number, owners: Set<string>) {
  window.localStorage.setItem(photoStorageKey(islandId), JSON.stringify([...owners]));
}

function viewLabel(view: ResidentView) {
  return { liked: "위시 주민", camping: "캠핑장 방문", island: "섬 주민", former: "이사간 주민" }[view];
}
