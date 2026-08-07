# 땅콩이 백엔드

충북대학교 멋쟁이사자처럼 해커톤 1조 백엔드입니다. 현재는 FastAPI 실행 환경, Gemini 환경 변수, MySQL 연결 기반만 설정되어 있습니다.

## 포함된 기본 설정

- FastAPI 앱과 CORS 설정
- 로컬 실행 포트 5050
- `.env` 기반 환경 변수 관리
- Gemini API 키·모델 설정 값
- SQLAlchemy·PyMySQL 기반 MySQL 연결 세션
- 서버 및 MySQL 연결 상태 확인 API
- Render 배포 설정

## 실행 방법

Python 3.11 이상과 실행 중인 MySQL이 필요합니다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 5050
```

API 문서는 [http://localhost:5050/docs](http://localhost:5050/docs)에서 확인할 수 있습니다.

## 환경 변수

`.env.example`을 참고해 `.env`를 설정합니다. 실제 키와 비밀번호는 Git에 커밋하지 않습니다.

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DATABASE_URL=mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/ddangkongi?charset=utf8mb4
```

## 커밋 메시지 타입

- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅 등 기능과 무관한 코드 변경
- `refactor`: 기능 변경 없는 코드 리팩토링
- `test`: 테스트 추가 또는 수정
- `chore`: 빌드 프로세스 또는 보조 도구 수정
- `perf`: 성능 향상 관련 변경
- `build`: 빌드 관련 파일 변경

## 현재 API

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `GET` | `/health` | FastAPI 서버 상태 확인 |
| `GET` | `/health/database` | MySQL 연결 상태 확인 |

## Render 배포

저장소를 Render에 연결하면 `render.yaml`을 인식합니다. Render 환경 변수에는 아래 값을 등록합니다.

- `GEMINI_API_KEY`
- `DATABASE_URL` — Render에서는 로컬 `127.0.0.1`이 아닌 외부 MySQL 주소를 사용해야 합니다.
- `CORS_ORIGINS` — 배포된 프론트엔드 주소
