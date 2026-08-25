import { Leaf } from "lucide-react";
import { useState, type FormEvent } from "react";

import { createIsland, updateIslandProfile } from "../../api/islands";
import { Button } from "../../components/ui/Button";
import { Pill } from "../../components/ui/Pill";
import type { Island } from "../../api/islands";

const friends = ["북반구", "남반구"];
const fruits = ["사과", "배", "복숭아", "오렌지", "체리"];
const flowers = ["코스모스", "장미", "튤립", "히아신스", "국화", "백합"];

type IslandSetupScreenProps = {
  onCreated?: (island: Island) => void;
};

export function IslandSetupScreen({ onCreated }: IslandSetupScreenProps) {
  const [islandName, setIslandName] = useState("왓섬");
  const [hemisphere, setHemisphere] = useState("north");
  const [fruit, setFruit] = useState("배");
  const [flower, setFlower] = useState("튤립");
  const [nickname, setNickname] = useState("은하");
  const [birthday, setBirthday] = useState("2026-12-08");
  const [status, setStatus] = useState<"idle" | "saving" | "error">("idle");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanName = islandName.trim();
    if (!cleanName || !nickname.trim() || !birthday) {
      setError("섬 이름, 주민대표 이름, 생일을 입력해 주세요.");
      setStatus("error");
      return;
    }

    setStatus("saving");
    setError("");
    try {
      const island = await createIsland(cleanName);
      await updateIslandProfile(island.id, {
        island_name: cleanName,
        nickname: nickname.trim(),
        representative_fruit: fruit,
        representative_flower: flower,
        birthday,
        hemisphere: hemisphere as "north" | "south",
        time_travel_enabled: false,
        game_datetime: "",
      });
      onCreated?.(island);
    } catch (cause) {
      setStatus("error");
      setError(cause instanceof Error ? cause.message : "섬을 등록하지 못했어요.");
    }
  }

  return (
    <main className="setup-page">
      <section className="phone-frame setup-phone" aria-label="섬 등록">
        <div className="mobile-status">
          <span>9:41</span>
          <span>모동숲 다이어리</span>
          <span>100%</span>
        </div>

        <div className="passport-title">PASSPORT</div>

        <form className="setup-card" onSubmit={handleSubmit}>
          <div className="setup-avatar">
            <Leaf aria-hidden="true" size={20} />
            <span>섬 등록</span>
          </div>

          <label className="field">
            <span>섬 이름</span>
            <input aria-label="섬 이름" value={islandName} onChange={(event) => setIslandName(event.target.value)} />
          </label>

          <fieldset className="choice-group">
            <legend>친구</legend>
            <div>
              {friends.map((item, index) => {
                const value = index === 0 ? "north" : "south";
                return (
                <button className={hemisphere === value ? "choice is-selected" : "choice"} key={item} onClick={() => setHemisphere(value)} type="button">
                  {item}
                </button>
                );
              })}
            </div>
          </fieldset>

          <fieldset className="choice-group">
            <legend>대표 과일</legend>
            <div>
              {fruits.map((item) => (
                <button className={fruit === item ? "choice is-selected" : "choice"} key={item} onClick={() => setFruit(item)} type="button">
                  {item}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset className="choice-group">
            <legend>대표 꽃</legend>
            <div>
              {flowers.map((item) => (
                <button className={flower === item ? "choice is-selected" : "choice"} key={item} onClick={() => setFlower(item)} type="button">
                  {item}
                </button>
              ))}
            </div>
          </fieldset>

          <label className="field">
            <span>주민대표 이름</span>
            <input aria-label="주민대표 이름" value={nickname} onChange={(event) => setNickname(event.target.value)} />
          </label>

          <label className="field">
            <span>주민대표 생일</span>
            <input aria-label="주민대표 생일" type="date" value={birthday} onChange={(event) => setBirthday(event.target.value)} />
          </label>

          <div className="setup-footer">
            <span>오늘</span>
            <time>2026.08.19</time>
          </div>

          {error ? <p className="form-error" role="alert">{error}</p> : null}

          <Button className="setup-submit" disabled={status === "saving"} type="submit">
            {status === "saving" ? "등록 중…" : "등록하기"}
          </Button>
        </form>
      </section>

      <aside className="setup-notes">
        <Pill tone="leaf">Island setup</Pill>
        <h1>태블릿에서도 한 손 흐름이 유지되는 등록 화면</h1>
        <p>입력은 세로로 단순하게, 선택지는 큰 칩으로 구성했습니다.</p>
      </aside>
    </main>
  );
}
