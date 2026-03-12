# Flutter 앱 아키텍처 설계

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`

## 1. 원칙

1. 공통 모바일 코드베이스 유지
2. 로컬 저장 모델과 UI 모델 분리
3. 번들 콘텐츠와 사용자 상태 저장을 분리
4. 인증 없는 단일 디바이스 앱으로 단순하게 유지
5. 유료 기능은 광고 제거 entitlement만 관리

## 2. 권장 스택

1. UI: `Flutter`
2. 상태관리: `Riverpod` 권장
3. 로컬 DB: `isar` 또는 `sqflite`
4. 라우팅: `go_router`
5. 로컬 저장:
- 간단 설정: `shared_preferences`
- 구매 상태/민감 정보: `flutter_secure_storage`
- 앱 상태 DB: `sqflite` 또는 `isar`
6. 결제: `in_app_purchase`
7. 광고: `google_mobile_ads`
8. 이미지 캐시: 번들 자산 우선, 외부 URL 사용 시 `cached_network_image`

## 3. 계층 구조

1. `presentation`
- screen
- widget
- controller/viewmodel

2. `domain`
- entity
- repository interface
- usecase

3. `data`
- datasource
- local model
- repository impl
- local store
- purchase store

## 4. feature 구분

1. home
2. villagers
3. catalog
4. calendar
5. settings
6. premium

## 5. 권장 폴더 구조

```text
lib/
  app/
  core/
  features/
    home/
    villagers/
    catalog/
    calendar/
    settings/
    premium/
```

## 6. 데이터 소스 구분

1. `content datasource`
- 앱 번들에 포함된 정적 JSON 또는 SQLite
- 업데이트 전까지 읽기 전용

2. `state datasource`
- 주민 상태, 카탈로그 보유 여부, 일정, 프로필 저장
- 디바이스 로컬 쓰기 가능

3. `premium datasource`
- 스토어 구매 상태
- 광고 제거 여부만 저장
