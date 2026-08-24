# ACNH Diary React Frontend

React/Vite 기반 새 프론트엔드입니다. 기존 FastAPI 백엔드는 그대로 두고 개발 중에는 Vite proxy로 `/api`와 `/static` 요청을 `http://127.0.0.1:8001`에 전달합니다.

## Commands

```bash
npm install
npm run dev
npm run build
```

## Input Documents

SRS, SDS, SAD가 제공되면 이 앱의 화면 구조, 상태 관리, API 경계, 폴더 구조를 해당 문서 기준으로 확장합니다.
