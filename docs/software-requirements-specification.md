# 모동숲 다이어리 Software Requirements Specification

- 문서 버전: 1.0
- 작성일: 2026-08-25
- 기준 프로젝트 경로: `C:\Users\user\Documents\KIMTAEMIN\acnh-diary`
- 기준 코드: 현재 워크스페이스의 FastAPI 백엔드, 정적 SPA, SQLite DB, 로컬 데이터/자산
- 목적: 현재 프로젝트를 기준으로 기능, 데이터, API, 화면, 제약, 비기능 요구사항을 상세히 정의한다.

## 1. 문서 범위

본 SRS는 `모동숲 다이어리` 웹 애플리케이션의 현재 구현 상태를 기준으로 한다. 앱은 Animal Crossing: New Horizons 데이터를 한국어 중심으로 탐색하고, 섬/주민/카탈로그/캘린더 진행 상황을 섬 단위로 기록하는 개인 관리 도구다.

문서에 포함하는 범위:

- FastAPI 서버와 `/api/*` 엔드포인트
- `static/index.html` 기반 정적 SPA
- `static/js/*` 모듈의 화면 동작
- `app.db` 상태 DB
- `content.db` 콘텐츠 DB
- 로컬 JSON 매핑과 정적 이미지 자산
- Vercel 배포 설정
- Supabase 전환을 고려한 현재 분기 구조

문서에 포함하지 않는 범위:

- Nintendo 또는 Animal Crossing 원저작권 관리
- 공개 사용자 인증/회원가입 UX의 완성 요구사항
- 앱스토어 배포용 네이티브 모바일 구현
- `frontend/` 폴더의 완성된 React 앱 요구사항. 현재 `frontend/`에는 `dist`, `.vite`, `node_modules`, 로그 파일은 있으나 `package.json`/소스가 없어 운영 기준 산출물로 보기 어렵다.

## 2. 제품 개요

### 2.1 제품명

- 한국어 표시명: 모동숲 다이어리
- 백엔드 프로젝트명: `nookipedia-api`
- FastAPI 앱 title: `ACNH Manager Prototype`
- 현재 앱 버전: `0.4.0`

### 2.2 제품 목표

1. 사용자는 여러 섬을 만들고 각 섬의 진행 상황을 독립적으로 기록할 수 있어야 한다.
2. 사용자는 주민 417명의 정보와 상태를 검색, 필터링, 정렬, 토글할 수 있어야 한다.
3. 사용자는 카탈로그 16개 유형의 보유, 기증, 수량, 변형 보유 상태를 관리할 수 있어야 한다.
4. 사용자는 홈 화면에서 섬 프로필, 섬 주민, 오늘의 계절/별자리/이벤트/레시피/낮은나무/출현 생물/카탈로그 진행률을 확인할 수 있어야 한다.
5. 사용자는 NPC 방문 캘린더에 방문 기록, 메모, 확인 여부를 저장할 수 있어야 한다.
6. 앱은 한국어 이름/카테고리/상태 표시를 우선 제공하되, 원문 영문 데이터도 상세 정보와 검색에 활용해야 한다.
7. 앱은 로컬 SQLite 기반으로 동작하되, Supabase 상태 저장소와 Supabase 자산 저장소로 전환 가능한 구조를 유지해야 한다.

### 2.3 주요 사용자

- 개인 플레이어: 자신의 섬 진행 상황을 기록한다.
- 다중 섬 플레이어: 여러 섬을 전환하며 섬별 상태를 분리 관리한다.
- 수집 진행률 관리 사용자: 가구, 의류, 생물, 미술품, 사진, 음악, 레시피 등을 보유/기증/수량 기준으로 관리한다.
- 이벤트/시간 관리 사용자: 타임슬립 시간을 적용해 오늘의 이벤트와 출현 생물을 확인한다.

## 3. 현재 시스템 구성

### 3.1 런타임 구조

- 백엔드: Python FastAPI
- 정적 프론트엔드: HTML, CSS, ES module JavaScript
- 상태 DB: SQLite `app.db`
- 콘텐츠 DB: SQLite `content.db`
- 로컬 매핑: `data/*_map_ko.json`
- 정적 자산: `static/icons`, `static/assets/music`, `static/assets/offline`, `villagers`
- 배포 타깃: Vercel Python function

### 3.2 주요 진입점

- FastAPI 앱: `app/main.py`
- Vercel 엔트리포인트: `app/index.py`
- 정적 HTML: `static/index.html`
- 프론트 메인 모듈: `static/app.js`
- API 클라이언트: `static/js/api.js`
- 화면 상태: `static/js/state.js`
- 데이터 로딩/필터링: `static/js/data.js`
- 렌더링: `static/js/render.js`
- 홈 화면: `static/js/home.js`
- 캘린더: `static/js/calendar.js`
- 상세 모달: `static/js/detail.js`
- 이벤트 바인딩: `static/js/events.js`

### 3.3 현재 데이터 규모

`content.db` 기준:

| catalog_type | 항목 수 | 변형 수 |
| --- | ---: | ---: |
| art | 43 | 0 |
| bugs | 80 | 0 |
| clothing | 1,527 | 5,540 |
| events | 1,428 | 0 |
| fish | 80 | 0 |
| fossils | 73 | 0 |
| furniture | 2,076 | 13,674 |
| gyroids | 36 | 189 |
| interior | 737 | 0 |
| items | 365 | 0 |
| music | 110 | 0 |
| photos | 966 | 4,319 |
| reactions | 88 | 0 |
| recipes | 924 | 0 |
| sea | 40 | 0 |
| special_items | 464 | 861 |
| tools | 150 | 314 |

추가 콘텐츠:

- 주민: 417명
- 레시피 태그: 19개

현재 `app.db` 상태 데이터:

- 섬: 3개
- 섬 프로필: 3개
- 주민 상태: 40개
- 캘린더 항목: 1개
- 카탈로그 상태: 0개
- 카탈로그 변형 상태: 0개
- 플레이어 프로필: 0개

## 4. 공통 요구사항

### 4.1 섬 단위 데이터 분리

- REQ-COM-001: 모든 사용자 상태 API는 `X-Island-Id` 헤더를 기준으로 상태를 읽고 써야 한다.
- REQ-COM-002: `X-Island-Id`가 비어 있으면 서버는 기본 섬 ID `1`을 사용해야 한다.
- REQ-COM-003: `X-Island-Id`가 정수가 아니거나 0 이하이면 서버는 HTTP 400 `invalid island id`를 반환해야 한다.
- REQ-COM-004: 프론트엔드는 현재 섬 ID를 `localStorage` 키 `acnh-current-island-id`에 저장해야 한다.
- REQ-COM-005: 섬이 변경되면 프론트엔드는 섬 프로필, 캘린더, 플레이어, 카탈로그 캐시, 상세 캐시, 음악 카드 메타 캐시를 무효화하고 새 섬 기준으로 다시 로드해야 한다.

### 4.2 SPA 네비게이션

- REQ-COM-006: 루트 `/`는 `static/index.html`을 반환해야 한다.
- REQ-COM-007: 앱은 서버에서 `/api/nav`로 모드 목록을 가져와 상단/모바일 네비게이션을 구성해야 한다.
- REQ-COM-008: 홈은 브랜드 버튼 `모동숲 다이어리`로 진입해야 하며, 상단 그룹 메뉴에서는 직접 표시하지 않는다.
- REQ-COM-009: 상단 네비게이션은 주민, 도감, 카탈로그, 기타 그룹을 제공해야 한다.
- REQ-COM-010: 도감 그룹은 `fossils`, `bugs`, `fish`, `sea`, `art`를 포함해야 한다.
- REQ-COM-011: 카탈로그 그룹은 `furniture`, `interior`, `clothing`, `music`, `items`, `tools`, `special_items`, `gyroids`, `photos`, `recipes`, `reactions`를 포함해야 한다.
- REQ-COM-012: `events` 모드는 상단 네비게이션에서 숨기고 홈 캘린더의 `이벤트 보기` 버튼을 통해 진입해야 한다.
- REQ-COM-013: 현재 모드가 홈이 아니면 breadcrumb를 `그룹 > 모드` 형식으로 표시해야 한다.
- REQ-COM-014: URL 쿼리 파라미터는 현재 모드, 검색어, 필터, 정렬, 탭, 레시피 태그 선택을 복원할 수 있어야 한다.
- REQ-COM-015: 브라우저 `popstate` 발생 시 URL 상태를 화면 상태에 재적용하고 해당 모드 데이터를 다시 로드해야 한다.

### 4.3 오류와 폴백

- REQ-COM-016: 데이터 로딩 실패 시 결과 영역에 `데이터를 불러오지 못했습니다.` 또는 모드별 오류 메시지를 표시해야 한다.
- REQ-COM-017: 이미지 로딩 실패 시 가능한 대체 이미지 URL 또는 `/static/no-image.svg`로 폴백해야 한다.
- REQ-COM-018: API 응답이 실패하면 프론트의 `getJSON`은 HTTP 상태와 응답 텍스트를 포함한 Error를 던져야 한다.

## 5. 홈 화면 요구사항

### 5.1 내 섬 요약

- REQ-HOME-001: 홈 화면은 현재 섬 이름, 주민대표 이름, 주민대표 생일을 표시해야 한다.
- REQ-HOME-002: 섬 이름이 없으면 `-` 또는 빈 상태를 표시해야 한다.
- REQ-HOME-003: `정보 수정` 버튼은 섬/플레이어 정보 설정 모달을 열어야 한다.

### 5.2 섬/프로필 설정 모달

- REQ-HOME-004: 설정 모달은 `role="dialog"`, `aria-modal="true"`를 가져야 한다.
- REQ-HOME-005: 설정 모달은 배경 클릭, 닫기 버튼, `Escape` 키로 닫을 수 있어야 한다.
- REQ-HOME-006: 섬 선택 드롭다운은 `/api/islands` 결과를 표시해야 한다.
- REQ-HOME-007: 섬 추가 입력값이 비어 있으면 서버는 `New Island`를 기본명으로 사용해야 한다.
- REQ-HOME-008: 섬 삭제 시 마지막 남은 섬은 삭제할 수 없어야 한다.
- REQ-HOME-009: 섬 삭제는 해당 섬의 주민 상태, 카탈로그 상태, 변형 상태, 캘린더, 플레이어, 프로필을 함께 삭제해야 한다.
- REQ-HOME-010: 섬 정보 입력은 섬 이름, 반구, 대표 과일, 대표 꽃, 주민대표 이름, 주민대표 생일을 포함해야 한다.
- REQ-HOME-011: 반구 값은 `north` 또는 `south`만 저장해야 하며, 유효하지 않은 값은 `north`로 정규화해야 한다.
- REQ-HOME-012: 대표 과일 선택지는 사과, 체리, 오렌지, 복숭아, 배를 제공해야 한다.
- REQ-HOME-013: 대표 꽃 선택지는 코스모스, 히아신스, 백합, 국화, 팬지, 장미, 튤립, 아네모네를 제공해야 한다.
- REQ-HOME-014: 생일 입력은 월/일 선택으로 제공해야 하고 저장 시 `MM-DD`로 정규화해야 한다.
- REQ-HOME-015: `YYYY-MM-DD`, `M-D`, `M/D`, `M.D` 형식의 기존 생일 문자열은 가능한 경우 `MM-DD`로 정규화해야 한다.

### 5.3 플레이어 관리

- REQ-HOME-016: 플레이어 목록은 현재 섬의 플레이어만 표시해야 한다.
- REQ-HOME-017: 플레이어는 이름, 생일, 주민대표 여부, 부주 여부를 저장해야 한다.
- REQ-HOME-018: 플레이어 이름은 필수이며 비어 있으면 HTTP 400 `player name is required`를 반환해야 한다.
- REQ-HOME-019: 섬당 등록 가능한 플레이어는 최대 8명이어야 한다.
- REQ-HOME-020: 신규 플레이어 등록 시 주민대표가 아직 없으면 자동으로 주민대표가 되어야 한다.
- REQ-HOME-021: 특정 플레이어를 주민대표로 지정하면 같은 섬의 다른 플레이어는 주민대표가 해제되어야 한다.
- REQ-HOME-022: 주민대표 플레이어를 삭제하면 남아 있는 첫 번째 플레이어가 자동 주민대표가 되어야 한다.
- REQ-HOME-023: 홈의 부주 목록은 `is_sub=true`인 플레이어를 중심으로 표시해야 한다.

### 5.4 타임슬립 시간

- REQ-HOME-024: 홈은 `타임슬립 시간 사용` 체크박스와 `datetime-local` 입력을 제공해야 한다.
- REQ-HOME-025: 타임슬립이 켜져 있고 `game_datetime`이 유효하면 홈 요약, 캘린더 기본 날짜, 현재 출현 생물은 해당 시간을 기준으로 계산해야 한다.
- REQ-HOME-026: 타임슬립이 꺼져 있거나 시간이 유효하지 않으면 서버의 앱 타임존 현재 시간을 사용해야 한다.
- REQ-HOME-027: 기본 앱 타임존은 `Asia/Seoul`이어야 하며 `APP_TIMEZONE`으로 변경할 수 있어야 한다.
- REQ-HOME-028: `현재 시간으로` 버튼은 게임 시간을 현재 시간으로 설정해야 한다.
- REQ-HOME-029: 유효 시간이 변경되면 `acnh:effective-date-changed` 이벤트를 발생시켜 캘린더와 홈 요약을 다시 동기화해야 한다.

### 5.5 현재 섬 주민

- REQ-HOME-030: 홈은 현재 섬 주민 수를 `n/10`으로 표시해야 한다.
- REQ-HOME-031: 현재 섬 주민 목록은 `/api/villagers?on_island=true`로 가져와야 한다.
- REQ-HOME-032: 현재 섬 주민은 `island_order` 오름차순으로 정렬되어야 하며, 순서가 없는 주민은 뒤로 가야 한다.
- REQ-HOME-033: 주민 카드는 이미지, 이름, 성격/종 정보를 표시해야 한다.
- REQ-HOME-034: 주민 제거 버튼은 해당 주민의 `on_island` 상태를 `false`로 바꾸어야 한다.
- REQ-HOME-035: 주민 카드는 드래그 앤 드롭으로 순서를 바꿀 수 있어야 한다.
- REQ-HOME-036: 순서 변경 저장 시 전달한 주민 ID 집합은 현재 섬 주민 집합과 정확히 일치해야 하며, 불일치하면 HTTP 400 `island villager ids do not match current on-island list`를 반환해야 한다.
- REQ-HOME-037: 섬 주민 추가 모달은 이름 검색, 성격 필터, 종 필터를 제공해야 한다.
- REQ-HOME-038: 주민 추가 후보 목록에는 이미 현재 섬 주민인 주민을 제외해야 한다.
- REQ-HOME-039: 섬 주민은 최대 10명까지 등록 가능해야 하며 초과 시 HTTP 400 `up to 10 villagers can be on island`를 반환해야 한다.
- REQ-HOME-040: 주민 카드 클릭 시 주민 상세 모달을 열어야 한다.

### 5.6 NPC 방문 캘린더

- REQ-HOME-041: 홈은 월간 캘린더를 표시해야 한다.
- REQ-HOME-042: 캘린더는 이전달/다음달 이동을 제공해야 한다.
- REQ-HOME-043: 날짜 선택 시 선택 날짜의 방문 기록과 이벤트/생일 annotation을 표시해야 한다.
- REQ-HOME-044: 날짜 선택 input 변경 시 해당 월/일로 캘린더를 동기화해야 한다.
- REQ-HOME-045: 사용자는 선택 날짜, 메모, 방문 확인 여부를 지정하고 NPC 버튼을 눌러 방문 기록을 저장할 수 있어야 한다.
- REQ-HOME-046: NPC 선택지는 여욱, 사하라, 패트릭, 저스틴, 레온, 여울, 고숙이, 무파니, 죠니, 해적 죠니, K.K., 부옥, 깨빈을 제공해야 한다.
- REQ-HOME-047: 부옥과 깨빈은 야간 NPC로 표시해야 한다.
- REQ-HOME-048: 일요일에는 무파니, 토요일에는 K.K.를 기본 방문 NPC로 자동 표시해야 한다.
- REQ-HOME-049: 기본 방문 NPC는 저장 DB 항목이 아니며 `checked=true`, `note=기본 방문`, `is_default=true`로 표시해야 한다.
- REQ-HOME-050: 기본 방문 NPC는 체크박스와 삭제 버튼을 비활성화해야 한다.
- REQ-HOME-051: 저장된 방문 기록은 체크 여부를 변경할 수 있어야 한다.
- REQ-HOME-052: 저장된 방문 기록은 삭제할 수 있어야 한다.
- REQ-HOME-053: 월간 캘린더 일자 칸에는 최대 3개의 미리보기 pill을 표시해야 한다.
- REQ-HOME-054: 월간 annotation은 주민 생일과 이벤트를 포함해야 한다.
- REQ-HOME-055: 이벤트 annotation은 `event_type=Event`인 이벤트만 포함해야 한다.
- REQ-HOME-056: 북반구/남반구 전용 이벤트는 현재 섬 반구에 맞는 것만 표시해야 한다.
- REQ-HOME-057: Festivale, Bunny Day 및 준비 기간은 연도별 Easter Sunday 기준 이동 날짜로 보정해야 한다.

### 5.7 오늘의 요약

- REQ-HOME-058: 홈 요약은 유효 시간 기준 `effective_datetime`을 사용해야 한다.
- REQ-HOME-059: 계절은 반구와 월을 기준으로 봄/여름/가을/겨울을 표시해야 한다.
- REQ-HOME-060: 별자리는 월/일을 기준으로 표시해야 한다.
- REQ-HOME-061: 다가오는 이벤트는 이벤트 날짜를 파싱해 오늘 이후 가까운 순서로 최대 6개 표시해야 한다.
- REQ-HOME-062: 이벤트 이름에 birthday가 포함된 이벤트는 다가오는 이벤트에서 제외해야 한다.
- REQ-HOME-063: 오늘의 너굴 쇼핑은 Nook Shopping event begins/ends 쌍을 기준으로 현재 진행 중인 이벤트를 우선 표시해야 한다.
- REQ-HOME-064: 진행 중인 너굴 쇼핑 이벤트가 없으면 가까운 너굴 쇼핑 이벤트를 대체 표시해야 한다.
- REQ-HOME-065: 시즌 레시피는 반구와 월/일 기준으로 봄의 대나무, 벚꽃, 여름 조개, 도토리/솔방울, 버섯, 단풍잎, 눈꽃, 장식 오너먼트/크리스마스 테마를 계산해야 한다.
- REQ-HOME-066: 개화 중인 낮은나무는 반구와 월 기준으로 동백나무, 철쭉, 수국, 무궁화, 플루메리아, 올리브를 계산해야 한다.
- REQ-HOME-067: 카탈로그 진행률은 화석, 토용, 가구, 인테리어, 옷, 잡화, 도구, 사진, 미술품을 표시해야 한다.
- REQ-HOME-068: 카탈로그 진행률은 보유 수, 전체 수, 부분 변형 수, 달성률을 포함해야 한다.
- REQ-HOME-069: 홈 요약의 클릭 가능한 항목은 해당 모드로 이동할 수 있어야 한다.

### 5.8 현재 출현 생물

- REQ-HOME-070: 홈은 현재 출현 생물을 곤충, 물고기, 해산물 탭으로 조회해야 한다.
- REQ-HOME-071: API는 `catalog_type=all|bugs|fish|sea`를 지원해야 한다.
- REQ-HOME-072: 다른 `catalog_type` 값은 HTTP 400 `catalog_type은 all/bugs/fish/sea 중 하나여야 합니다.`를 반환해야 한다.
- REQ-HOME-073: 출현 여부는 현재 반구, 현재 월, 현재 시간, 원본 데이터의 `months_array`/`times_by_month`/`time`/`times`를 기준으로 계산해야 한다.
- REQ-HOME-074: `All day`, `all-day`, `all_day`는 하루 종일 출현으로 처리해야 한다.
- REQ-HOME-075: 시간 범위는 `9 AM - 4 PM` 같은 12시간제 범위를 파싱해야 한다.
- REQ-HOME-076: 자정을 넘는 시간 범위도 현재 시간 포함 여부를 계산해야 한다.
- REQ-HOME-077: 홈 생물 목록은 보유 여부와 기증 여부 필터를 제공해야 한다.
- REQ-HOME-078: 생물 행은 이름, 크기, 출현 위치, 출현 시간, 출현 월, 잡은 적, 기증 여부를 표시해야 한다.

## 6. 주민 화면 요구사항

- REQ-VIL-001: 주민 화면은 전체 주민 목록을 표시해야 한다.
- REQ-VIL-002: 주민 검색은 한글명, 영문명, 기본 name 필드에 대해 부분 일치해야 한다.
- REQ-VIL-003: 주민 필터는 성격, 종, 서브타입을 지원해야 한다.
- REQ-VIL-004: 주민 정렬은 이름순, 종순, 생일순, 성격순을 지원해야 한다.
- REQ-VIL-005: 정렬 방향은 오름차순/내림차순 토글 버튼으로 변경할 수 있어야 한다.
- REQ-VIL-006: 주민 탭은 전체 주민, 좋아하는 주민, 우리 섬 주민, 섬 외 주민, 과거 주민을 제공해야 한다.
- REQ-VIL-007: 좋아하는 주민 탭은 `liked=true`인 주민만 표시해야 한다.
- REQ-VIL-008: 우리 섬 주민 탭은 `on_island=true`인 주민만 표시해야 한다.
- REQ-VIL-009: 섬 외 주민 탭은 `on_island=false`인 주민만 표시해야 한다.
- REQ-VIL-010: 과거 주민 탭은 `former_resident=true`인 주민만 표시해야 한다.
- REQ-VIL-011: 주민 카드는 주민 아이콘, 한국어 이름, 종/성격/서브타입, 생일을 표시해야 한다.
- REQ-VIL-012: 주민 카드는 좋아함, 캠핑장 방문, 우리 섬 주민, 과거 주민 토글을 제공해야 한다.
- REQ-VIL-013: 토글 변경은 `/api/villagers/{villager_id}/state`에 저장해야 한다.
- REQ-VIL-014: 존재하지 않는 주민 ID에 대한 상태 변경은 HTTP 404 `Villager not found.`를 반환해야 한다.
- REQ-VIL-015: 현재 필터에서 제외되는 상태 변경이 발생하면 카드를 즉시 제거하거나 목록을 갱신해야 한다.
- REQ-VIL-016: 주민 목록은 60개 단위로 점진 렌더링해야 한다.
- REQ-VIL-017: 주민 카드 클릭 시 상세 모달을 열어야 한다.
- REQ-VIL-018: 주민 상세는 이름, 종, 성격, 서브타입, 성별, 취미, 별자리, 생일, 말버릇, 좌우명, 사진/포스터 후보 등을 표시해야 한다.

## 7. 카탈로그 요구사항

### 7.1 공통 카탈로그 모드

- REQ-CAT-001: 카탈로그는 `clothing`, `furniture`, `items`, `tools`, `interior`, `gyroids`, `fossils`, `bugs`, `fish`, `sea`, `recipes`, `events`, `photos`, `art`, `reactions`, `music`, `special_items`를 지원해야 한다.
- REQ-CAT-002: 지원하지 않는 catalog type은 HTTP 404 `Catalog not found.`를 반환해야 한다.
- REQ-CAT-003: 각 카탈로그는 한국어 label과 status label을 가져야 한다.
- REQ-CAT-004: 목록 API는 검색어, 카테고리, 추가 필터, 보유 필터, 변형 범위, 정렬, 페이지네이션을 지원해야 한다.
- REQ-CAT-005: 목록 API의 기본 `page`는 1, 기본 `page_size`는 60이어야 한다.
- REQ-CAT-006: 서버는 `page_size`를 최소 1, 최대 200으로 제한해야 한다.
- REQ-CAT-007: 목록 응답은 `count`, `total_count`, `page`, `page_size`, `has_more`, `items`를 포함해야 한다.
- REQ-CAT-008: 프론트는 최초 로딩 시 페이지 크기 200으로 모든 페이지를 가져와 모드별 캐시에 저장할 수 있어야 한다.
- REQ-CAT-009: 프론트의 필터/정렬 전환은 가능하면 로컬 캐시에서 처리해야 한다.
- REQ-CAT-010: 모바일 폭 768px 이하에서는 카탈로그 목록이 하단 근처 도달 시 자동으로 더 불러오기 되어야 한다.
- REQ-CAT-011: 데스크톱에서는 `더보기` 버튼으로 다음 페이지를 불러올 수 있어야 한다.

### 7.2 검색/필터/정렬

- REQ-CAT-012: 검색은 `name`, `name_ko`, `name_en`, `source`, `source_notes`, `source_pairs`를 대상으로 부분 일치해야 한다.
- REQ-CAT-013: 일반 카테고리 필터는 `category`와 정확히 일치해야 한다.
- REQ-CAT-014: 레시피의 `season:`, `event:`, `npc:`, `ingredient:` 카테고리는 `recipe_filters` 포함 여부로 필터링해야 한다.
- REQ-CAT-015: 의류는 style 필터와 label theme 필터를 지원해야 한다.
- REQ-CAT-016: 이벤트는 event type 필터를 지원해야 한다.
- REQ-CAT-017: 미술품은 `genuine_only`, `has_fake` 진품/가품 필터를 지원해야 한다.
- REQ-CAT-018: 정렬은 번호순, 이름순, 획득방법순을 지원해야 한다.
- REQ-CAT-019: 정렬 방향은 오름차순/내림차순을 지원해야 한다.
- REQ-CAT-020: 초기화 버튼은 검색, 추가 필터, 출처 필터, 레시피 태그, 하위 카테고리, 보유 탭, 기증 탭, 정렬을 기본값으로 되돌려야 한다.

### 7.3 보유/기증/수량 상태

- REQ-CAT-021: 카탈로그 상태는 섬 ID, catalog type, item ID별로 저장해야 한다.
- REQ-CAT-022: 상태는 `owned`, `donated`, `quantity`를 포함해야 한다.
- REQ-CAT-023: 수량은 0 이상 정수로 정규화해야 한다.
- REQ-CAT-024: 보유 체크 변경은 `/api/catalog/{catalog_type}/{item_id}/state`로 저장해야 한다.
- REQ-CAT-025: 기증 체크 변경은 같은 상태 API에 `donated`를 저장해야 한다.
- REQ-CAT-026: 수량 변경 시 수량이 0보다 크면 보유 상태를 true로, 0이면 false로 간주해야 한다.
- REQ-CAT-027: 카탈로그 카드의 보유/미보유 탭은 재클릭 시 전체 상태로 돌아가야 한다.
- REQ-CAT-028: 기증/미기증 탭도 재클릭 시 전체 상태로 돌아가야 한다.
- REQ-CAT-029: 현재 렌더링된 항목 전체 보유 토글은 `/api/catalog/{catalog_type}/state/bulk`를 우선 사용해야 한다.
- REQ-CAT-030: bulk API가 404 또는 405일 때만 단건 업데이트 폴백을 수행해야 한다.
- REQ-CAT-031: 가구 중 변형이 없는 항목을 bulk 보유 처리할 때 수량은 최소 1로 설정해야 한다.
- REQ-CAT-032: 보유/미보유 탭에서 상태 변경으로 현재 필터에서 제외되는 항목은 즉시 화면에서 제거해야 한다.
- REQ-CAT-033: 대량 토글 시 해당 모드 상세 캐시는 비워야 한다.

### 7.4 변형 상태

- REQ-CAT-034: 변형 상태는 섬 ID, catalog type, item ID, variation ID별로 저장해야 한다.
- REQ-CAT-035: 변형 상태는 `owned`, `quantity`를 포함해야 한다.
- REQ-CAT-036: 상세 모달은 변형 목록을 색상/패턴/이미지와 함께 표시해야 한다.
- REQ-CAT-037: 변형별 보유 체크와 수량 변경은 개별 API로 저장할 수 있어야 한다.
- REQ-CAT-038: 상세 모달은 변형 전체 보유, 전체 해제 버튼을 제공해야 한다.
- REQ-CAT-039: 변형 일괄 변경은 `/api/catalog/{catalog_type}/{item_id}/variations/state`로 저장해야 한다.
- REQ-CAT-040: 존재하지 않는 variation ID는 HTTP 404 `Variation not found.` 또는 `Variation not found: {id}`를 반환해야 한다.
- REQ-CAT-041: 변형 보유 상태가 변경되면 상위 아이템의 `owned`는 모든 변형 보유 여부로 재계산되어야 한다.
- REQ-CAT-042: 상위 아이템의 `quantity`는 변형 수량 합계로 재계산되어야 한다.
- REQ-CAT-043: 변형 수량이 0보다 크면 해당 변형은 보유로 간주해야 한다.

### 7.5 상세 모달

- REQ-CAT-044: 카탈로그 카드 클릭 시 상세 모달을 열어야 한다.
- REQ-CAT-045: 상세 모달은 제목, 이미지, 소스 힌트, 기본 정보 필드, 변형, 원문 필드 보기를 제공해야 한다.
- REQ-CAT-046: 상세 모달은 이전/다음 버튼으로 현재 렌더링 목록 내 항목을 이동할 수 있어야 한다.
- REQ-CAT-047: 상세 모달은 배경 클릭, 닫기 버튼, `Escape` 키로 닫을 수 있어야 한다.
- REQ-CAT-048: 상세 조회 시 기본 목록 row에 변형이 없고 catalog type이 art가 아니면 단건 Nookipedia 상세 API를 시도할 수 있어야 한다.
- REQ-CAT-049: 상세 응답은 `summary`, `fields`, `raw_fields`, `variations`, `extra_images`를 포함할 수 있어야 한다.
- REQ-CAT-050: 비매품 항목은 상세 제목 영역과 카드에서 비매품 상태를 표시해야 한다.
- REQ-CAT-051: 하우스 이미지가 있는 경우 상세 모달에 하우스 이미지 섹션을 표시해야 한다.
- REQ-CAT-052: 원문 raw 필드는 `details/summary` UI로 접고 펼칠 수 있어야 한다.

### 7.6 레시피 태그/출처 필터

- REQ-CAT-053: 레시피 모드는 `/api/catalog/recipes/tags`로 태그 메타를 가져와야 한다.
- REQ-CAT-054: 레시피 태그가 아닌 catalog type의 tags 요청은 HTTP 404 `Recipe tags are only available for recipes.`를 반환해야 한다.
- REQ-CAT-055: 레시피 태그 모달은 선택 태그 수를 표시해야 한다.
- REQ-CAT-056: 레시피 태그 매칭 모드는 AND/OR를 지원해야 한다.
- REQ-CAT-057: 적용 버튼은 선택 태그와 매칭 모드로 목록을 갱신해야 한다.
- REQ-CAT-058: 선택 초기화 버튼은 태그 선택을 비우고 AND 모드로 되돌려야 한다.
- REQ-CAT-059: 활성 태그 바의 태그 chip 클릭은 해당 태그를 해제하고 목록을 갱신해야 한다.
- REQ-CAT-060: 레시피와 리액션은 출처 필터 active bar를 표시할 수 있어야 한다.
- REQ-CAT-061: 리액션의 `__not_for_sale__` 출처 필터는 펌킹, `*주민`, 그룹 체조, DJ K.K. 공연 출처를 비매품으로 간주해야 한다.

### 7.7 음악 특화 요구사항

- REQ-CAT-062: 음악 이미지는 런타임에서 외부 URL을 직접 쓰지 않고 `/static/assets/music/{번호}.png`를 사용해야 한다.
- REQ-CAT-063: 음악 카드 메타는 상세 API에서 구매가와 비매품 여부를 보강해 캐시할 수 있어야 한다.
- REQ-CAT-064: K.K. 노래가 구매 가능하고 구매가가 비어 있으면 기본 구매가 3,200벨을 적용해야 한다.

### 7.8 특수 아이템 요구사항

- REQ-CAT-065: `special_items`는 원본 catalog type을 `origin_catalog_type`으로 보유할 수 있어야 한다.
- REQ-CAT-066: `special_items` 상태 조회/저장은 가능한 경우 원본 catalog type의 상태를 사용해야 한다.
- REQ-CAT-067: `special_items` 상태 변경 후 원본 catalog type과 `special_items` 캐시를 함께 무효화해야 한다.

## 8. API 요구사항

### 8.1 Meta/Home API

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/` | SPA HTML 반환 |
| GET | `/api/nav` | 모드 목록 반환 |
| GET | `/api/meta` | 주민 성격/종 메타 반환 |
| GET | `/api/islands` | 섬 목록 반환 |
| POST | `/api/islands` | 섬 생성 |
| DELETE | `/api/islands/{island_id}` | 섬 삭제 |
| GET | `/api/home/summary` | 홈 요약 반환 |
| GET | `/api/home/catalog-progress` | 카탈로그 진행률 반환 |
| GET | `/api/home/creatures-now` | 현재 출현 생물 반환 |
| GET | `/api/profile` | 섬 프로필 반환 |
| POST | `/api/profile` | 섬 프로필 저장 |
| GET | `/api/calendar` | 월별 캘린더 저장 항목 반환 |
| GET | `/api/calendar/annotations` | 월별 생일/이벤트 annotation 반환 |
| GET | `/api/calendar/day` | 일별 캘린더 저장 항목 반환 |
| POST | `/api/calendar` | 캘린더 항목 생성/수정 |
| POST | `/api/calendar/{entry_id}/checked` | 캘린더 체크 상태 변경 |
| DELETE | `/api/calendar/{entry_id}` | 캘린더 항목 삭제 |
| GET | `/api/players` | 플레이어 목록 반환 |
| POST | `/api/players` | 플레이어 생성/수정 |
| POST | `/api/players/{player_id}/main` | 주민대표 지정 |
| DELETE | `/api/players/{player_id}` | 플레이어 삭제 |

### 8.2 Villager API

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/api/villagers` | 주민 목록 조회 |
| POST | `/api/villagers/{villager_id}/state` | 주민 상태 저장 |
| POST | `/api/villagers/island-order` | 섬 주민 순서 저장 |

`GET /api/villagers` query:

- `q`: 이름 검색
- `personality`: 성격 필터
- `species`: 종 필터
- `liked`: 좋아함 여부
- `on_island`: 현재 섬 주민 여부
- `former_resident`: 과거 주민 여부

### 8.3 Catalog API

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/api/catalog/{catalog_type}/meta` | 카탈로그 메타 반환 |
| GET | `/api/catalog/{catalog_type}/tags` | 레시피 태그 반환 |
| GET | `/api/catalog/{catalog_type}` | 카탈로그 목록 반환 |
| GET | `/api/catalog/{catalog_type}/{item_id}/detail` | 카탈로그 상세 반환 |
| POST | `/api/catalog/{catalog_type}/{item_id}/state` | 항목 상태 저장 |
| POST | `/api/catalog/{catalog_type}/state/bulk` | 항목 보유 상태 일괄 저장 |
| POST | `/api/catalog/{catalog_type}/{item_id}/variations/{variation_id}/state` | 변형 상태 저장 |
| POST | `/api/catalog/{catalog_type}/{item_id}/variations/state` | 변형 상태 일괄 저장 |

`GET /api/catalog/{catalog_type}` query:

- `q`
- `category`
- `style`
- `label_theme`
- `event_type`
- `fake_state`
- `owned`
- `variation_scope`: 빈 값, `full`, `partial`
- `sort_by`: `name`, `number`, `source`
- `sort_order`: `asc`, `desc`
- `page`
- `page_size`

### 8.4 Debug API

- REQ-API-001: `/api/debug/runtime-config`는 런타임 설정 진단 정보를 반환해야 한다.
- REQ-API-002: debug runtime config는 secret 값을 마스킹해야 한다.
- REQ-API-003: `/api/debug/state-probe`는 Supabase 상태 테이블 연결 상태와 샘플 row를 반환할 수 있어야 한다.

## 9. 데이터 모델 요구사항

### 9.1 상태 DB 테이블

`app.db`는 다음 테이블을 포함해야 한다.

- `island`
- `island_profile`
- `villager_state`
- `catalog_state`
- `catalog_variation_state`
- `calendar_entry`
- `player_profile`

### 9.2 island

- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `name`: TEXT NOT NULL DEFAULT ''
- `created_at`: TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at`: TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

요구사항:

- REQ-DATA-001: 앱 시작 시 ID 1 기본 섬을 보장해야 한다.
- REQ-DATA-002: 기존 프로필 이름이 있으면 기본 섬 이름으로 활용해야 한다.

### 9.3 island_profile

- `island_id`: INTEGER PRIMARY KEY
- `island_name`
- `nickname`
- `representative_fruit`
- `representative_flower`
- `birthday`
- `hemisphere`
- `time_travel_enabled`
- `game_datetime`
- `updated_at`

요구사항:

- REQ-DATA-003: `island_profile`은 `island`와 1:1 관계여야 한다.
- REQ-DATA-004: 프로필 저장 시 `island` 이름도 함께 갱신해야 한다.

### 9.4 villager_state

- 복합 PK: `island_id`, `villager_id`
- 상태 필드: `liked`, `on_island`, `camping_visited`, `former_resident`, `island_order`

요구사항:

- REQ-DATA-005: 주민 상태는 섬별로 독립되어야 한다.
- REQ-DATA-006: 기존 단일 섬/정수 ID 스키마는 마이그레이션 시 `island_id=1`, `villager_id=TEXT`로 변환해야 한다.

### 9.5 catalog_state

- 복합 PK: `island_id`, `catalog_type`, `item_id`
- 상태 필드: `owned`, `donated`, `quantity`

요구사항:

- REQ-DATA-007: 카탈로그 상태는 섬과 catalog type별로 독립되어야 한다.
- REQ-DATA-008: 기존 `clothing_state`가 있으면 `catalog_type=clothing`의 `catalog_state`로 이관해야 한다.

### 9.6 catalog_variation_state

- 복합 PK: `island_id`, `catalog_type`, `item_id`, `variation_id`
- 상태 필드: `owned`, `quantity`

요구사항:

- REQ-DATA-009: 변형 상태는 상위 아이템 상태와 동기화 가능해야 한다.
- REQ-DATA-010: 변형 상태 캐시는 항목 상태 변경 시 무효화해야 한다.

### 9.7 calendar_entry

- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `island_id`
- `visit_date`
- `npc_name`
- `note`
- `checked`
- `created_at`
- `updated_at`

요구사항:

- REQ-DATA-011: 같은 날짜/같은 NPC의 중복 저장을 DB 레벨에서 막지 않는다.
- REQ-DATA-012: 과거 `(visit_date, npc_name)` unique 제약이 있던 DB는 마이그레이션 시 제약을 제거해야 한다.

### 9.8 player_profile

- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `island_id`
- `name`
- `birthday`
- `is_main`
- `is_sub`
- `created_at`
- `updated_at`

요구사항:

- REQ-DATA-013: 플레이어는 섬별로 독립되어야 한다.
- REQ-DATA-014: 기존 단일 섬 플레이어 데이터는 마이그레이션 시 `island_id=1`로 변환해야 한다.

## 10. 콘텐츠 데이터 요구사항

- REQ-CONT-001: 앱은 `content.db`를 우선 사용해 주민/카탈로그/레시피 태그를 읽어야 한다.
- REQ-CONT-002: 콘텐츠 backend는 `CONTENT_BACKEND=auto|sqlite|supabase`로 선택 가능해야 한다.
- REQ-CONT-003: `auto` 모드에서는 사용 가능한 backend를 자동 선택해야 한다.
- REQ-CONT-004: 콘텐츠 DB가 없거나 해당 데이터가 없으면 로컬 JSON/Nookipedia loader fallback을 사용할 수 있어야 한다.
- REQ-CONT-005: Nookipedia API 키가 없어도 앱 startup은 실패하지 않아야 한다.
- REQ-CONT-006: API 키가 없으면 live Nookipedia 의존 route가 실패할 수 있음을 startup warning으로 출력해야 한다.
- REQ-CONT-007: 앱 시작 시 한국어 매핑 파일이 없으면 빈 객체 또는 기본 매핑으로 생성해야 한다.
- REQ-CONT-008: 주민 성격 기본 번역은 Cranky, Jock, Lazy, Normal, Peppy, Smug, Snooty, Big sister/Sisterly/Uchi를 포함해야 한다.
- REQ-CONT-009: 주민 종 기본 번역은 악어, 개미핥기, 곰, 아기곰, 새, 황소, 고양이, 닭, 소, 사슴, 개, 오리, 독수리, 코끼리, 개구리, 염소, 고릴라, 햄스터, 하마, 말, 캥거루, 코알라, 사자, 원숭이, 쥐, 문어, 타조, 펭귄, 돼지, 토끼, 코뿔소, 양, 다람쥐, 호랑이, 늑대를 포함해야 한다.
- REQ-CONT-010: `scripts/build_content_db.py`는 콘텐츠 DB 생성 도구로 유지해야 한다.
- REQ-CONT-011: `scripts/content_db_healthcheck.py`, `compare_content_counts.py`, `compare_catalog_queries.py`, `benchmark_catalog_latency.py`는 검증/회귀/성능 점검 용도로 유지해야 한다.

## 11. 이미지/자산 요구사항

- REQ-ASSET-001: 정적 파일은 `/static` 경로에서 서비스해야 한다.
- REQ-ASSET-002: 음악 이미지는 `static/assets/music/*.png`를 사용해야 한다.
- REQ-ASSET-003: 일반 카탈로그/주민 이미지는 콘텐츠 데이터의 `image_url`, `icon_url`, `image_uri` 등을 우선 사용해야 한다.
- REQ-ASSET-004: 미술품 이미지는 가능한 경우 `real_info`/`fake_info`의 texture URL을 우선 사용해야 한다.
- REQ-ASSET-005: 이미지 로드 실패 시 no-image SVG로 폴백해야 한다.
- REQ-ASSET-006: 자산 backend는 `ASSET_BACKEND=local|supabase|auto`로 선택 가능해야 한다.
- REQ-ASSET-007: Supabase 자산 URL은 `SUPABASE_URL`, `SUPABASE_ASSET_BUCKET`, `SUPABASE_ASSET_PREFIX`를 조합해 생성해야 한다.

## 12. 성능 요구사항

- REQ-PERF-001: 앱 startup 시 매핑 파일 보장, DB 초기화, 캐시 준비를 수행해야 한다.
- REQ-PERF-002: `PREWARM_ON_STARTUP` 기본값은 활성 상태여야 한다.
- REQ-PERF-003: API 키가 있고 prewarm이 켜져 있으면 주민과 모든 카탈로그를 백그라운드 thread에서 프리워밍해야 한다.
- REQ-PERF-004: prewarm 실패는 앱 기동 실패로 취급하지 않아야 한다.
- REQ-PERF-005: SQLite 상태 DB는 로컬에서 WAL, `synchronous=NORMAL`, `busy_timeout=10000`을 사용해야 한다.
- REQ-PERF-006: Vercel 환경의 콘텐츠 DB는 가능하면 read-only URI 또는 query-only 모드로 열어야 한다.
- REQ-PERF-007: 콘텐츠 DB 연결은 `busy_timeout=30000`을 사용해야 한다.
- REQ-PERF-008: 상태 저장소는 카탈로그 상태, 변형 보유 수, 변형 수량 합계를 메모리 캐시해야 한다.
- REQ-PERF-009: 상태 변경 후 관련 캐시를 무효화해야 한다.
- REQ-PERF-010: 프론트 검색 입력은 220ms debounce 후 로드해야 한다.
- REQ-PERF-011: 카탈로그 상세 prefetch는 인접 항목에 대해 수행할 수 있어야 한다.
- REQ-PERF-012: 주민 이미지는 lazy loading과 async decoding을 사용해야 한다.

## 13. 보안/개인정보 요구사항

- REQ-SEC-001: `.env`는 Git에 포함하지 않아야 한다.
- REQ-SEC-002: `.env.example`에는 placeholder만 포함해야 한다.
- REQ-SEC-003: `SUPABASE_SERVICE_ROLE_KEY`는 브라우저에 노출하면 안 된다.
- REQ-SEC-004: debug runtime config는 secret 값을 전체 노출하지 말고 마스킹해야 한다.
- REQ-SEC-005: 현재 앱은 별도 사용자 인증이 없으므로 공개 배포 시 섬 상태가 사용자별로 보호되지 않는 위험이 있다.
- REQ-SEC-006: Supabase 전환 시 상태 테이블은 `island.user_id = auth.uid()` 기반 RLS 정책으로 보호해야 한다.
- REQ-SEC-007: CORS origin은 `CORS_ORIGINS`로 제한 가능해야 한다.

## 14. 배포 요구사항

- REQ-DEP-001: Vercel은 `app/index.py`를 FastAPI entrypoint로 사용해야 한다.
- REQ-DEP-002: Vercel function maxDuration은 30초로 설정되어야 한다.
- REQ-DEP-003: Vercel 배포 번들에는 `static/index.html`, `static/app.js`, `static/styles.css`, `static/js/**`, `static/icons/**`, `static/no-image.svg`, `static/assets/music/**`, `data/**`, `content.db`가 포함되어야 한다.
- REQ-DEP-004: Vercel 배포 번들에서 `.git/**`, `.github/**`, `.venv/**`, `__pycache__/**`, `docs/**`, `villagers/**`, `app.db*`, `server*.log`, `data/.cache/**`는 제외되어야 한다.
- REQ-DEP-005: Vercel에서는 상태 DB로 로컬 `app.db`를 장기 사용하면 안 되며 Supabase 상태 backend를 사용해야 한다.
- REQ-DEP-006: `content.db`는 읽기 중심 데이터이므로 1차 운영에서는 번들 포함을 허용한다.

## 15. 현재 미완/주의 사항

- NOTE-001: `frontend/` 폴더는 Git status상 untracked이며 `package.json`이 없다. 현재 운영 앱의 기준은 `static/` SPA다.
- NOTE-002: `docs/current-db-schema.md`는 현재 코드/실제 `app.db`와 일부 차이가 있다. 최신 상태 스키마는 `app/core/db.py`와 실제 DB PRAGMA 기준으로 판단해야 한다.
- NOTE-003: 현재 앱은 인증 없는 개인 도구 구조다. 공개 멀티유저 서비스로 운영하려면 인증, 사용자-섬 소유권, RLS, 세션 처리가 추가 요구된다.
- NOTE-004: `.env` 파일이 로컬에 존재한다. 문서화/공유 시 secret 값이 노출되지 않도록 주의해야 한다.
- NOTE-005: `pyproject.toml`의 Python 요구 버전은 `>=3.14`이나 `requirements.txt`는 FastAPI/Uvicorn만 고정한다. 배포/로컬 런타임 호환성은 별도 확인이 필요하다.
- NOTE-006: `content.db`는 `.gitignore`에 포함되어 있으나 Vercel includeFiles에는 포함 대상으로 지정되어 있다. 배포 환경에서 실제 파일 포함 여부를 확인해야 한다.

## 16. 검증 시나리오

### 16.1 기본 smoke

1. 서버를 시작한다.
2. `/`가 HTML을 반환하는지 확인한다.
3. `/api/nav`가 홈, 주민, 전체 catalog type 모드를 반환하는지 확인한다.
4. `/api/meta`가 성격/종 메타를 반환하는지 확인한다.
5. `/api/debug/runtime-config`가 secret을 마스킹하는지 확인한다.

### 16.2 섬/프로필

1. 섬을 생성한다.
2. 생성된 섬으로 전환한다.
3. 섬 이름, 반구, 과일, 꽃, 대표명, 생일, 타임슬립 시간을 저장한다.
4. 새로고침 후 같은 값이 복원되는지 확인한다.
5. 마지막 섬 삭제가 차단되는지 확인한다.

### 16.3 주민

1. 주민 검색어를 입력한다.
2. 성격/종/서브타입을 변경한다.
3. 좋아함, 캠핑장 방문, 우리 섬 주민, 과거 주민을 토글한다.
4. 우리 섬 주민을 10명까지 추가한다.
5. 11번째 추가가 실패하는지 확인한다.
6. 섬 주민 순서를 드래그해 저장한다.

### 16.4 카탈로그

1. 각 catalog type 목록을 연다.
2. 검색, 하위 카테고리, 보유/미보유, 정렬을 적용한다.
3. 단일 항목 보유를 토글한다.
4. 현재 표시 항목 전체 보유 토글을 실행한다.
5. 상세 모달을 열고 변형 전체 보유/해제를 실행한다.
6. 변형 수량 변경 후 상위 아이템 보유/수량이 재계산되는지 확인한다.
7. 미술품 진품/가품 필터, 레시피 태그 AND/OR, 리액션 비매품 필터를 확인한다.

### 16.5 홈/캘린더

1. 타임슬립 시간을 설정한다.
2. 홈 요약의 계절, 별자리, 이벤트, 레시피, 낮은나무가 변경되는지 확인한다.
3. 캘린더에서 날짜를 선택한다.
4. NPC 방문 기록을 추가한다.
5. 방문 확인 체크를 변경한다.
6. 방문 기록을 삭제한다.
7. 일요일 무파니, 토요일 K.K. 기본 방문 표시와 삭제 불가 상태를 확인한다.
8. 주민 생일과 이벤트 annotation이 월간/일간 목록에 표시되는지 확인한다.

## 17. 추적성 요약

- 홈: REQ-HOME-001 ~ REQ-HOME-078
- 주민: REQ-VIL-001 ~ REQ-VIL-018
- 카탈로그: REQ-CAT-001 ~ REQ-CAT-067
- API: REQ-API-001 ~ REQ-API-003
- 데이터: REQ-DATA-001 ~ REQ-DATA-014
- 콘텐츠: REQ-CONT-001 ~ REQ-CONT-011
- 자산: REQ-ASSET-001 ~ REQ-ASSET-007
- 성능: REQ-PERF-001 ~ REQ-PERF-012
- 보안: REQ-SEC-001 ~ REQ-SEC-007
- 배포: REQ-DEP-001 ~ REQ-DEP-006
