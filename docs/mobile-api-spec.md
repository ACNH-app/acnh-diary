# ACNH 모바일 앱 API Spec

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`
- 플랫폼: `Flutter`

## 1. 목적

이 문서는 Flutter 모바일 앱과 현재 FastAPI 서버 사이의 공통 계약 문서다.

## 2. 공통 정책

1. 현재 인증 없음
2. JSON 요청/응답 사용
3. 에러는 현재 FastAPI `detail` 형식을 우선 처리
4. 날짜 형식:
- 월: `YYYY-MM`
- 일자: `YYYY-MM-DD`
- 생일: `MM-DD`

## 3. 주요 엔드포인트

1. 홈
- `GET /api/home/summary`
- `GET /api/home/creatures-now`

2. 주민
- `GET /api/meta`
- `GET /api/villagers`
- `POST /api/villagers/{villager_id}/state`
- `POST /api/villagers/island-order`

3. 카탈로그
- `GET /api/catalog/{catalog_type}/meta`
- `GET /api/catalog/{catalog_type}`
- `GET /api/catalog/{catalog_type}/{item_id}/detail`
- `POST /api/catalog/{catalog_type}/{item_id}/state`
- `POST /api/catalog/{catalog_type}/{item_id}/variations/{variation_id}/state`

4. 프로필/플레이어
- `GET /api/profile`
- `POST /api/profile`
- `GET /api/players`
- `POST /api/players`
- `POST /api/players/{player_id}/main`
- `DELETE /api/players/{player_id}`

5. 캘린더
- `GET /api/calendar`
- `GET /api/calendar/annotations`
- `GET /api/calendar/day`
- `POST /api/calendar`
- `POST /api/calendar/{entry_id}/checked`
- `DELETE /api/calendar/{entry_id}`

## 4. 앱 구현 주의사항

1. 주민 `on_island`는 최대 10명 제한
2. 카탈로그 목록은 `page/page_size` 기반
3. 상태 변경 API는 부분 업데이트 성격
4. 상세 응답은 카테고리별 필드 차이가 있으므로 앱 DTO 분리 필요
