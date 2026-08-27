# Figma 가져오기

SVG 파일을 Figma 캔버스에 드래그하거나 `File > Place image`로 선택합니다.

- `residents-list.svg`: 주민 목록 화면
- `resident-detail.svg`: 주민 상세 스크롤 화면
- `encyclopedia-home.svg`: 도감 홈 화면
- `encyclopedia-bugs.svg`: 곤충 도감 목록 화면
- `encyclopedia-bug-detail.svg`: 곤충 상세 스크롤 화면
- `encyclopedia-fish.svg`: 물고기 도감 목록 화면
- `encyclopedia-fish-detail.svg`: 물고기 상세 스크롤 화면
- `encyclopedia-sea.svg`: 해산물 도감 목록 화면
- `encyclopedia-sea-detail.svg`: 해산물 상세 스크롤 화면
- `encyclopedia-fossils.svg`: 화석 도감 목록 화면
- `encyclopedia-fossil-detail.svg`: 화석 상세 스크롤 화면
- `encyclopedia-art.svg`: 미술품 도감 목록 화면
- `encyclopedia-art-detail.svg`: 미술품 상세 스크롤 화면
- 외부 이미지나 네트워크 폰트에 의존하지 않습니다.
- Figma로 가져온 뒤 그룹을 풀어 색상, 텍스트, 도형을 편집할 수 있습니다.
- 한글 글꼴이 대체되면 텍스트 레이어를 선택하고 `Inter` 또는 설치된 한글 UI 글꼴로 변경합니다.
- 모든 주민 카드에는 `Wishlist`, `Island`, `Camping`, `Former`, `Photo` 상태 아이콘 5개가 항상 표시됩니다. 색이 있는 아이콘은 선택 상태, 테두리만 있는 아이콘은 미선택 상태입니다.
- 하단 메인 내비게이션은 `오늘`, `주민`, `도감`, `카탈로그`, `공략` 5개 항목으로 구성되며, 전체 메뉴는 우측 상단 햄버거 버튼에서 엽니다.
- SVG 자체는 정적 시안입니다. 프론트엔드에서는 각 아이콘을 토글 버튼으로 구현하고 클릭 시 선택/해제 상태와 저장 데이터를 함께 변경합니다.
