# content.db 전환 롤백 가이드

## 목적
- `content.db` 전환 중 장애(응답 오류/데이터 불일치/성능 저하)가 발생했을 때 즉시 서비스 안정화

## 즉시 롤백
1. 서버 환경변수 설정:
   - `USE_CONTENT_DB=0`
2. 서버 재시작:
   - 예: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. 정상 확인:
   - `/api/catalog/recipes/meta`
   - `/api/catalog/recipes?page=1&page_size=60`
   - `/api/profile`

## 재적용(롤포워드)
1. 콘텐츠 DB 재빌드:
   - `python3 scripts/build_content_db.py --refresh-snapshot`
2. 건수 검증:
   - `python3 scripts/compare_content_counts.py`
3. 쿼리 회귀 검증:
   - `./.venv/bin/python scripts/compare_catalog_queries.py`
4. 성능 측정:
   - `./.venv/bin/python scripts/benchmark_catalog_latency.py`
5. 문제 없으면:
   - `USE_CONTENT_DB=1` 또는 `USE_CONTENT_DB=auto`로 전환 후 재시작

## 운영 권장값
- 안정화 단계: `USE_CONTENT_DB=1` 고정
- 장기 운영: `USE_CONTENT_DB=auto` (파일 존재 시 자동 사용)
- 장애 대응: 즉시 `USE_CONTENT_DB=0`
