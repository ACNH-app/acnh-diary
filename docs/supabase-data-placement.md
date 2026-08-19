# Supabase Data Placement

기준 날짜: 2026-08-18

## 로컬에 남길 것

- `data/*.json`
  - 번역 맵, 빌드 보조 데이터, 원본 스냅샷
  - 이유: 빌드 입력값이고 배포 런타임에서 자주 바뀌지 않음
- `scripts/*`
  - Nookipedia 수집, content DB 생성, asset inventory/export 도구
  - 이유: 운영 데이터가 아니라 제작 파이프라인
- `content.db`
  - 기본 권장: 개발/로컬 fallback용으로 유지
  - 이유: 가장 빠른 읽기 경로이며 Supabase 장애 시 로컬 fallback 가능

## Supabase로 옮길 것

- `app.db`의 상태성 테이블 전체
  - `island`
  - `island_profile`
  - `villager_state`
  - `catalog_state`
  - `catalog_variation_state`
  - `calendar_entry`
  - `player_profile`
- `content.db`의 런타임 조회 테이블
  - `catalog_items`
  - `catalog_variations`
  - `villagers`
  - `catalog_meta`
  - `content_version`
  - `recipe_tags`
  - `recipe_tag_links`
- 이미지 자산
  - `static/assets/music/**`
  - `static/assets/offline/_url_cache/**`
  - `static/assets/offline/catalog/**`
  - `static/assets/offline/variations/**`
  - `static/assets/offline/villagers/**`
  - `villagers/**`

## 권장 운영 구조

- 개발 환경
  - `content.db` 로컬 유지
  - `app.db` 로컬 유지
  - `ASSET_BACKEND=local`
- 프로덕션 환경
  - 상태 데이터는 Supabase Postgres
  - 읽기 전용 콘텐츠는 Supabase Postgres 또는 `content.db` 중 택1
  - 이미지 자산은 Supabase Storage
  - `ASSET_BACKEND=supabase`

## 이미지 URL 치환 규칙

- `/static/assets/music/123.png`
  - `music/123.png`
- `/static/assets/offline/_url_cache/<sha>.<ext>`
  - `remote-cache/<sha>.<ext>`
- `/static/assets/offline/catalog/...`
  - `catalog/...`
- `/static/assets/offline/variations/...`
  - `variations/...`
- `/static/assets/offline/villagers/...`
  - `villagers/...`
- 외부 원격 URL(`https://...`)
  - `remote-cache/<sha256(url)>.<ext>`

런타임에서는 `app/services/asset_urls.py`가 위 규칙으로 Storage public URL로 바꿉니다.

## 적용된 코드

- 이미지 URL 해석 레이어 추가
  - `app/services/asset_urls.py`
- 데이터 로더에서 이미지 URL 자동 치환
  - `app/services/catalog_data.py`
- Supabase 자산 관련 환경변수 추가
  - `.env.example`
  - `app/core/config.py`
- Supabase 업로드/시드 준비 스크립트 추가
  - `scripts/upload_supabase_assets.py`
  - `scripts/export_supabase_seed.py`
  - `scripts/import_supabase_seed.py`
  - `scripts/supabase_state_schema.sql`
  - `scripts/supabase_content_schema.sql`
