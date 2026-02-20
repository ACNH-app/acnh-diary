# 데이터 로딩/이미지 소스 정리

이 문서는 현재 웹앱이 **어떤 데이터를 어디서 가져오고**, **어디에 저장하며**, **이미지를 어디서 불러오는지**를 코드 기준으로 정리한 문서입니다.

## 1) 전체 구조 요약
- 정적 데이터(아이템 메타)는 주로 `app/services/catalog_data.py`에서 로드
- 원본 소스
  - Nookipedia API (`https://api.nookipedia.com`)
  - 로컬 JSON (`data/acnhapi`, `data/norviah-animal-crossing`)
- 사용자 상태 데이터(보유/미보유, 수량, 프로필 등)는 SQLite(`app.db`) 저장
- 프론트는 FastAPI `/api/*` 엔드포인트만 호출하고, 외부 API를 직접 호출하지 않음

## 2) 카탈로그/주민 데이터 출처

### 2.1 Nookipedia API 기반
아래 카테고리는 기본적으로 Nookipedia를 통해 가져옵니다. (`app/core/config.py`의 `CATALOG_TYPES`)

- clothing: `/nh/clothing`
- furniture: `/nh/furniture`
- items: `/nh/items`
- tools: `/nh/tools`
- interior: `/nh/interior`
- gyroids: `/nh/gyroids`
- fossils: `/nh/fossils/individuals`
- bugs: `/nh/bugs`
- fish: `/nh/fish`
- sea: `/nh/sea`
- events: `/nh/events`
- art: `/nh/art`
- photos: `/nh/photos`
- posters: `/nh/posters`
- villagers: `/villagers?game=nh&nhdetails=true`

관련 코드:
- `app/services/nookipedia_client.py`
- `app/services/catalog_data.py`
- `app/core/config.py`

### 2.2 로컬 JSON 기반(직접 로드)
아래는 현재 로컬 JSON을 직접 읽어 구성합니다.

- reactions: `data/norviah-animal-crossing/Reactions.json` (또는 `reactions.json`)
- recipes: 기본 목록은 Nookipedia, 추가/보완 정보는 `data/norviah-animal-crossing/recipes.json` 참고
- music: `data/acnhapi/music.json`

관련 코드:
- `app/services/catalog_data.py`
  - `load_local_reactions()`
  - `load_local_recipes_by_name()`
  - `load_local_music_catalog()`

## 3) 한글명/번역 매핑 데이터
- 주민/카탈로그 한글명은 `data/*_name_map_ko.json` 파일군 사용
- 성격/종/이벤트 국가/말버릇 등도 별도 매핑 파일 사용
- 앱 시작 시 매핑 파일이 없으면 생성/초기화 수행

관련 코드:
- `app/services/mappings.py`
- `app/main.py` (`on_startup`)

대표 파일 예시:
- `data/name_map_ko.json` (주민 이름)
- `data/furniture_name_map_ko.json`
- `data/items_name_map_ko.json`
- `data/tools_name_map_ko.json`
- `data/interior_name_map_ko.json`
- `data/music_name_map_ko.json`
- `data/reaction_name_map_ko.json`

## 4) 사용자 상태 저장(DB)
사용자가 체크하는 값은 로컬 DB(SQLite)에 저장됩니다.

DB 파일:
- 기본 `app.db` (`DB_PATH` 환경변수로 변경 가능)

주요 테이블:
- `villager_state` (좋아함/섬주민/과거주민/정렬)
- `catalog_state` (보유/기증/수량)
- `catalog_variation_state` (변형별 보유/수량)
- `island_profile` (섬 정보)
- `calendar_entry` (방문 NPC/메모)
- `player_profile` (주민대표/부주)

관련 코드:
- `app/core/db.py`
- `app/repositories/state.py`

## 5) 이미지 소스 정리

### 5.1 일반 카탈로그/주민 이미지
- 원칙: API 응답의 이미지 필드(`image_url`, `icon_url`, `image_uri` 등)를 우선 사용
- 미술품은 `real_info`/`fake_info` 내부 `texture_url`을 우선 사용하도록 보정
- 실패 시 `/static/no-image.svg` 폴백

관련 코드:
- `app/services/catalog_data.py` (`_extract_image_url`)
- `static/js/render.js`, `static/js/detail.js` (프론트 폴백)

### 5.2 음악 이미지
현재 음악 이미지는 **외부 URL을 런타임에서 직접 사용하지 않고**, 로컬 정적 파일만 사용합니다.

- 런타임 경로: `/static/assets/music/{번호}.png`
- 실제 파일 위치: `static/assets/music/*.png`
- 동기화 스크립트: `scripts/download_music_images.py`
  - 소스 기준으로 로컬 파일을 내려받고
  - 결과를 `data/music_image_manifest.json`에 기록

관련 코드:
- `app/services/catalog_data.py` (`load_local_music_catalog`)
- `scripts/download_music_images.py`

## 6) 캐시/성능 방식

### 6.1 Nookipedia 응답 디스크 캐시
- 위치: `data/.cache/nookipedia/*.json`
- 기본 TTL: 24시간 (`NOOKIPEDIA_CACHE_TTL_SEC`로 조정)

관련 코드:
- `app/services/nookipedia_client.py`

### 6.2 프로세스 메모리 캐시
- `@lru_cache`로 주민/카탈로그/상세 일부 캐싱
- 상태 조회도 리포지토리 레벨 메모리 캐시 사용

관련 코드:
- `app/services/catalog_data.py`
- `app/services/nookipedia_client.py`
- `app/repositories/state.py`

### 6.3 프론트 캐시
- 카탈로그 목록을 모드별로 `state.catalogAllItemsByMode`에 보관
- 필터/정렬/탭 전환은 로컬 캐시 배열 기준으로 처리

관련 코드:
- `static/js/data.js`

## 7) 앱 시작 시 동작
1. `.env`/환경변수에서 API 키 로드 (`NOOKIPEDIA_API_KEY`)
2. 매핑 파일 존재 보장 및 자동 생성
3. DB 스키마/마이그레이션 실행
4. (옵션) 백그라운드 프리워밍으로 주민/카탈로그 선로드 (`PREWARM_ON_STARTUP=1` 기본)

관련 코드:
- `app/main.py` `on_startup`

## 8) 요약 (한 줄)
- **데이터 본문**: Nookipedia + 일부 로컬 JSON 혼합
- **한글화**: 로컬 매핑 JSON
- **사용자 체크 상태**: SQLite
- **이미지**: API 원본 URL(카테고리별 보정) + 일부 로컬 정의(Norviah) + no-image 폴백
