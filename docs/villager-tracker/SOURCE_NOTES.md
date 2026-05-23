# 데이터 및 이미지 출처

## 주민 기본 데이터

- 원본 파일: `data/acnhapi/villagers.json`
- 사용 필드: 이름, 성격, 생일, 종, 성별, 취미, 말버릇, 좌우명, 색상 등

## 한글 매핑

- 주민 이름: `data/name_map_ko.json`
- 성격: `data/personality_map_ko.json`
- 동물종: `data/species_map_ko.json`
- 말버릇/좌우명 보조 매핑:
  - `data/villager_saying_map_ko.json`

## 주민 이미지

- 로컬 이미지 폴더: `villagers/*.png`
- 새 정적 앱 배포용 복사 위치: `docs/villager-tracker/assets/villagers/*.png`

## 저장 방식

- 사용자 체크 데이터는 서버 DB가 아니라 브라우저 `localStorage`에 저장됩니다.
- 저장 키: `acnh-villager-tracker-state-v1`
