# ACNH Diary React Frontend

React/Vite 기반 새 프론트엔드입니다. 기존 FastAPI 백엔드는 그대로 두고 개발 중에는 Vite proxy로 `/api`와 `/static` 요청을 `http://127.0.0.1:8001`에 전달합니다.

## Commands

```bash
npm install
npm run dev
npm run build
```

백엔드 API smoke 테스트는 저장소 루트에서 실행합니다.

```powershell
$env:STATE_BACKEND = "sqlite"
$env:CONTENT_BACKEND = "sqlite"
$env:ASSET_BACKEND = "local"
python scripts/webapp_smoke_test.py
```

## Local API

Vite 개발 서버는 기본적으로 `http://127.0.0.1:8001`의 FastAPI를 프록시합니다. Supabase 연결이 가능한 환경에서는 기존 `.env` 설정으로 실행하고, 오프라인 로컬 개발에서는 PowerShell에서 SQLite fallback을 명시할 수 있습니다.

```powershell
$env:STATE_BACKEND = "sqlite"
$env:CONTENT_BACKEND = "sqlite"
$env:ASSET_BACKEND = "local"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

## Input Documents

SRS, SDS, SAD가 제공되면 이 앱의 화면 구조, 상태 관리, API 경계, 폴더 구조를 해당 문서 기준으로 확장합니다.

루틴은 현재 백엔드 전용 테이블이 없는 상태에서 섬·날짜별 `localStorage` 계층으로 동작하며, 완료 토글·수량형 목표·이름 수정·순서 변경을 지원합니다. 서버 동기화는 루틴 스키마/API가 추가될 때 `src/api/localRoutines.ts`를 교체하는 후속 작업입니다. 주민 사진 보유 상태도 같은 이유로 섬별 `localStorage`에 저장됩니다.

오늘 화면은 본문에 아이콘 중심의 컴팩트한 루틴 체크만 표시하고, `루틴 관리` 모달에서 기본 루틴 선택·사용자 루틴 추가·수정·삭제·순서 변경을 처리합니다. NPC 방문은 메인 화면에 최근 7일 요약만 표시하며, `NPC 선택` 모달에서 요일별 NPC 선택 칩으로 기록합니다. 생물은 API의 `icon_url`, 루틴은 `static/icons/`, NPC는 `static/icons/nav-more-bell.svg`를 사용합니다. 저장소에는 주민 이미지(`villagers/`)와 다수의 오프라인 이미지 캐시도 있지만, 전용 NPC 이미지 디렉터리는 없습니다.
