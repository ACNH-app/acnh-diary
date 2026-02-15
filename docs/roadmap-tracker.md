# ACNH 확장 로드맵 트래커

기준 문서: `docs/scaling-and-auth-roadmap.md`

## 사용 규칙

1. 작업 시작 시 `- [ ]`를 `- [~]`로 변경
2. 완료 시 `- [x]`로 변경
3. 이슈/결정사항은 각 Phase 하단에 날짜와 함께 기록

---

## 공통 메타

- 목표 릴리즈: `TBD`
- 현재 상태: `준비중`
- 담당자: `TBD`
- 시작일: `TBD`
- 목표 완료일: `TBD`

---

## Phase A. 현행 안정화

### 작업 항목

- [ ] A-01 성능 계측 포인트 정의 (API/화면 전환/상세 모달)
- [ ] A-02 응답시간 기준선(p50/p95) 측정 스크립트 추가
- [ ] A-03 회귀 스모크 테스트 케이스 확정
- [ ] A-04 정적 캐시 버전 정책 문서화
- [ ] A-05 `docs/performance-baseline.md` 작성
- [ ] A-06 `docs/release-checklist.md` 작성

### 완료 기준

- [ ] A-DONE-01 느린 API/화면 Top 5 식별
- [ ] A-DONE-02 릴리즈 전 체크리스트로 회귀 점검 가능

### 메모

- `YYYY-MM-DD`: 

---

## Phase B. 데이터 계층 강화

### 작업 항목

- [ ] B-01 Nookipedia 동기화 배치 설계
- [ ] B-02 카탈로그 정규화 스키마 설계
- [ ] B-03 조회 로직 로컬 DB 우선 전환
- [ ] B-04 동기화 실패 시 last-good-snapshot 복원 로직 구현
- [ ] B-05 동기화 스크립트/잡 추가 (`scripts/sync_nookipedia.py` 또는 동등 모듈)
- [ ] B-06 `docs/data-sync-design.md` 작성

### 완료 기준

- [ ] B-DONE-01 주요 조회 API에서 외부 API 직접 의존 제거
- [ ] B-DONE-02 동기화 실패 시에도 서비스 조회 기능 정상

### 메모

- `YYYY-MM-DD`: 

---

## Phase C. 인증/멀티유저

### 작업 항목

- [ ] C-01 PostgreSQL 전환 계획 확정
- [ ] C-02 사용자 테이블(`users`) 및 인증 스키마 도입
- [ ] C-03 비밀번호 해시/인증 토큰 정책 적용
- [ ] C-04 상태성 테이블에 `user_id` 스코프 추가
- [ ] C-05 API 인증/권한 미들웨어 적용
- [ ] C-06 기존 데이터 마이그레이션(dry-run 포함)
- [ ] C-07 `docs/auth-model.md` 작성
- [ ] C-08 `docs/db-migration-plan.md` 작성

### 완료 기준

- [ ] C-DONE-01 사용자 A/B 데이터 완전 분리 검증
- [ ] C-DONE-02 인증 없는 상태 변경 API 차단 검증
- [ ] C-DONE-03 로그인/로그아웃/세션 만료 시나리오 통과

### 메모

- `YYYY-MM-DD`: 

---

## Phase D. URL 라우팅/UX 정합성

### 작업 항목

- [ ] D-01 라우팅 방식 결정 (hash/history)
- [ ] D-02 모드별 URL 매핑 (`/home`, `/villagers`, `/catalog/:type`)
- [ ] D-03 필터/정렬/탭 상태 URL 동기화
- [ ] D-04 새로고침 상태 복원 구현
- [ ] D-05 상세 모달 deep-link 정책 반영
- [ ] D-06 `docs/routing-spec.md` 작성

### 완료 기준

- [ ] D-DONE-01 URL 공유/북마크로 동일 화면 재현
- [ ] D-DONE-02 브라우저 뒤로가기/앞으로가기 정상 동작

### 메모

- `YYYY-MM-DD`: 

---

## Phase E. 배포/운영

### 작업 항목

- [ ] E-01 dev/staging/prod 환경 분리
- [ ] E-02 CI 파이프라인 (lint/test/build/deploy) 구축
- [ ] E-03 모니터링/알림 구성 (에러율/지연시간/동기화 실패)
- [ ] E-04 DB 백업/복구 정책 구현
- [ ] E-05 보안 점검 (CORS, rate limit, secret, 보안 헤더)
- [ ] E-06 `docs/deployment-runbook.md` 작성
- [ ] E-07 `docs/incident-playbook.md` 작성

### 완료 기준

- [ ] E-DONE-01 스테이징 자동 배포 가능
- [ ] E-DONE-02 백업 복구 리허설 완료

### 메모

- `YYYY-MM-DD`: 

---

## 릴리즈 게이트 (최종)

- [ ] G-01 PostgreSQL + user_id 스코프 기반 데이터 분리 완료
- [ ] G-02 인증/권한 정책 운영 수준 검증 완료
- [ ] G-03 URL 라우팅/상태 복원 기능 검증 완료
- [ ] G-04 운영 체계(CI/CD/모니터링/백업) 검증 완료

최종 판정:

- [ ] 배포 가능
- [ ] 배포 보류

판정 일시: `TBD`
판정자: `TBD`
