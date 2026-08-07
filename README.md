# 땅콩이 백엔드

충북대학교 멋쟁이사자처럼 해커톤 1조의 AI 말싸움 미니게임 백엔드입니다.

## 시작하기

Python 3.11 이상에서 실행합니다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 5050
```

브라우저에서 `http://localhost:5050/docs`를 열어 API를 테스트할 수 있습니다.
`GEMINI_API_KEY`는 `.env`에만 저장하며 절대 커밋하지 않습니다.

## API

- `GET /health` — 서버 상태 확인
- `GET /health/database` — MySQL 연결 상태 확인
- `POST /api/v1/chat` — 땅콩이의 말싸움 응답 생성

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

## Render 배포

저장소를 Render에 연결하면 `render.yaml`을 인식합니다. Render 대시보드에서 아래 환경 변수를 설정하세요.

- `GEMINI_API_KEY`: Google AI Studio에서 발급한 실제 키
- `CORS_ORIGINS`: 배포된 프론트엔드 주소. 예: `https://your-app.vercel.app`
- `DATABASE_URL`: MySQL 연결 문자열. 예: `mysql+pymysql://USER:PASSWORD@HOST:3306/ddangkongi?charset=utf8mb4`
