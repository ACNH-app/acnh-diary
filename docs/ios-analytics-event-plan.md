# iOS 분석 이벤트 계획

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`
- 목적: iPhone 앱의 핵심 사용 흐름을 측정하기 위한 최소 이벤트 집합을 정의한다.

## 1. 원칙

1. 사용자 행동 측정은 핵심 플로우에만 한정한다.
2. 개인정보성 텍스트는 이벤트에 직접 싣지 않는다.
3. 이벤트 이름은 기능 기준으로 일관되게 둔다.

## 2. 공통 속성

모든 이벤트에 붙일 수 있는 공통 속성:

1. `screen`
2. `app_version`
3. `build_number`
4. `environment`

## 3. 핵심 이벤트

### 3.1 앱/화면

1. `app_opened`
2. `home_viewed`
3. `villagers_viewed`
4. `catalog_viewed`
5. `calendar_viewed`

### 3.2 주민

1. `villager_filter_applied`
2. `villager_state_updated`
3. `island_order_updated`

권장 속성:

1. `filter_type`
2. `changed_fields`

### 3.3 카탈로그

1. `catalog_type_selected`
2. `catalog_filter_applied`
3. `catalog_item_opened`
4. `catalog_state_updated`
5. `catalog_variation_state_updated`

권장 속성:

1. `catalog_type`
2. `has_variations`
3. `changed_fields`

### 3.4 프로필/플레이어

1. `profile_updated`
2. `player_created`
3. `player_deleted`
4. `main_player_changed`

### 3.5 캘린더

1. `calendar_day_opened`
2. `calendar_entry_created`
3. `calendar_entry_checked`
4. `calendar_entry_deleted`

## 4. 품질 이벤트

1. `api_request_failed`
2. `image_load_failed`
3. `sync_queue_failed`

주의:

1. 실패 이벤트는 과도하게 쏘지 않도록 샘플링 또는 중복 억제 필요

## 5. 1차 출시 범위

1차에서는 아래만 구현해도 충분하다.

1. `app_opened`
2. `home_viewed`
3. `villager_state_updated`
4. `catalog_item_opened`
5. `catalog_state_updated`
6. `calendar_entry_created`
