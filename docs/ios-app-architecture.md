# iOS 앱 아키텍처 설계

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`
- 목적: 현재 FastAPI 백엔드를 사용하는 iPhone 앱의 기본 구조를 정의한다.

## 1. 아키텍처 원칙

1. 서버 계약과 앱 UI를 분리한다.
2. 서버 응답을 그대로 뷰에 바인딩하지 않고 앱 전용 DTO와 ViewModel을 둔다.
3. 읽기 캐시와 쓰기 작업을 분리한다.
4. 인증은 1차 출시에서 쓰지 않더라도 나중에 붙일 수 있게 구조를 열어둔다.

## 2. 권장 기술 스택

1. UI: `SwiftUI`
2. 네비게이션: `NavigationStack` + `TabView`
3. 비동기: `async/await`
4. 네트워크: `URLSession`
5. 로컬 저장:
- 메타/응답 캐시: 파일 캐시 또는 SQLite 기반 경량 저장
- 사용자 설정: `UserDefaults`
- 인증 토큰(차기): `Keychain`
6. 이미지 캐시: `Nuke` 또는 동급 라이브러리 권장

## 3. 계층 구조

### 3.1 App Layer

역할:

1. 앱 시작
2. 환경 설정 주입
3. 탭 구조 초기화
4. 공통 의존성 구성

구성 예시:

1. `App`
2. `AppEnvironment`
3. `AppRouter`

### 3.2 Feature Layer

각 기능을 독립 feature로 둔다.

1. `HomeFeature`
2. `VillagersFeature`
3. `CatalogFeature`
4. `CalendarFeature`
5. `SettingsFeature`

각 feature 내부 구성:

1. `View`
2. `ViewModel`
3. `UseCase` 또는 `Action`
4. `Repository` 인터페이스 사용

### 3.3 Data Layer

역할:

1. API 호출
2. 응답 디코딩
3. 캐시 읽기/쓰기
4. 오프라인 동기화 큐 처리

구성 예시:

1. `APIClient`
2. `Repositories`
3. `CacheStore`
4. `SyncQueueStore`

## 4. 모듈 경계

### 4.1 공통 Core

공통으로 두는 항목:

1. API 클라이언트
2. 에러 타입
3. 날짜 포맷터
4. 이미지 로더
5. 환경 설정
6. 로깅/분석 인터페이스

### 4.2 Feature별 도메인 분리

1. 홈은 요약과 빠른 진입만 담당
2. 주민은 필터/상태 변경/섬 주민 순서 담당
3. 카탈로그는 타입 선택/목록/상세/변형 상태 담당
4. 일정은 월간/일자별 조회와 편집 담당
5. 설정은 섬 프로필/플레이어/앱 설정 담당

## 5. 데이터 흐름

기본 읽기 흐름:

1. View가 ViewModel에 로드 요청
2. ViewModel이 Repository 호출
3. Repository가 캐시 우선 또는 네트워크 우선 정책 적용
4. 응답을 앱 모델로 변환
5. ViewModel이 UI 상태 갱신

기본 쓰기 흐름:

1. View가 수정 액션 전달
2. ViewModel이 optimistic update 여부 결정
3. Repository가 네트워크 전송
4. 성공 시 로컬 캐시 갱신
5. 실패 시 롤백 또는 오류 상태 표시

## 6. 화면 상태 모델

모든 주요 화면은 공통적으로 아래 상태를 가진다.

1. `idle`
2. `loading`
3. `loaded`
4. `empty`
5. `error`

추가 상태:

1. `refreshing`
2. `paging`
3. `saving`
4. `syncPending`

## 7. Repository 설계

필수 Repository:

1. `HomeRepository`
2. `VillagerRepository`
3. `CatalogRepository`
4. `ProfileRepository`
5. `CalendarRepository`
6. `PlayerRepository`
7. `ImageCacheRepository`
8. `SyncQueueRepository`

원칙:

1. ViewModel은 API path를 모르게 한다.
2. Repository가 서버 DTO와 앱 모델 매핑을 담당한다.

## 8. 캐시 전략

1. 홈: 마지막 성공 응답 1개 보관
2. 주민 목록: 필터 없는 기본 목록 + 마지막 조회 결과 캐시
3. 카탈로그 목록: 타입별 첫 페이지와 마지막 상세 응답 캐시
4. 상세: 최근 본 항목 N개 보관

## 9. 향후 인증 확장 포인트

1. `APIClient`에 인증 헤더 provider 추가
2. `AuthSessionStore` 추가
3. 401 처리 interceptor 추가
4. 앱 시작 시 세션 복원 로직 추가

## 10. 권장 폴더 구조

```text
App/
Core/
  API/
  Cache/
  Config/
  DesignSystem/
  Utils/
Features/
  Home/
  Villagers/
  Catalog/
  Calendar/
  Settings/
Resources/
```
