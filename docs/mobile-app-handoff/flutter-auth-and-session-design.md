# Flutter 인증/세션 설계

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`

## 1. 현재 기준

1. 서버 인증 없음
2. 1차 모바일 앱도 로그인 없이 진행

## 2. 1차 앱 정책

1. 로그인 화면 없음
2. 인증 토큰 저장 없음
3. 네트워크 레이어는 인증 헤더 없이 동작

## 3. 미리 준비할 추상화

1. `AuthState`
2. `CredentialStore`
3. `AuthInterceptor`
4. `SessionManager`

## 4. 차기 공개 배포 확장

권장:

1. 서버: `JWT + refresh token`
2. 앱 저장: `flutter_secure_storage`
3. 401 시 refresh 후 재시도
4. 상태 테이블 `user_id` 분리
