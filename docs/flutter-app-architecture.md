# Flutter 앱 아키텍처 설계

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`

## 1. 원칙

1. 공통 모바일 코드베이스 유지
2. 서버 DTO와 UI 모델 분리
3. 읽기 캐시와 쓰기 작업 분리
4. 향후 인증 추가 가능하도록 구조 개방

## 2. 권장 스택

1. UI: `Flutter`
2. 상태관리: `Riverpod` 권장
3. 네트워크: `Dio` 또는 `http`
4. 라우팅: `go_router`
5. 로컬 저장:
- 간단 설정: `shared_preferences`
- 민감 정보: `flutter_secure_storage`
- 캐시/큐: `sqflite` 또는 `isar`
6. 이미지 캐시: `cached_network_image`

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
- dto
- repository impl
- cache store

## 4. feature 구분

1. home
2. villagers
3. catalog
4. calendar
5. settings

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
```
