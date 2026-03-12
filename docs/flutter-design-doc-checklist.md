# Flutter 앱 설계 문서 체크리스트

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`
- 목적: Flutter 모바일 앱 설계 문서를 순차적으로 작성하고 진행도를 관리한다.

## 1. 진행도 요약

- 전체 문서 수: `19`
- 초안 완료: `19`
- 진행률: `100%`

## 2. 문서 체크리스트

| 상태 | 우선순위 | 문서 | 경로 | 비고 |
| --- | --- | --- | --- | --- |
| [x] | P0 | 제품 요구사항(PRD) | `mobile-app-prd.md` | 1차 출시 범위 정의 |
| [x] | P0 | API 계약 | `mobile-api-spec.md` | 서버-앱 공통 계약 초안 |
| [x] | P0 | 앱 아키텍처 | `flutter-app-architecture.md` | 레이어/스택 초안 |
| [x] | P0 | 화면 흐름 | `mobile-screen-flow-spec.md` | 탭/기본 흐름 초안 |
| [x] | P0 | 화면별 UI 명세 | `flutter-ui-spec.md` | 화면별 상태/UI/액션 정의 |
| [x] | P0 | 상태관리 설계 | `flutter-state-management-design.md` | Riverpod 상태 구조/갱신 규칙 |
| [x] | P0 | 데이터 모델 설계 | `flutter-data-modeling.md` | DTO/도메인/UI 모델 분리 |
| [x] | P0 | 네비게이션/라우팅 설계 | `flutter-navigation-and-routing.md` | `go_router` 기준 라우트 정책 |
| [x] | P1 | 오프라인/동기화 설계 | `mobile-offline-sync-design.md` | 캐시/쓰기 큐 정책 |
| [x] | P1 | 네트워크/에러 처리 설계 | `flutter-network-and-error-handling.md` | 타임아웃/재시도/에러 UX |
| [x] | P1 | 디자인 시스템 | `flutter-design-system.md` | 토큰/컴포넌트/접근성 규칙 |
| [x] | P1 | 인증/세션 설계 | `flutter-auth-and-session-design.md` | 무인증 1차 정책과 확장 고려 |
| [x] | P1 | 배포/환경 계획 | `mobile-release-and-store-plan.md` | flavor/store 준비 |
| [x] | P1 | 로컬 데이터 아키텍처 | `flutter-local-data-architecture.md` | 콘텐츠 DB와 상태 DB 분리 |
| [x] | P1 | 유료/광고 정책 | `flutter-monetization-design.md` | 광고 제거 purchase 정책 |
| [x] | P2 | QA 시나리오 | `mobile-qa-scenarios.md` | 기능/회귀 테스트 시나리오 |
| [x] | P2 | 분석 이벤트 계획 | `mobile-analytics-event-plan.md` | 이벤트 수집 정의 |
| [x] | P2 | 위젯 테스트 전략 | `flutter-widget-test-plan.md` | 핵심 화면 테스트 범위 정의 |
| [x] | P2 | 성능 예산/관측성 | `flutter-performance-budget.md` | 성능 기준과 측정 지표 정의 |

## 3. 작성 순서

1. P0 문서 완성
2. 데이터 계약과 화면 설계 정렬
3. 캐시/에러/배포 문서 보완
4. 테스트/성능 문서 추가

## 4. 현재 단계 메모

1. 기존 모바일 문서는 방향성 초안 수준이라 세부 설계 문서로 보강했다.
2. 현재 설계 문서 초안 세트는 로컬 저장 + 무인증 + 광고 제거 유료 정책 기준으로 정렬되었다.
