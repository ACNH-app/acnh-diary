# Flutter 성능 예산 및 관측성

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`

## 1. 목표

1. 중급 모바일 기기에서 부드러운 목록 스크롤을 유지한다.
2. 첫 진입과 상세 전환의 체감 지연을 낮춘다.
3. 성능 저하를 조기에 감지할 수 있게 관측 지표를 정의한다.

## 2. 성능 예산

1. 앱 콜드 스타트 첫 콘텐츠 표시: `2.5s` 이내
2. 탭 전환: `300ms` 이내
3. 목록 추가 페이지 로드 후 셀 표시: `1.0s` 이내
4. 상세 화면 전환: `500ms` 이내
5. 스크롤 중 dropped frame: 주요 목록에서 체감상 없거나 매우 낮음

## 3. 주의 구간

1. 대량 이미지 리스트
2. 카탈로그 상세의 variation 렌더링
3. 월간 캘린더 annotation 계산
4. 앱 복귀 시 동시 재검증 요청

## 4. 대응 전략

1. 이미지 썸네일 우선 로드
2. pagination page size 고정 유지
3. 불필요한 provider 재계산 최소화
4. 상세에서 무거운 가공은 isolate 또는 사전 정규화 검토

## 5. 측정 지표

1. API latency
2. cache hit ratio
3. image load failure rate
4. sync queue backlog
5. screen render time
