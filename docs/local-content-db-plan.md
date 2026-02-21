# 로컬 콘텐츠 DB 전환 계획

## 목표
- 외부 Nookipedia API 호출 없이 서비스 동작
- 로컬 데이터(JSON/매핑) 기반으로 콘텐츠 DB(`content.db`)를 빌드
- 이미지 URL도 데이터에 포함(향후 로컬 이미지 파일 경로로 전환 가능)
- 사용자 상태 DB(`app.db`)와 콘텐츠 DB를 분리

## 현재 구조 요약
- 콘텐츠 데이터 원천:
  - `data/acnhapi/*.json`
  - `data/norviah-animal-crossing/*.json`
  - Nookipedia API(캐시 포함) 경로
- 한글 매핑:
  - `data/*_name_map_ko.json`, `event_country_map_ko.json`, 기타 매핑 파일
- 서비스 가공:
  - `app/services/catalog_data.py`, `app/services/mappings.py`, `app/services/source.py`
- 사용자 상태:
  - `app.db` (`catalog_state`, `catalog_variation_state`, `villager_state` 등)

## 목표 아키텍처
- `content.db` (읽기 중심)
  - `catalog_items`
  - `catalog_variations`
  - `catalog_meta`
  - `villagers`
  - `content_version`
- `app.db` (쓰기 중심, 기존 유지)
  - 보유/기증/수량/프로필/캘린더 등 상태

## 데이터 정책
- 원본(raw) JSON은 계속 보관
- 빌드 결과(DB)는 재생성 가능해야 함(스크립트 1회 실행)
- 이미지 관련 정책:
  - 현재: 원본 image URL 저장
  - 향후: 로컬 이미지 다운로드 후 `local_image_path` 컬럼으로 전환

## 단계
1. 계획/체크리스트 문서화
2. `content.db` 스키마 정의 + 생성 스크립트
3. 로컬 JSON + 매핑 통합 적재 파이프라인 구현
4. API 조회를 `content.db` 우선으로 전환
5. 검증(건수/정렬/필터/상세/상태 결합) 및 성능 측정
6. 운영 문서(재빌드/배포/백업) 정리

## 검증 기준
- 카탈로그별 아이템 건수 일치(허용오차 0)
- 상세 조회 시 기존과 동일 필드 제공(이미지 URL 포함)
- 필터/정렬/검색 결과 동일
- 상태 체크(보유/기증/수량) 기존 동작 유지
- 첫 요청 및 탭 전환 속도 개선

