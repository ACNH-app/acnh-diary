# ACNH Diary Today Page Component Structure

## Goal

Turn the current `오늘` screen into a reusable Figma component set that can scale to other pages without rebuilding each card by hand.

## Page Structure

Use this page split in Figma:

1. `Cover`
2. `Foundations`
3. `Components / Labels`
4. `Components / Chips`
5. `Components / Cards`
6. `Components / Lists`
7. `Components / Navigation`
8. `Screens / Today`

## Foundation Tokens

Create these first as local variables/styles.

### Color

- `color/bg/app`
- `color/bg/card`
- `color/bg/card-subtle`
- `color/bg/chip-green`
- `color/bg/chip-yellow`
- `color/bg/chip-purple`
- `color/bg/chip-blue`
- `color/bg/chip-cream`
- `color/bg/progress-track`
- `color/bg/progress-fill`
- `color/text/primary`
- `color/text/secondary`
- `color/text/inverse`
- `color/text/green`
- `color/text/yellow`
- `color/text/purple`
- `color/text/blue`
- `color/border/card`
- `color/icon/default`
- `color/icon/muted`

### Radius

- `radius/chip = 12`
- `radius/card = 24`
- `radius/card-lg = 28`
- `radius/nav = 28`
- `radius/full = 999`

### Spacing

- `space/4`
- `space/6`
- `space/8`
- `space/10`
- `space/12`
- `space/14`
- `space/16`
- `space/18`
- `space/20`
- `space/24`

### Type Styles

- `type/hero-date`
- `type/section-label`
- `type/card-body`
- `type/card-title`
- `type/card-caption`
- `type/chip-label`
- `type/nav-label`

## Component Inventory

Build from small to large.

### 1. `SectionLabel`

Purpose: card 밖에 걸치는 상단 라벨.

Variants:

- `tone = orange | green | yellow | blue | indigo`
- `width = auto | fixed`

Props:

- `label`

### 2. `StatusChip`

Purpose: 상단 정보칩, 가격칩, 상태칩 공통.

Variants:

- `tone = green | yellow | purple | blue | cream`
- `size = sm | md`
- `icon = none | leading-dot | leading-symbol`

Props:

- `label`

### 3. `IconBadge`

Purpose: 생물/시즌 영역의 둥근 아이콘 배경.

Variants:

- `tone = yellow | green | cream`
- `iconType = fish | salmon | beetle | fireworks | weather`

If icon swap is convenient, prefer:

- base badge component
- nested icon instance via `INSTANCE_SWAP`

### 4. `ProgressBar`

Purpose: 루틴/레시피 공용 진행률 바.

Variants:

- `tone = green | yellow`
- `size = sm | md`

Props:

- `valueText`
- optional overlay label

Structure:

- Track
- Fill
- Optional label row outside component

### 5. `ChecklistRow`

Purpose: 루틴 체크리스트 행.

Variants:

- `state = complete | pending`

Props:

- `label`

Nested parts:

- `CheckIndicator`
- `RowBackground`
- `Text`

### 6. `CritterRow`

Purpose: 미수집 생물 리스트 한 줄.

Variants:

- `iconType = fish | salmon | beetle`
- `badge = bells | time | location`

Props:

- `name`
- `meta`
- `price`

Structure:

- leading `IconBadge`
- text stack
- trailing `StatusChip`

### 7. `RecipeTag`

Purpose: 시즌 카드 내부 태그.

Variants:

- `tone = cream`
- `size = sm`

Props:

- `label`

### 8. `InfoMiniCard`

Purpose: 이벤트 / 팁 하단 2열 카드 공통 베이스.

Variants:

- `tone = neutral | blue`
- `labelTone = blue | indigo`
- `height = compact`

Props:

- `sectionLabel`
- `title`
- `body`

### 9. `BottomNavItem`

Purpose: 하단 탭 1개.

Variants:

- `state = active | inactive`
- `icon = home | catalog | guide | island`

Props:

- `label`

### 10. `BottomNavigation`

Purpose: 하단 네비 전체.

Contains:

- 4x `BottomNavItem`

Props:

- current tab state only through nested variants

## Card Components

After atoms above, build these reusable section cards.

### 11. `TodayHeroCard`

Variants:

- `weather = clear | cloudy | rain`

Props:

- `hemisphere`
- `islandName`
- `time`
- `date`
- `subtitleLine1`
- `subtitleLine2`
- `stat1`
- `stat2`
- `stat3`

Nested components:

- `StatusChip`

### 12. `RoutineCard`

Props:

- `progressText`

Nested components:

- `SectionLabel`
- `ProgressBar`
- 4x `ChecklistRow`

Recommended future variant:

- `density = compact | default`

### 13. `CritterCard`

Props:

- `description`

Nested components:

- `SectionLabel`
- 3x `CritterRow`

### 14. `SeasonRecipeCard`

Props:

- `seasonName`
- `progressText`

Nested components:

- `SectionLabel`
- `IconBadge`
- `ProgressBar`
- multiple `RecipeTag`

### 15. `EventCard`

Nested components:

- `InfoMiniCard` base or dedicated card
- `StatusChip`

### 16. `TipCard`

Nested components:

- `InfoMiniCard` base

## Screen Assembly

Use this assembly for `Screens / Today`.

1. `TodayHeroCard`
2. `RoutineCard`
3. `CritterCard`
4. `SeasonRecipeCard`
5. 2-column row
   - `EventCard`
   - `TipCard`
6. `BottomNavigation`

## Auto Layout Rules

Apply these consistently:

- Screen frame: vertical auto layout
- Card stack gap: `space/16`
- Card internal padding: `space/18`
- Card internal gap: `space/12`
- Row chips: horizontal auto layout
- All text stacks: vertical auto layout with `space/2` to `space/4`
- Bottom nav: horizontal auto layout with equal-width items

## Naming Convention

Use these names in Figma exactly:

- `SectionLabel`
- `StatusChip`
- `IconBadge`
- `ProgressBar`
- `ChecklistRow`
- `CritterRow`
- `RecipeTag`
- `InfoMiniCard`
- `BottomNavItem`
- `BottomNavigation`
- `TodayHeroCard`
- `RoutineCard`
- `CritterCard`
- `SeasonRecipeCard`
- `EventCard`
- `TipCard`

Variant naming:

- `State=Active`
- `Tone=Green`
- `Icon=Home`
- `Size=SM`

## Recommended Build Order

1. Tokens
2. `SectionLabel`
3. `StatusChip`
4. `IconBadge`
5. `ProgressBar`
6. `ChecklistRow`
7. `CritterRow`
8. `RecipeTag`
9. `BottomNavItem`
10. `BottomNavigation`
11. `InfoMiniCard`
12. section cards
13. `Screens / Today`

## What To Componentize Later

These can stay local for now, then be extracted later:

- weather chip icon glyphs
- critter-specific internal icon strokes
- event tag badge

These should be componentized now:

- all section labels
- all chips
- all list rows
- bottom nav item
- each major card container
