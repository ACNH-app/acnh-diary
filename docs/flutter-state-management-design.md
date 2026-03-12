# Flutter 상태관리 설계

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`
- 권장 상태관리: `Riverpod`

## 1. 목표

1. 네트워크 상태와 UI 상태를 분리한다.
2. feature 단위로 provider 경계를 명확히 한다.
3. 목록/상세/수정 작업 간 캐시 정합성을 유지한다.

## 2. 상태 분류

1. 서버 상태: API에서 읽어오는 목록, 상세, 메타, 프로필, 일정
2. 세션 상태: 현재 환경, base URL, 앱 설정, 캐시 정책
3. 화면 상태: 검색어, 필터, 정렬, 탭 인덱스, 선택 날짜
4. 작업 상태: 저장 중, 삭제 중, 동기화 대기열 상태

## 3. Provider 구조

```text
appConfigProvider
dioProvider
apiClientProvider
databaseProvider
syncQueueProvider

homeSummaryProvider
homeCreaturesNowProvider

villagerQueryStateProvider
villagerListProvider
villagerDetailProvider(id)
villagerMutationProvider

catalogTypeProvider
catalogQueryStateProvider(type)
catalogListProvider(type)
catalogDetailProvider(type, id)
catalogMutationProvider

calendarMonthProvider(month)
calendarDayProvider(date)
calendarMutationProvider

profileProvider
playersProvider
settingsProvider
```

## 4. 상태 객체 규칙

1. 검색/필터/정렬은 `freezed` 기반 immutable query object로 관리한다.
2. 목록 provider는 query object를 key로 사용한다.
3. 상세 provider는 `type + id` 조합으로 식별한다.
4. mutation provider는 성공 시 관련 query cache만 무효화한다.

## 5. 목록 갱신 정책

1. 첫 진입: 로컬 캐시 반환 후 서버 재검증
2. pull-to-refresh: 서버 강제 재요청
3. 필터 변경: 목록 초기화 후 첫 페이지부터 다시 로드
4. pagination: 다음 페이지 요청 중 기존 아이템 유지

## 6. Mutation 정책

1. 주민 거주 여부, 카탈로그 보유 상태, 일정 체크는 optimistic update 허용
2. 플레이어 삭제, 섬 주민 순서 재정렬은 서버 성공 후 UI 확정
3. 4xx 응답은 즉시 rollback
4. 네트워크 오류는 rollback 후 재시도 UI 제공

## 7. 캐시 무효화 규칙

1. 주민 상태 변경 후:
   - `villagerListProvider`
   - `villagerDetailProvider(id)`
   - `homeSummaryProvider`
2. 카탈로그 상태 변경 후:
   - 현재 `catalogListProvider(type, query)`
   - `catalogDetailProvider(type, id)`
   - 관련 타입 메타가 상태 카운트를 갖는 경우 메타도 무효화
3. 일정 변경 후:
   - 해당 월 annotations
   - 해당 날짜 상세
   - 홈 요약
4. 프로필/플레이어 변경 후:
   - `profileProvider`
   - `playersProvider`
   - 홈 요약

## 8. 실무 권장 구현

1. 읽기 계층은 `AsyncNotifier` 또는 `FutureProvider.family`
2. 변경 작업은 `Notifier` 기반 action controller
3. 스크롤 위치 보존은 `AutomaticKeepAliveClientMixin`과 route-level state restoration 사용
4. 화면 일시 상태는 provider보다 위젯 로컬 상태를 우선한다.

## 9. 에러 전파 규칙

1. 전역 provider에서 사용자 문구를 만들지 않는다.
2. provider는 `AppError`를 던지고 UI가 문구를 결정한다.
3. 저장 에러는 가능한 한 전역 다이얼로그 대신 셀 또는 시트 근처에 표시한다.

## 10. 폴더 예시

```text
lib/features/catalog/
  application/
    catalog_query_state.dart
    catalog_list_controller.dart
    catalog_detail_controller.dart
    catalog_mutation_controller.dart
  data/
  domain/
  presentation/
```
