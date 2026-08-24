import { Leaf } from "lucide-react";

import { Button } from "../../components/ui/Button";
import { Pill } from "../../components/ui/Pill";

const friends = ["쑥보구", "남반구"];
const fruits = ["사과", "배", "복숭아", "오렌지", "체리"];
const flowers = ["코스모스", "장미", "튤립", "히아신스", "국화", "백합"];

export function IslandSetupScreen() {
  return (
    <main className="setup-page">
      <section className="phone-frame setup-phone" aria-label="섬 등록">
        <div className="mobile-status">
          <span>9:41</span>
          <span>모동숲 다이어리</span>
          <span>100%</span>
        </div>

        <div className="passport-title">PASSPORT</div>

        <form className="setup-card">
          <div className="setup-avatar">
            <Leaf aria-hidden="true" size={20} />
            <span>섬 등록</span>
          </div>

          <label className="field">
            <span>섬 이름</span>
            <input defaultValue="왓섬" aria-label="섬 이름" />
          </label>

          <fieldset className="choice-group">
            <legend>친구</legend>
            <div>
              {friends.map((item, index) => (
                <button className={index === 0 ? "choice is-selected" : "choice"} key={item} type="button">
                  {item}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset className="choice-group">
            <legend>대표 과일</legend>
            <div>
              {fruits.map((item, index) => (
                <button className={index === 1 ? "choice is-selected" : "choice"} key={item} type="button">
                  {item}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset className="choice-group">
            <legend>대표 꽃</legend>
            <div>
              {flowers.map((item, index) => (
                <button className={index === 2 ? "choice is-selected" : "choice"} key={item} type="button">
                  {item}
                </button>
              ))}
            </div>
          </fieldset>

          <label className="field">
            <span>주민대표 이름</span>
            <input defaultValue="은하" aria-label="주민대표 이름" />
          </label>

          <label className="field">
            <span>주민대표 생일</span>
            <input defaultValue="2026-12-08" aria-label="주민대표 생일" />
          </label>

          <div className="setup-footer">
            <span>오늘</span>
            <time>2026.08.19</time>
          </div>

          <Button className="setup-submit" type="submit">
            등록하기
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
