# ACNH iPhone App API Spec

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`
- 버전: `v0.1`
- 관련 문서:
- `docs/ios-app-prd.md`
- `docs/ios-app-current-state-gap-analysis.md`

## 1. 목적

이 문서는 현재 FastAPI 백엔드를 iPhone 앱 클라이언트에서 사용하기 위한 1차 계약 문서다. 현재 서버 구현을 기준선으로 삼되, 앱 전환 시 추가로 고정해야 할 규칙을 함께 적는다.

## 2. 공통 정책

### 2.1 Base URL

- Development: `[TBD]`
- Staging: `[TBD]`
- Production: `[TBD]`

### 2.2 인증

현재 상태:

1. 인증 없음
2. 상태 변경 API도 인증 없이 호출 가능

앱 1차 기준:

1. 인증 헤더 미사용
2. 개인용 또는 제한된 배포 환경 전제

향후 확장:

1. `Authorization: Bearer <token>` 헤더를 주입할 수 있게 네트워크 계층을 설계한다.

### 2.3 콘텐츠 타입

모든 요청/응답은 JSON을 기본으로 한다.

```http
Content-Type: application/json
Accept: application/json
```

### 2.4 에러 응답

현재 구현은 FastAPI 기본 `detail` 형식을 주로 사용한다.

예시:

```json
{
  "detail": "아이템을 찾을 수 없습니다."
}
```

앱 처리 원칙:

1. `detail` 문자열이 있으면 사용자 메시지 후보로 사용한다.
2. 네트워크 오류와 서버 오류를 구분해 표시한다.
3. 추후 공통 `error.code` 구조로 전환 가능성을 열어둔다.

### 2.5 날짜/시간 규칙

현재 사용 형식:

1. 월: `YYYY-MM`
2. 일자: `YYYY-MM-DD`
3. 홈 유효 시각: `YYYY-MM-DDTHH:MM`
4. 생일: `MM-DD`

주의:

1. 타임존 표시는 현재 응답에 명시되지 않는다.
2. 홈 기준 시각은 섬 프로필의 `game_datetime`과 `hemisphere` 영향을 받는다.

## 3. 홈 API

### 3.1 홈 요약

- Method: `GET`
- Path: `/api/home/summary`

목적:

1. 홈 화면 상단 요약 데이터 조회

응답 구조:

```json
{
  "effective_datetime": "2026-03-12T09:00",
  "hemisphere": "north",
  "island_profile": {},
  "calendar": {},
  "today_events": [],
  "catalog_progress": {}
}
```

비고:

1. 실제 필드명은 서버 구현과 함께 최종 고정이 필요하다.
2. 앱은 필수 필드만 뷰모델로 매핑한다.

### 3.2 현재 잡을 수 있는 생물

- Method: `GET`
- Path: `/api/home/creatures-now`

쿼리 파라미터:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `catalog_type` | string | N | `all`, `bugs`, `fish`, `sea` |
| `owned` | bool | N | 보유 상태 필터 |
| `donated` | bool | N | 기증 상태 필터 |

응답 예시:

```json
{
  "effective_datetime": "2026-03-12T09:00",
  "hemisphere": "north",
  "catalog_type": "all",
  "count": 3,
  "counts_by_type": {
    "bugs": 1,
    "fish": 1,
    "sea": 1
  },
  "items": [
    {
      "id": "common-butterfly",
      "catalog_type": "bugs",
      "number": 1,
      "name_ko": "배추흰나비",
      "name_en": "Common butterfly",
      "icon_url": "https://...",
      "size": "-",
      "location": "꽃 주변",
      "time": "4 AM - 7 PM",
      "months": "9-6",
      "owned": false,
      "donated": false
    }
  ]
}
```

에러:

1. `400` 잘못된 `catalog_type`

## 4. 메타 API

### 4.1 주민 메타

- Method: `GET`
- Path: `/api/meta`

목적:

1. 주민 필터용 성격/종 목록 조회

응답 예시:

```json
{
  "personalities": [
    { "en": "Lazy", "ko": "먹보" }
  ],
  "species": [
    { "en": "Cat", "ko": "고양이" }
  ]
}
```

## 5. 주민 API

### 5.1 주민 목록

- Method: `GET`
- Path: `/api/villagers`

쿼리 파라미터:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `q` | string | N | 이름 검색 |
| `personality` | string | N | 성격 필터 |
| `species` | string | N | 종 필터 |
| `liked` | bool | N | 좋아하는 주민 |
| `on_island` | bool | N | 우리 섬 주민 |
| `former_resident` | bool | N | 과거 주민 |

응답 예시:

```json
{
  "count": 1,
  "items": [
    {
      "id": "bob",
      "name": "Bob",
      "name_ko": "니콜",
      "name_en": "Bob",
      "species": "Cat",
      "personality": "Lazy",
      "image_url": "https://...",
      "liked": true,
      "on_island": false,
      "camping_visited": false,
      "former_resident": false,
      "island_order": 0
    }
  ]
}
```

비고:

1. `on_island=true`일 때 서버는 `island_order` 기준으로 정렬한다.

### 5.2 주민 상태 수정

- Method: `POST`
- Path: `/api/villagers/{villager_id}/state`

요청 본문:

```json
{
  "liked": true,
  "on_island": true,
  "camping_visited": false,
  "former_resident": false
}
```

응답:

```json
{
  "villager_id": "bob",
  "liked": true,
  "on_island": true,
  "camping_visited": false,
  "former_resident": false
}
```

에러:

1. `404` 존재하지 않는 주민
2. `400` 우리 섬 주민 10명 초과

부분 업데이트 규칙:

1. 전달하지 않은 필드는 기존 값을 유지한다.

### 5.3 섬 주민 순서 변경

- Method: `POST`
- Path: `/api/villagers/island-order`

요청:

```json
{
  "villager_ids": ["bob", "raymond", "ankha"]
}
```

응답:

```json
{
  "ok": true,
  "count": 3
}
```

에러:

1. `400` 현재 섬 주민 목록과 요청 목록이 일치하지 않음

## 6. 카탈로그 API

### 6.1 카탈로그 메타

- Method: `GET`
- Path: `/api/catalog/{catalog_type}/meta`

목적:

1. 카테고리, 상태 라벨, 스타일, 라벨 테마 등 필터 메타 조회

응답 예시:

```json
{
  "label": "가구",
  "status_label": "보유",
  "categories": [
    { "en": "Housewares", "ko": "가구" }
  ]
}
```

카테고리별 추가 필드:

1. `clothing`
- `styles`
- `label_themes`

2. `events`
- `event_types`

3. `art`
- `authenticity_types`

에러:

1. `404` 알 수 없는 카탈로그

### 6.2 레시피 태그

- Method: `GET`
- Path: `/api/catalog/recipes/tags`

응답:

```json
{
  "count": 10,
  "items": []
}
```

### 6.3 카탈로그 목록

- Method: `GET`
- Path: `/api/catalog/{catalog_type}`

쿼리 파라미터:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `q` | string | N | 검색어 |
| `category` | string | N | 카테고리 |
| `style` | string | N | 의류 스타일 |
| `label_theme` | string | N | 의류 라벨 테마 |
| `event_type` | string | N | 이벤트 필터 |
| `fake_state` | string | N | 미술품 진위 필터 |
| `owned` | bool | N | 보유 여부 |
| `variation_scope` | string | N | `full` 또는 `partial` |
| `sort_by` | string | N | 정렬 키 |
| `sort_order` | string | N | `asc`, `desc` |
| `page` | int | N | 기본 `1` |
| `page_size` | int | N | 기본 `60`, 최대 `200` |

응답 예시:

```json
{
  "count": 60,
  "total_count": 320,
  "page": 1,
  "page_size": 60,
  "has_more": true,
  "items": [
    {
      "id": "wooden-chair",
      "name": "Wooden chair",
      "name_ko": "나무 의자",
      "name_en": "Wooden chair",
      "category": "Housewares",
      "image_url": "https://...",
      "owned": true,
      "donated": false,
      "quantity": 1,
      "variation_total": 3,
      "variation_owned_count": 1
    }
  ]
}
```

규칙:

1. 목록 API는 검색/필터/정렬 후 페이지네이션한다.
2. 앱은 `has_more` 기반 무한 스크롤 또는 더보기 방식을 사용할 수 있다.

에러:

1. `404` 알 수 없는 카탈로그

### 6.4 카탈로그 상세

- Method: `GET`
- Path: `/api/catalog/{catalog_type}/{item_id}/detail`

응답 예시:

```json
{
  "id": "wooden-chair",
  "name": "Wooden chair",
  "name_ko": "나무 의자",
  "image_url": "https://...",
  "owned": true,
  "donated": false,
  "quantity": 1,
  "variations": [
    {
      "variation_id": "blue",
      "owned": true,
      "quantity": 1
    }
  ]
}
```

비고:

1. 카테고리별 상세 필드는 다를 수 있다.
2. 앱은 공통 필드와 카테고리별 확장 필드를 분리해서 파싱한다.

에러:

1. `404` 알 수 없는 카탈로그
2. `404` 아이템 없음
3. `404` 원본 데이터 없음

### 6.5 카탈로그 상태 수정

- Method: `POST`
- Path: `/api/catalog/{catalog_type}/{item_id}/state`

요청:

```json
{
  "owned": true,
  "donated": false,
  "quantity": 1
}
```

응답:

```json
{
  "catalog_type": "furniture",
  "item_id": "wooden-chair",
  "owned": true,
  "donated": false,
  "quantity": 1
}
```

규칙:

1. 전달하지 않은 필드는 기존 값을 유지한다.
2. 서버는 아이템 상태 갱신 후 변형 상태를 동기화할 수 있다.

### 6.6 카탈로그 벌크 수정

- Method: `POST`
- Path: `/api/catalog/{catalog_type}/state/bulk`

요청:

```json
{
  "item_ids": ["a", "b", "c"],
  "owned": true
}
```

응답 예시:

```json
{
  "updated": 3,
  "owned": true
}
```

비고:

1. iPhone 앱 1차에서는 숨김 기능으로 두는 것을 권장한다.

### 6.7 변형 상태 수정

- Method: `POST`
- Path: `/api/catalog/{catalog_type}/{item_id}/variations/{variation_id}/state`

요청:

```json
{
  "owned": true,
  "quantity": 1
}
```

응답:

```json
{
  "catalog_type": "furniture",
  "item_id": "wooden-chair",
  "variation_id": "blue",
  "owned": true,
  "quantity": 1
}
```

### 6.8 변형 상태 일괄 수정

- Method: `POST`
- Path: `/api/catalog/{catalog_type}/{item_id}/variations/state`

요청:

```json
{
  "items": [
    { "variation_id": "blue", "owned": true, "quantity": 1 }
  ]
}
```

응답 예시:

```json
{
  "updated": 1
}
```

## 7. 섬 프로필/플레이어 API

### 7.1 섬 프로필 조회

- Method: `GET`
- Path: `/api/profile`

응답:

```json
{
  "island_name": "",
  "nickname": "",
  "representative_fruit": "",
  "representative_flower": "",
  "birthday": "",
  "hemisphere": "north",
  "time_travel_enabled": false,
  "game_datetime": ""
}
```

### 7.2 섬 프로필 수정

- Method: `POST`
- Path: `/api/profile`

요청/응답 구조는 조회와 동일하다.

### 7.3 플레이어 목록

- Method: `GET`
- Path: `/api/players`

응답:

```json
[
  {
    "id": 1,
    "name": "Temn",
    "birthday": "03-12",
    "is_main": true,
    "is_sub": false
  }
]
```

### 7.4 플레이어 저장

- Method: `POST`
- Path: `/api/players`

요청:

```json
{
  "id": 1,
  "name": "Temn",
  "birthday": "03-12",
  "is_main": true,
  "is_sub": false
}
```

에러:

1. `400` 유효성 또는 비즈니스 규칙 오류

### 7.5 대표 플레이어 설정

- Method: `POST`
- Path: `/api/players/{player_id}/main`

### 7.6 플레이어 삭제

- Method: `DELETE`
- Path: `/api/players/{player_id}`

에러:

1. `404` 대상 플레이어 없음

## 8. 캘린더 API

### 8.1 월별 일정 목록

- Method: `GET`
- Path: `/api/calendar`

쿼리:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `month` | string | Y | `YYYY-MM` |

응답:

```json
[
  {
    "id": 1,
    "visit_date": "2026-03-12",
    "npc_name": "K.K.",
    "note": "",
    "checked": false
  }
]
```

### 8.2 월별 주석 데이터

- Method: `GET`
- Path: `/api/calendar/annotations`

쿼리:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `month` | string | Y | `YYYY-MM` |

비고:

1. 앱은 월 셀 뱃지 렌더링 용도로 사용한다.

### 8.3 일자별 일정 목록

- Method: `GET`
- Path: `/api/calendar/day`

쿼리:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `date` | string | Y | `YYYY-MM-DD` |

### 8.4 일정 저장

- Method: `POST`
- Path: `/api/calendar`

요청:

```json
{
  "id": 1,
  "visit_date": "2026-03-12",
  "npc_name": "K.K.",
  "note": "토요일 방문",
  "checked": false
}
```

응답:

```json
{
  "id": 1,
  "visit_date": "2026-03-12",
  "npc_name": "K.K.",
  "note": "토요일 방문",
  "checked": false
}
```

### 8.5 일정 체크 상태 변경

- Method: `POST`
- Path: `/api/calendar/{entry_id}/checked`

요청:

```json
{
  "checked": true
}
```

### 8.6 일정 삭제

- Method: `DELETE`
- Path: `/api/calendar/{entry_id}`

## 9. 앱 구현 시 주의사항

1. 현재 서버는 에러 표준화가 덜 되어 있으므로 앱에서 `detail` 기반 방어 처리가 필요하다.
2. 현재 서버는 인증이 없으므로 공개 배포 시 보안 리스크가 있다.
3. 목록/상세 응답의 필드 폭이 넓을 수 있으므로 앱 DTO를 별도로 정의하는 편이 낫다.
4. 카테고리별 상세 필드가 다르므로 공통 모델과 확장 모델을 분리한다.

## 10. 차기 버전에서 고정할 항목

1. 공통 에러 포맷
2. 인증 헤더 및 만료 처리
3. `updated_at` 또는 버전 필드 기반 충돌 처리
4. 캐시 힌트 헤더 또는 응답 메타
5. 홈 요약 응답 필드 확정
