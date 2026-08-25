export type NpcOption = {
  name: string;
  night?: boolean;
  icon_url: string;
};

const npcIcon = "/static/icons/nav-more-bell.svg";

export const npcOptions: NpcOption[] = [
  { name: "여욱", icon_url: npcIcon },
  { name: "사하라", icon_url: npcIcon },
  { name: "패트릭", icon_url: npcIcon },
  { name: "저스틴", icon_url: npcIcon },
  { name: "레온", icon_url: npcIcon },
  { name: "여울", icon_url: npcIcon },
  { name: "고숙이", icon_url: npcIcon },
  { name: "무파니", icon_url: npcIcon },
  { name: "죠니", icon_url: npcIcon },
  { name: "해적 죠니", icon_url: npcIcon },
  { name: "K.K.", icon_url: npcIcon },
  { name: "부옥", night: true, icon_url: npcIcon },
  { name: "깨빈", night: true, icon_url: npcIcon },
  { name: "파니엘", icon_url: npcIcon },
  { name: "리포", icon_url: npcIcon },
  { name: "너굴", icon_url: npcIcon },
  { name: "콩돌", icon_url: npcIcon },
  { name: "밤돌", icon_url: npcIcon },
  { name: "마스터", icon_url: npcIcon },
  { name: "베르리나", icon_url: npcIcon },
];
