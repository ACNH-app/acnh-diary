# 모바일 앱 전환 체크리스트

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`
- 목적: 현재 웹/API 프로젝트를 Flutter 기반 모바일 앱으로 전환하기 전에 필요한 문서를 준비한다.

## 1. 문서 작성 순서

1. `docs/mobile-app-current-state-gap-analysis.md`
2. `docs/mobile-app-prd.md`
3. `docs/mobile-api-spec.md`
4. `docs/flutter-app-architecture.md`
5. `docs/flutter-auth-and-session-design.md`
6. `docs/mobile-offline-sync-design.md`
7. `docs/mobile-image-cache-policy.md`
8. `docs/mobile-release-and-store-plan.md`
9. `docs/mobile-qa-scenarios.md`

## 2. 현재 프로젝트에서 재사용 가능한 것

- [ ] FastAPI 읽기/쓰기 API 구조
- [ ] `content.db` 기반 조회 데이터
- [ ] 로컬 매핑 JSON 기반 한글화
- [ ] 주민/카탈로그/프로필/플레이어/캘린더 도메인 모델
- [ ] 이미지 소스 구조와 fallback 규칙

## 3. 새로 만들어야 할 것

- [ ] Flutter 앱 구조
- [ ] 모바일 전용 화면 흐름
- [ ] 오프라인 캐시/동기화 구조
- [ ] Flutter용 secure storage 전략
- [ ] App Store/Play Store 배포 계획

## 4. 구현 착수 전 확인

- [ ] PRD 확정
- [ ] API 계약 확정
- [ ] 공통 모바일 UX 흐름 확정
- [ ] Flutter 아키텍처 결정
- [ ] 오프라인 범위 결정
- [ ] 이미지 캐시 정책 결정
