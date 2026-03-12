# iPhone 앱 API 명세 템플릿

- 문서 목적: iPhone 앱과 `nookipedia-api` 백엔드 사이의 계약을 고정한다.
- 사용 방법: 현재 엔드포인트를 기준으로 필요한 필드와 정책을 채운다.

## 1. 기본 정보

- 문서명: `ACNH iPhone App API Spec`
- 작성일: [YYYY-MM-DD]
- 작성자: [이름]
- 관련 문서:
- `docs/ios-app-prd-template.md`
- `docs/ios-app-current-state-gap-analysis.md`

## 2. 공통 정책

### 2.1 Base URL

- Development: `[https://dev.example.com]`
- Staging: `[https://staging.example.com]`
- Production: `[https://api.example.com]`

### 2.2 인증

- 인증 방식: `[없음 / Bearer token / Cookie session]`
- 헤더:

```http
Authorization: Bearer <token>
```

- 토큰 만료 응답 처리: `[정의]`
- refresh 정책: `[정의]`

### 2.3 공통 헤더

```http
Content-Type: application/json
Accept: application/json
```

### 2.4 공통 에러 형식

```json
{
  "error": {
    "code": "string_code",
    "message": "사용자에게 노출 가능한 메시지",
    "details": {}
  }
}
```

정의 항목:

1. `400` 유효성 오류
2. `401` 인증 필요/만료
3. `403` 권한 없음
4. `404` 리소스 없음
5. `409` 동기화 충돌
6. `500` 서버 내부 오류

### 2.5 페이지네이션

- 현재 카탈로그 API는 `page`, `page_size`를 사용한다.
- 응답 표준 형식:

```json
{
  "items": [],
  "page": 1,
  "page_size": 60,
  "total": 0,
  "has_more": false
}
```

확인 필요:

1. 현재 모든 목록 API가 위 구조를 동일하게 쓰는지
2. iOS 앱에서 cursor 방식이 더 나은지

### 2.6 캐시 힌트

정의 필요:

1. ETag 지원 여부
2. Last-Modified 지원 여부
3. 응답별 TTL 힌트 제공 여부
4. 이미지 캐시 만료 정책

## 3. 홈 API

### 3.1 홈 요약

- Method: `GET`
- Path: `/api/home/summary`
- 목적: 홈 상단 요약 데이터 조회

쿼리 파라미터:
- 없음

응답 예시:

```json
{
  "island_profile": {},
  "players": [],
  "calendar_summary": {},
  "catalog_summary": {}
}
```

정의 필요:

1. 홈에서 반드시 필요한 필드만 남길지
2. null 가능 필드를 어떻게 표준화할지

### 3.2 현재 잡을 수 있는 생물

- Method: `GET`
- Path: `/api/home/creatures-now`

쿼리 파라미터:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `catalog_type` | string | N | `all`, `bugs`, `fish`, `sea` 등 |
| `owned` | bool | N | 보유 상태 필터 |
| `donated` | bool | N | 기증 상태 필터 |

응답 예시:

```json
{
  "items": []
}
```

## 4. 주민 API

### 4.1 주민 목록

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
  "items": [
    {
      "id": "string",
      "name": "string",
      "species": "string",
      "personality": "string",
      "image_url": "string",
      "liked": false,
      "on_island": false,
      "former_resident": false
    }
  ]
}
```

정의 필요:

1. 정렬 기준이 서버 기본인지 앱 정렬인지
2. 상세 API가 필요한지 여부

### 4.2 주민 상태 수정

- Method: `POST`
- Path: `/api/villagers/{villager_id}/state`

요청 예시:

```json
{
  "liked": true,
  "on_island": false,
  "camping_visited": false,
  "former_resident": false
}
```

응답 예시:

```json
{
  "villager_id": "string",
  "liked": true,
  "on_island": false,
  "camping_visited": false,
  "former_resident": false
}
```

### 4.3 섬 주민 순서 변경

- Method: `POST`
- Path: `/api/villagers/island-order`

요청 예시:

```json
{
  "villager_ids": ["a", "b", "c"]
}
```

## 5. 카탈로그 API

### 5.1 카탈로그 메타

- Method: `GET`
- Path: `/api/catalog/{catalog_type}/meta`

목적:
- 필터 목록, 카테고리, 정렬 기준 등 앱이 목록 화면을 구성하는 데 필요한 메타 데이터 조회

### 5.2 카탈로그 목록

- Method: `GET`
- Path: `/api/catalog/{catalog_type}`

쿼리 파라미터:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `q` | string | N | 검색어 |
| `category` | string | N | 카테고리 |
| `style` | string | N | 의류 스타일 |
| `label_theme` | string | N | 의류 라벨 테마 |
| `event_type` | string | N | 이벤트 타입 |
| `fake_state` | string | N | 미술품 진위 필터 |
| `owned` | bool | N | 보유 여부 |
| `variation_scope` | string | N | 변형 기준 조회 범위 |
| `sort_by` | string | N | 정렬 키 |
| `sort_order` | string | N | `asc` or `desc` |
| `page` | int | N | 페이지 번호 |
| `page_size` | int | N | 페이지 크기 |

응답 예시:

```json
{
  "items": [
    {
      "id": "string",
      "name": "string",
      "image_url": "string",
      "owned": false,
      "donated": false,
      "quantity": 0
    }
  ],
  "page": 1,
  "page_size": 60,
  "total": 0,
  "has_more": false
}
```

정의 필요:

1. 목록 셀에 필요한 최소 필드 집합
2. 앱에서 정렬/필터 일부를 로컬에서 처리할지 여부

### 5.3 카탈로그 상세

- Method: `GET`
- Path: `/api/catalog/{catalog_type}/{item_id}/detail`

응답 예시:

```json
{
  "id": "string",
  "name": "string",
  "image_url": "string",
  "owned": false,
  "donated": false,
  "quantity": 0,
  "variations": []
}
```

정의 필요:

1. 앱 상세 화면에 필요한 필드만 고정
2. 미술품, 생물, 음악처럼 카테고리별 차이 필드를 어떻게 다룰지

### 5.4 카탈로그 상태 수정

- Method: `POST`
- Path: `/api/catalog/{catalog_type}/{item_id}/state`

요청 예시:

```json
{
  "owned": true,
  "donated": false,
  "quantity": 1
}
```

### 5.5 카탈로그 벌크 수정

- Method: `POST`
- Path: `/api/catalog/{catalog_type}/state/bulk`

요청 예시:

```json
{
  "item_ids": ["a", "b", "c"],
  "owned": true
}
```

주의:
- 모바일 UX에서 실제로 필요한지 PRD에서 먼저 결정한다.

### 5.6 변형 상태 수정

- Method: `POST`
- Path: `/api/catalog/{catalog_type}/{item_id}/variations/{variation_id}/state`

요청 예시:

```json
{
  "owned": true,
  "quantity": 1
}
```

### 5.7 변형 상태 일괄 수정

- Method: `POST`
- Path: `/api/catalog/{catalog_type}/{item_id}/variations/state`

요청 예시:

```json
{
  "items": [
    { "variation_id": "red", "owned": true, "quantity": 1 }
  ]
}
```

## 6. 프로필/플레이어 API

### 6.1 섬 프로필 조회

- Method: `GET`
- Path: `/api/profile`

### 6.2 섬 프로필 수정

- Method: `POST`
- Path: `/api/profile`

요청 필드 예시:

```json
{
  "island_name": "string",
  "nickname": "string",
  "representative_fruit": "apple",
  "representative_flower": "rose",
  "birthday": "03-12",
  "hemisphere": "north",
  "time_travel_enabled": false,
  "game_datetime": "2026-03-12T09:00:00"
}
```

### 6.3 플레이어 목록

- Method: `GET`
- Path: `/api/players`

### 6.4 플레이어 저장

- Method: `POST`
- Path: `/api/players`

### 6.5 대표 플레이어 설정

- Method: `POST`
- Path: `/api/players/{player_id}/main`

### 6.6 플레이어 삭제

- Method: `DELETE`
- Path: `/api/players/{player_id}`

## 7. 캘린더 API

### 7.1 월별 일정 목록

- Method: `GET`
- Path: `/api/calendar`

쿼리 파라미터:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `month` | string | Y | `YYYY-MM` |

### 7.2 월별 주석/뱃지

- Method: `GET`
- Path: `/api/calendar/annotations`

### 7.3 일자별 일정

- Method: `GET`
- Path: `/api/calendar/day`

쿼리 파라미터:

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `date` | string | Y | `YYYY-MM-DD` |

### 7.4 일정 저장

- Method: `POST`
- Path: `/api/calendar`

요청 예시:

```json
{
  "id": 1,
  "visit_date": "2026-03-12",
  "npc_name": "K.K.",
  "note": "string",
  "checked": false
}
```

### 7.5 일정 체크 상태 변경

- Method: `POST`
- Path: `/api/calendar/{entry_id}/checked`

### 7.6 일정 삭제

- Method: `DELETE`
- Path: `/api/calendar/{entry_id}`

## 8. 오프라인/동기화 고려사항

정의 필요:

1. 오프라인 수정 요청이 실패했을 때 앱이 어떤 로컬 상태를 유지하는지
2. 재전송 성공 후 서버 응답을 어떤 방식으로 병합하는지
3. `409 Conflict` 발생 조건을 둘지
4. 각 상태 수정 API에 `updated_at` 또는 `version` 필드가 필요한지

## 9. App Store 제출 전 API 체크리스트

- [ ] 인증 없는 쓰기 API 공개 범위 결정
- [ ] 에러 메시지 사용자 노출 문구 정리
- [ ] 응답 필드 null/빈배열/빈문자열 규칙 통일
- [ ] 날짜/시간 표준 타임존 규칙 정의
- [ ] 이미지 URL가 HTTPS만 사용하는지 확인
- [ ] 레이트리밋 또는 악용 방지 정책 검토
