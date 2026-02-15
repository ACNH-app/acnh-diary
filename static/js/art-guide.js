import {
  artGuideBackdrop,
  artGuideCloseBtn,
  artGuideList,
  artGuideModal,
  artGuideStatus,
  catalogArtGuideBtn,
} from "./dom.js";

function closeArtGuide() {
  if (!artGuideModal) return;
  artGuideModal.classList.add("hidden");
  artGuideModal.setAttribute("aria-hidden", "true");
}

function openArtGuide() {
  if (!artGuideModal) return;
  artGuideModal.classList.remove("hidden");
  artGuideModal.setAttribute("aria-hidden", "false");
}

function renderGuideRows(items) {
  if (!artGuideList) return;
  artGuideList.innerHTML = "";
  items.forEach((row) => {
    const card = document.createElement("article");
    card.className = "art-guide-card";

    const title = document.createElement("h3");
    const name = row.name_ko || row.name_en || "-";
    title.textContent = `${name} (${row.authenticity_ko || "-"})`;
    card.appendChild(title);

    const body = document.createElement("div");
    body.className = "art-guide-body";

    const real = document.createElement("div");
    real.className = "art-guide-col";
    const realTitle = document.createElement("p");
    realTitle.className = "art-guide-label";
    realTitle.textContent = "진품";
    const realImg = document.createElement("img");
    realImg.className = "art-guide-img";
    realImg.src = row.real_image_url || "/static/no-image.svg";
    realImg.alt = `${name} 진품`;
    realImg.onerror = () => {
      realImg.src = "/static/no-image.svg";
    };
    const realDesc = document.createElement("p");
    realDesc.className = "art-guide-desc";
    realDesc.textContent = row.real_description || "설명 없음";
    real.appendChild(realTitle);
    real.appendChild(realImg);
    real.appendChild(realDesc);

    const fake = document.createElement("div");
    fake.className = "art-guide-col";
    const fakeTitle = document.createElement("p");
    fakeTitle.className = "art-guide-label";
    fakeTitle.textContent = "가품";
    const fakeImg = document.createElement("img");
    fakeImg.className = "art-guide-img";
    fakeImg.src = row.fake_image_url || "/static/no-image.svg";
    fakeImg.alt = `${name} 가품`;
    fakeImg.onerror = () => {
      fakeImg.src = "/static/no-image.svg";
    };
    const fakeDesc = document.createElement("p");
    fakeDesc.className = "art-guide-desc";
    fakeDesc.textContent =
      row.authenticity === "genuine_only"
        ? "가품이 없는 미술품입니다."
        : row.fake_description || "설명 없음";
    fake.appendChild(fakeTitle);
    fake.appendChild(fakeImg);
    fake.appendChild(fakeDesc);

    body.appendChild(real);
    body.appendChild(fake);
    card.appendChild(body);
    artGuideList.appendChild(card);
  });
}

export function bindArtGuideEvents({ getJSON }) {
  if (!catalogArtGuideBtn) return;
  let loaded = false;
  let cachedItems = [];

  const load = async () => {
    if (loaded) return;
    artGuideStatus.textContent = "로딩 중...";
    const data = await getJSON("/api/catalog/art/guide");
    cachedItems = Array.isArray(data.items) ? data.items : [];
    renderGuideRows(cachedItems);
    artGuideStatus.textContent = `${cachedItems.length}개`;
    loaded = true;
  };

  catalogArtGuideBtn.addEventListener("click", async () => {
    openArtGuide();
    try {
      await load();
    } catch (err) {
      console.error(err);
      artGuideStatus.textContent = "미술품 데이터를 불러오지 못했습니다.";
    }
  });

  if (artGuideCloseBtn) artGuideCloseBtn.addEventListener("click", closeArtGuide);
  if (artGuideBackdrop) artGuideBackdrop.addEventListener("click", closeArtGuide);
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (!artGuideModal || artGuideModal.classList.contains("hidden")) return;
    closeArtGuide();
  });
}
