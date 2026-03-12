# Flutter 로컬 데이터 아키텍처

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`

## 1. 목표

1. 앱 서버 없이도 전체 핵심 기능이 동작해야 한다.
2. 콘텐츠 데이터와 사용자 상태 데이터를 분리한다.
3. 앱 업데이트 시 사용자 상태가 유지되어야 한다.

## 2. 저장소 구조

1. `content.db`
- 주민, 카탈로그, 이벤트, 메타 데이터 저장
- 앱 번들 포함
- 읽기 전용

2. `app.db`
- 주민 상태, 카탈로그 보유 상태, 일정, 프로필, 플레이어, 앱 설정 저장
- 로컬 쓰기 가능

3. `secure storage`
- 광고 제거 entitlement 캐시
- 스토어 복구 관련 최소 플래그

## 3. Repository 구조

1. `ContentRepository`
- 번들 데이터 조회

2. `StateRepository`
- 사용자 상태 CRUD

3. `PremiumRepository`
- 광고 제거 여부 확인
- 구매 복구 상태 반영

## 4. 데이터 흐름

1. 앱 시작
- `content.db` 오픈
- `app.db` 마이그레이션
- premium 상태 확인

2. 목록/상세 조회
- `content.db` 조회
- 필요 시 `app.db` 상태 조인

3. 상태 변경
- `app.db` 즉시 저장
- UI 즉시 반영

## 5. 마이그레이션 규칙

1. 콘텐츠 스키마와 상태 스키마는 독립 버전 관리
2. 콘텐츠 항목 ID는 최대한 안정적으로 유지
3. 삭제된 항목은 숨김 처리 또는 orphan mapping 정책 적용
4. 마이그레이션 실패 시 백업 후 복구 경로 제공

## 6. 구현 권장

1. 대용량 읽기에는 SQLite 계열 우선 검토
2. feature별 DAO 또는 datasource로 테이블 접근 분리
3. Riverpod provider는 repository만 의존하게 유지

## 7. 비범위

1. 실시간 서버 동기화
2. 원격 사용자 계정
3. 클라우드 백업
