import { BriefcaseBusiness, ChevronDown, Menu, UserRound } from "lucide-react";
import { useCallback, useEffect, useState, type FormEvent } from "react";

import { getIslandProfile, updateIslandProfile, type IslandProfileInput } from "../../api/islands";
import type { AppTab } from "../../components/layout/BottomNavigation";
import { BottomNavigation, type BottomNavItem } from "../../components/layout/BottomNavigation";
import { MobileScreen } from "../../components/layout/MobileScreen";
import { Button } from "../../components/ui/Button";
import { Pill } from "../../components/ui/Pill";
import { useAsync } from "../../hooks/useAsync";

type MyIslandScreenProps = {
  islandId: number;
  navItems: BottomNavItem[];
  currentTab: AppTab;
  islandName: string;
  onTabChange: (tab: AppTab) => void;
  onOpenMenu: () => void;
};

export function MyIslandScreen({ navItems, currentTab, islandId, islandName, onTabChange, onOpenMenu }: MyIslandScreenProps) {
  const loadProfile = useCallback(() => getIslandProfile(islandId), [islandId]);
  const profileState = useAsync(loadProfile);
  const profile = profileState.status === "success" ? profileState.data : null;
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState<IslandProfileInput>({
    island_name: islandName,
    nickname: "",
    representative_fruit: "",
    representative_flower: "",
    birthday: "",
    hemisphere: "north",
    time_travel_enabled: false,
    game_datetime: "",
  });

  useEffect(() => {
    if (profile) {
      const { island_id: _islandId, ...profileDraft } = profile;
      setDraft(profileDraft);
    }
  }, [profile]);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    try {
      await updateIslandProfile(islandId, draft);
      profileState.reload();
      window.dispatchEvent(new CustomEvent("acnh-diary.profile-updated", { detail: { islandId } }));
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

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
      {profileState.status === "loading" ? <div className="screen-state">섬 프로필을 불러오는 중이에요…</div> : null}
      {profileState.status === "error" ? <div className="screen-state screen-state--error" role="alert">섬 프로필을 불러오지 못했어요.<button className="retry-button" onClick={profileState.reload} type="button">다시 시도</button></div> : null}
      <section className="island-passport">
        <div className="passport-card-header">
          <Pill tone="mint">섬 여권</Pill>
          <Button onClick={() => setEditing((value) => !value)} size="sm" variant="ghost">{editing ? "수정 닫기" : "정보 수정"}</Button>
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
          <div><dt>대표 과일</dt><dd>{profile?.representative_fruit || "—"}</dd></div>
          <div><dt>자생 꽃</dt><dd>{profile?.representative_flower || "—"}</dd></div>
          <div><dt>반구</dt><dd>{profile?.hemisphere === "south" ? "남반구" : "북반구"}</dd></div>
          <div><dt>주민대표</dt><dd>{profile?.nickname || "—"}</dd></div>
          <div><dt>생일</dt><dd>{profile?.birthday || "—"}</dd></div>
        </dl>
      </section>

      {editing ? (
        <form className="profile-edit-form" onSubmit={handleSave}>
          <label className="field"><span>섬 이름</span><input value={draft.island_name} onChange={(event) => setDraft({ ...draft, island_name: event.target.value })} /></label>
          <label className="field"><span>주민대표</span><input value={draft.nickname} onChange={(event) => setDraft({ ...draft, nickname: event.target.value })} /></label>
          <label className="field"><span>생일</span><input type="date" value={draft.birthday.length === 5 ? `2026-${draft.birthday}` : draft.birthday} onChange={(event) => setDraft({ ...draft, birthday: event.target.value })} /></label>
          <label className="field field--checkbox"><span>게임 날짜 직접 사용</span><input checked={draft.time_travel_enabled} onChange={(event) => setDraft({ ...draft, time_travel_enabled: event.target.checked })} type="checkbox" /></label>
          {draft.time_travel_enabled ? <label className="field"><span>게임 날짜/시간</span><input type="datetime-local" value={draft.game_datetime.slice(0, 16)} onChange={(event) => setDraft({ ...draft, game_datetime: event.target.value })} /></label> : null}
          <Button disabled={saving} type="submit">{saving ? "저장 중…" : "저장하기"}</Button>
        </form>
      ) : null}

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
