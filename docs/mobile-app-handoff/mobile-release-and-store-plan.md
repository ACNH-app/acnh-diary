# 모바일 배포/스토어 계획

- 작성일: 2026-03-12
- 대상 프로젝트: `nookipedia-api`
- 플랫폼: `App Store + Play Store`

## 1. 환경

1. `dev`
2. `staging`
3. `prod`

환경별 설정:

1. API base URL
2. 앱 이름 suffix
3. 디버그 메뉴 노출 여부

## 2. 배포 채널

1. 내부 개발 빌드
2. TestFlight
3. Play Internal Testing
4. 정식 배포 빌드

## 3. 스토어 제출 전 체크

1. 앱 설명/스크린샷 준비
2. 개인정보 처리방침 필요 여부 검토
3. 데이터/이미지 사용 권한 정리
4. 네트워크 실패 UX 점검
5. 미구현 메뉴 제거

## 4. 공개 배포 전 주의

1. 현재 서버는 인증이 없으므로 공개 운영 시 보안 검토 필요
2. App Store와 Play Store 모두 비정상 종료 없는 빌드 필요
