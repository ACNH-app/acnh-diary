# Flutter 네비게이션 및 라우팅 설계

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`
- 권장 라우터: `go_router`

## 1. 목표

1. 탭별 독립 navigation stack을 유지한다.
2. 상세 화면 deep link를 허용한다.
3. 모바일 뒤로가기 동작을 예측 가능하게 만든다.

## 2. 라우팅 원칙

1. 하단 탭은 `StatefulShellRoute`로 구성한다.
2. 각 탭은 자체 navigator key를 가진다.
3. 상세 화면은 탭 스택 위에 push한다.
4. 전역 모달은 root navigator를 사용한다.

## 3. 루트 구조

```text
/
  home
  villagers
  catalog
  calendar
  settings
```

## 4. 상세 라우트

```text
/villagers/:id
/catalog/:type
/catalog/:type/:id
/calendar/day/:date
/settings/players
/settings/profile
```

## 5. 탭별 정책

1. 홈 탭
   - 홈 카드에서 다른 탭 상세로 이동 가능
   - 이동 시 대상 탭 stack으로 전환 후 상세 push
2. 주민 탭
   - 목록 -> 상세
   - 상세 내 상태 편집 시 바텀시트 사용
3. 카탈로그 탭
   - 타입 루트 -> 목록 -> 상세
   - 필터는 route query parameter로 일부 반영 가능
4. 일정 탭
   - 월간 -> 날짜 상세
   - 일정 생성/수정은 modal route
5. 설정 탭
   - 하위 관리 화면을 일반 push route로 사용

## 6. Query Parameter 정책

1. 공유 가치가 있는 상태만 URL에 반영한다.
2. 추천 대상:
   - `catalog type`
   - `search query`
   - `category`
   - `sort`
   - `selected date`
3. URL이 과도하게 길어지는 복합 필터는 메모리 상태로 유지한다.

## 7. Deep Link 정책

1. 주민 상세, 카탈로그 상세, 특정 날짜 상세를 우선 지원한다.
2. 앱 최초 진입 deep link는 필요한 상위 stack을 자동 구성한다.
3. 로컬 캐시가 있으면 먼저 그리고 서버 데이터를 재검증한다.

## 8. 뒤로가기 규칙

1. 상세 화면에서는 직전 화면으로 pop
2. 탭 루트에서 뒤로가기:
   - Android: 첫 탭이 아니면 홈 탭으로 이동하지 않고 현재 탭 종료 정책을 따른다.
   - iOS: 시스템 back gesture만 처리
3. 확인이 필요한 편집 시트는 unsaved changes 다이얼로그 표시

## 9. 상태 복원

1. 선택 탭 인덱스 복원
2. 주민/카탈로그 목록 스크롤 복원
3. 일정 탭 선택 월/일자 복원
4. 앱 강제 종료 후에도 마지막 탭을 열지 여부는 설정 가능 항목으로 두지 않고 기본 복원 사용

## 10. 구현 메모

1. 탭별 navigator key는 `app_router.dart`에 집중 관리
2. route 이름은 문자열 상수 또는 typed route로 선언
3. analytics screen event는 route observer가 아니라 `go_router` listener에서 수집
