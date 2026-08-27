import {
  encyclopediaMonthLabel,
  encyclopediaShortcutButtons,
  monthlyTargetsCard,
  monthlyTargetsList,
  monthlyTargetsSummary,
} from "./dom.js";

const typeLabels = {
  bugs: "곤충",
  fish: "물고기",
  sea: "해산물",
};

function navigateMode(mode) {
  window.dispatchEvent(new CustomEvent("acnh:navigate-mode", { detail: { mode } }));
}

function reasonText(item) {
  const reasons = Array.isArray(item?.reasons) ? item.reasons.filter(Boolean) : [];
  return reasons.length ? reasons.join(" · ") : "이번 달 출현";
}

function renderTargetItem(item) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "monthly-target-item";
  button.dataset.mode = String(item?.catalog_type || "");

  const image = document.createElement("img");
  image.loading = "lazy";
  image.decoding = "async";
  image.alt = "";
  image.src = item?.icon_url || "/static/no-image.svg";
  image.addEventListener("error", () => {
    image.src = "/static/no-image.svg";
  });

  const text = document.createElement("span");
  const title = document.createElement("strong");
  title.textContent = item?.name_ko || item?.name_en || "-";
  const meta = document.createElement("small");
  const typeLabel = typeLabels[item?.catalog_type] || "생물";
  meta.textContent = `${typeLabel} · ${reasonText(item)}`;
  text.append(title, meta);

  button.append(image, text);
  button.addEventListener("click", () => {
    const mode = String(item?.catalog_type || "");
    if (mode) navigateMode(mode);
  });
  return button;
}

export async function loadEncyclopediaOverview(getMonthlyTargets) {
  if (!monthlyTargetsSummary || !monthlyTargetsList) return;
  monthlyTargetsSummary.textContent = "이번 달 출현 생물을 확인하는 중이에요.";
  monthlyTargetsList.innerHTML = "";

  try {
    const payload = await getMonthlyTargets();
    const month = Number(payload?.month || 0);
    const count = Number(payload?.count || 0);
    const items = Array.isArray(payload?.items) ? payload.items : [];
    const newCounts = payload?.new_counts_by_type || {};
    const newTotal = Object.values(newCounts).reduce((sum, value) => sum + Number(value || 0), 0);

    if (encyclopediaMonthLabel) {
      encyclopediaMonthLabel.textContent = month ? `${month}월` : "-";
    }

    monthlyTargetsSummary.textContent = count
      ? `미채집/미기증 또는 이번 달부터 출현하는 생물 ${count}종`
      : "이번 달 기준으로 새로 챙길 생물은 없어요.";

    if (monthlyTargetsCard) {
      monthlyTargetsCard.dataset.mode = items[0]?.catalog_type || "fish";
      monthlyTargetsCard.classList.toggle("is-empty", count === 0);
    }

    if (items.length) {
      const fragment = document.createDocumentFragment();
      items.slice(0, 6).forEach((item) => fragment.appendChild(renderTargetItem(item)));
      monthlyTargetsList.appendChild(fragment);
    } else {
      const empty = document.createElement("p");
      empty.className = "monthly-target-empty";
      empty.textContent = "채집과 기증 상태가 모두 깔끔해요.";
      monthlyTargetsList.appendChild(empty);
    }

    if (newTotal > 0) {
      monthlyTargetsSummary.textContent += ` · 이번 달 시작 ${newTotal}종`;
    }
  } catch (err) {
    console.error(err);
    monthlyTargetsSummary.textContent = "이번 달 생물 정보를 불러오지 못했어요.";
    const empty = document.createElement("p");
    empty.className = "monthly-target-empty";
    empty.textContent = "잠시 후 다시 확인해 주세요.";
    monthlyTargetsList.replaceChildren(empty);
  }
}

export function bindEncyclopediaEvents() {
  monthlyTargetsCard?.addEventListener("click", () => {
    const mode = String(monthlyTargetsCard.dataset.mode || "fish");
    navigateMode(mode);
  });
  encyclopediaShortcutButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const mode = String(button.dataset.mode || "");
      if (mode) navigateMode(mode);
    });
  });
}
