# 로컬 콘텐츠 DB 전환 체크리스트

## 0. 준비/정의
- [x] 목표 확정: 외부 API 비의존 + 로컬 콘텐츠 DB 사용
- [x] 현재 데이터 원천/매핑/가공 경로 점검
- [x] 계획 문서 작성 (`docs/local-content-db-plan.md`)

## 1. 스키마/빌드 기반
- [x] `content.db` 파일 경로/설정 추가
- [x] `catalog_items` 스키마 정의
- [x] `catalog_variations` 스키마 정의
- [x] `villagers` 스키마 정의
- [x] `catalog_meta`, `content_version` 스키마 정의
- [x] 인덱스 설계(카테고리/검색/정렬)

## 2. 데이터 빌드 파이프라인
- [x] 빌드 스크립트 추가 (`scripts/build_content_db.py`)
- [x] 로컬 JSON 적재 로직 구현
- [x] 한글 매핑 적용 로직 통합
- [x] 출처/카테고리 정규화 통합
- [x] 이미지 URL 컬럼 저장
- [x] 빌드 결과 건수 리포트 출력

## 3. 서비스 전환
- [x] catalog 목록 조회를 `content.db`로 전환
- [x] 상세/변형 조회를 `content.db`로 전환
- [x] villagers 조회를 `content.db`로 전환
- [x] 기존 `app.db` 상태 결합 로직 호환 확인

## 4. 검증
- [x] 카테고리별 건수 비교 스크립트 (`scripts/compare_content_counts.py`)
- [x] 필터/정렬/검색 회귀 테스트 (`scripts/compare_catalog_queries.py`)
- [x] 모바일/아이패드 성능 체크(백엔드 응답시간 기준 벤치마크: `scripts/benchmark_catalog_latency.py`)
- [x] 실패 시 롤백 경로 확인 (`docs/content-db-rollback.md`)

## 5. 운영
- [x] 재빌드 명령 문서화 (`docs/content-db-operations.md`)
- [x] 배포 시 포함 파일 정리(`content.db`, 이미지 자산) (`docs/content-db-operations.md`)
- [x] 백업/버전 정책 문서화 (`docs/content-db-backup-version-policy.md`)
