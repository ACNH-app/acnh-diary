# Flutter 데이터 모델 설계

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`

## 1. 목표

1. 서버 응답 DTO와 앱 내부 모델을 분리한다.
2. 카탈로그 타입별 응답 편차를 안전하게 흡수한다.
3. 캐시 저장 모델과 UI 모델을 구분한다.

## 2. 모델 계층

1. DTO
   - API JSON 직렬화 전용
   - nullable 필드를 서버 계약 그대로 보존
2. Domain Entity
   - 앱 로직에서 사용하는 정규화 모델
   - 타입 안정성과 기본값 보정 수행
3. UI Model
   - 화면 표시에 맞춘 가공 모델
   - 텍스트 조합, 배지 문구, 카드 subtitle 생성 담당
4. Local Cache Model
   - DB 저장에 맞춘 평탄 구조
   - query key, fetchedAt, payload snapshot 포함

## 3. 공통 엔티티

1. `AppImage`
   - `url`
   - `thumbnailUrl`
   - `fallbackAsset`
2. `LocalizedText`
   - `ko`
   - `en`
3. `PagedResult<T>`
   - `items`
   - `page`
   - `pageSize`
   - `totalCount`
   - `hasMore`
4. `MutationResult`
   - `success`
   - `syncedAt`
   - `message`

## 4. 주민 모델

### 4.1 DTO

1. `VillagerDto`
2. `VillagerStateDto`

### 4.2 Domain

1. `Villager`
   - `id`
   - `name`
   - `species`
   - `personality`
   - `birthday`
   - `image`
   - `isOnIsland`
   - `isFavorite`
   - `isDonatedToMuseum`
2. `VillagerStatePatch`
   - 부분 업데이트 전송용

## 5. 카탈로그 모델

### 5.1 공통 DTO

1. `CatalogListItemDto`
2. `CatalogMetaDto`
3. `CatalogStateDto`
4. `VariationStateDto`

### 5.2 Domain

1. `CatalogItem`
   - `catalogType`
   - `id`
   - `name`
   - `category`
   - `image`
   - `owned`
   - `donated`
   - `quantity`
   - `variationOwnedCount`
   - `variationTotal`
2. `CatalogDetail`
   - 공통 필드
   - `attributes: Map<String, CatalogAttribute>`
   - `variations: List<CatalogVariation>`
3. `CatalogVariation`
   - `id`
   - `label`
   - `image`
   - `owned`

### 5.3 타입별 확장

1. `RecipeDetail`
   - `materials`
   - `recipeFilters`
2. `ArtDetail`
   - `authenticity`
   - `fakeInfo`
   - `realInfo`
3. `EventItem`
   - `eventType`
   - `startDate`
   - `endDate`

## 6. 홈 모델

1. `HomeSummary`
   - `todayBirthdays`
   - `todayEvents`
   - `islandResidents`
   - `ownedCatalogStats`
2. `CreatureNow`
   - `type`
   - `name`
   - `availabilityText`
   - `image`

## 7. 일정/프로필 모델

1. `CalendarEntry`
   - `id`
   - `title`
   - `date`
   - `checked`
   - `note`
2. `CalendarAnnotation`
   - `date`
   - `count`
   - `hasUnchecked`
3. `IslandProfile`
   - `islandName`
   - `hemisphere`
   - `nativeFruit`
4. `Player`
   - `id`
   - `name`
   - `isMain`

## 8. 직렬화 규칙

1. 날짜는 내부적으로 `DateTime` 또는 value object로 파싱한다.
2. 서버의 `snake_case`는 앱에서 `camelCase`로 변환한다.
3. 서버의 빈 문자열은 domain 변환 시 `null`로 정규화한다.
4. 카탈로그 detail의 가변 속성은 화면에서 직접 `Map<String, dynamic>`를 소비하지 않는다.

## 9. 코드 생성 권장

1. DTO: `json_serializable`
2. Domain/UI model: `freezed`
3. enum: 서버 문자열과 앱 enum 간 converter 별도 정의

## 10. 주의사항

1. `special_items`는 실제 상태 저장 타입과 표시 타입이 다를 수 있다.
2. `recipes`, `art`, `photos`는 필터 및 상세 필드가 일반 카탈로그와 다르다.
3. API 응답 필드 추가에 대비해 DTO는 unknown field 허용 방향으로 유지한다.
