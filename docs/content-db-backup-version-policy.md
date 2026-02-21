# content/app DB 백업 및 버전 정책

## 1) 범위
- 콘텐츠 데이터:
  - `content.db`
  - `data/content_full_snapshot.json` (선택)
  - 매핑 JSON(`data/*_name_map_ko.json`, 기타 매핑 파일)
- 사용자 상태 데이터:
  - `app.db`

## 2) 백업 주기
- 개발/로컬 운영:
  - 작업 종료 시 1회 수동 백업
- 운영 배포 전:
  - 배포 직전 전체 백업 1회
  - 배포 직후 헬스체크 통과본 백업 1회
- 정기 백업(권장):
  - 일 1회 증분
  - 주 1회 전체

## 3) 보관 정책
- 일간 백업: 최근 14일 보관
- 주간 백업: 최근 8주 보관
- 월간 백업: 최근 6개월 보관
- 긴급 장애 시점 백업: 별도 태그로 30일 보관

## 4) 버전 규칙
- 콘텐츠 빌드 버전:
  - `content_version` 테이블의 `built_at_utc`를 기준으로 관리
- 파일 태그 형식(권장):
  - `content-YYYYMMDD-HHMM`
  - `state-YYYYMMDD-HHMM`
- 릴리즈 노트에는 아래를 같이 기록:
  - `USE_CONTENT_DB` 값
  - 빌드 명령
  - 헬스체크 결과(`scripts/content_db_healthcheck.py`)

## 5) 백업 절차(권장)
1. 서버 쓰기 부하가 낮은 시점 확보
2. 아래 파일 사본 생성
   - `content.db`
   - `app.db`
   - `data/content_full_snapshot.json`(있으면)
   - `data/*_map*.json`
3. 체크섬 생성(예: `shasum -a 256`)
4. 백업 위치에 업로드 후 체크섬 검증

## 6) 복구 절차
1. 앱 중지
2. 현재 DB를 안전 위치로 이동(롤백 대비)
3. 백업 파일 복원
4. 앱 기동
5. 검증 실행
   - `./.venv/bin/python scripts/content_db_healthcheck.py`
6. 실패 시 `USE_CONTENT_DB=0`로 즉시 전환 (`docs/content-db-rollback.md`)

## 7) 복구 점검(드릴)
- 최소 월 1회 복구 리허설
- 점검 항목:
  - `/api/catalog/*` 목록/상세 응답
  - 보유/미보유 상태 반영
  - 모바일 핵심 화면 진입

## 8) 주의사항
- `app.db-wal`, `app.db-shm`는 런타임 파일이므로 백업에서 제외 권장
- 백업 파일을 Git에 커밋하지 않음
- 복구 후 캐시 불일치가 의심되면 서버 재시작으로 프로세스 캐시 초기화
