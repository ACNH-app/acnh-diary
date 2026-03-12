# 모바일 오프라인 데이터 감사

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`
- 목적: 앱 내 완전 오프라인 번들을 만들기 위해 현재 로컬 데이터와 원격 의존성을 정리한다.

## 1. 결론

1. 텍스트/메타 데이터는 대부분 이미 로컬에 있다.
2. 음악 이미지는 이미 로컬 정적 자산으로 보유 중이다.
3. 주민/카탈로그/변형 이미지 대부분은 아직 원격 URL 의존이다.
4. 완전 오프라인 앱으로 전환하려면 이미지 대량 다운로드가 필요하다.

## 2. 현재 로컬 데이터 현황

### 2.1 텍스트/메타 데이터

1. 메인 콘텐츠 DB: [content.db](/Users/temn/projects/acnh-app/nookipedia-api/content.db)
   - 크기: 약 `34MB`
   - 테이블: `catalog_items`, `catalog_variations`, `villagers`, `catalog_meta`, `recipe_tags`, `recipe_tag_links`
2. 원본/보조 JSON
   - [data/acnhapi](/Users/temn/projects/acnh-app/nookipedia-api/data/acnhapi): `9`개
   - [data/norviah-animal-crossing](/Users/temn/projects/acnh-app/nookipedia-api/data/norviah-animal-crossing): `14`개
   - [data](/Users/temn/projects/acnh-app/nookipedia-api/data): 루트 파일 `31`개
3. 한글화/매핑 데이터
   - `*_name_map_ko.json`, `species_map_ko.json`, `personality_map_ko.json` 등

### 2.2 현재 로컬 이미지

1. 음악 이미지: [static/assets/music](/Users/temn/projects/acnh-app/nookipedia-api/static/assets/music)
   - 파일 수: `110`
   - 크기: 약 `40MB`
2. 주민 로컬 이미지: [villagers](/Users/temn/projects/acnh-app/nookipedia-api/villagers)
   - 파일 수: `391`
   - 크기: 약 `26MB`
   - 현재 `content.db`의 주민 image/icon/photo/house URL과 직접 연결된 구조는 아님
3. 기타 정적 아이콘: [static/icons](/Users/temn/projects/acnh-app/nookipedia-api/static/icons)

## 3. 원격 이미지 의존 현황

### 3.1 catalog_items.image_url

원격 URL 이미지가 남아 있는 항목 수:

1. `furniture`: `2000`
2. `clothing`: `1527`
3. `photos`: `966`
4. `recipes`: `924`
5. `interior`: `737`
6. `special_items`: `457`
7. `items`: `442`
8. `tools`: `150`
9. `reactions`: `88`
10. `bugs`: `80`
11. `fish`: `80`
12. `fossils`: `73`
13. `art`: `43`
14. `sea`: `40`
15. `gyroids`: `36`

합계:

1. catalog item rows: `7,643`
2. unique catalog image URLs: `7,100`

예외:

1. `music`: `110`개 모두 로컬 `/static/assets/music/...`
2. `events`: `1,378`개는 현재 이미지 없음

### 3.2 catalog_variations.image_url

1. variation rows with remote image: `23,597`
2. unique variation image URLs: `22,762`

### 3.3 villagers image slots

1. 주민 수: `417`
2. 원격 image_url: `417`
3. 원격 icon_url: `417`
4. 원격 photo_url: `417`
5. 원격 house_exterior_url: `417`
6. 원격 house_interior_url: `417`
7. unique villager-related URLs: `2,085`

### 3.4 전체 고유 원격 이미지 URL

1. combined unique URLs: `27,273`

## 4. 저장된 manifest

대량 다운로드/정리용 manifest를 저장했다.

1. [catalog_remote_images.csv](/Users/temn/projects/acnh-app/nookipedia-api/data/offline_asset_manifests/catalog_remote_images.csv)
2. [catalog_variation_remote_images.csv](/Users/temn/projects/acnh-app/nookipedia-api/data/offline_asset_manifests/catalog_variation_remote_images.csv)
3. [villager_remote_images.csv](/Users/temn/projects/acnh-app/nookipedia-api/data/offline_asset_manifests/villager_remote_images.csv)

manifest 디렉터리 크기:

1. 약 `3.1MB`

## 5. 오프라인 앱 전환에 필요한 작업

1. 원격 이미지 `27,273`개 다운로드
2. 앱에서 사용할 로컬 자산 경로 규칙 설계
3. `content.db`의 원격 `image_url`을 로컬 경로로 치환하거나 매핑 테이블 추가
4. variation 이미지와 주민 house/photo/icon 이미지를 카테고리별 폴더에 정리
5. 앱 번들 용량 한도를 고려해 이미지 해상도/포맷 최적화

## 6. 권장 자산 구조

```text
app_assets/
  catalog/
    furniture/
    clothing/
    ...
  variations/
    furniture/
    clothing/
    ...
  villagers/
    icons/
    photos/
    houses/
```

## 7. 현재 blocker

1. 이 세션에서는 외부 네트워크를 사용해 이미지를 실제로 다운로드하지 않았다.
2. 따라서 지금 저장한 것은 "무엇을 받아야 하는지"에 대한 확정 목록이다.
3. 실제 다운로드를 하려면 네트워크 접근과 장시간 배치 실행이 필요하다.
