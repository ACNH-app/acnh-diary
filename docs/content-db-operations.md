# content.db 운영 가이드

## 1) 기본 개념
- `content.db`: 읽기 전용 성격의 콘텐츠 DB(카탈로그/주민/변형 데이터)
- `app.db`: 사용자 상태 DB(보유/기증/수량/프로필/캘린더)

## 2) 전환 플래그
- `USE_CONTENT_DB=1`: 무조건 `content.db` 사용
- `USE_CONTENT_DB=0`: 기존 source loader 경로 사용
- `USE_CONTENT_DB=auto`: `content.db`가 있으면 사용, 없으면 source loader

## 3) 빌드
- 스냅샷 갱신 + DB 재생성
```bash
python3 scripts/build_content_db.py --refresh-snapshot
```
- 기존 스냅샷으로만 DB 재생성
```bash
python3 scripts/build_content_db.py
```

## 4) 검증
- 건수 비교
```bash
python3 scripts/compare_content_counts.py
```
- 필터/정렬/검색 회귀
```bash
./.venv/bin/python scripts/compare_catalog_queries.py
```
- 응답시간 벤치마크
```bash
./.venv/bin/python scripts/benchmark_catalog_latency.py
```
- 원클릭 헬스체크
```bash
./.venv/bin/python scripts/content_db_healthcheck.py
```

## 5) 장애 대응
- 즉시 롤백: `USE_CONTENT_DB=0` 후 서버 재시작
- 상세 절차: `docs/content-db-rollback.md`

## 5.1) 백업/버전 정책
- 정책 문서: `docs/content-db-backup-version-policy.md`

## 6) 배포 체크포인트
1. `content.db` 파일 포함 여부
2. `data/content_full_snapshot.json` 포함 여부(선택)
3. `USE_CONTENT_DB` 운영값 확인
4. `scripts/content_db_healthcheck.py` 통과 확인
