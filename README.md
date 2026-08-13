# 땅콩이 백엔드

충북대학교 멋쟁이사자처럼 해커톤 1조의 FastAPI 백엔드입니다. 현재 **밸런스 게임 전체 흐름**이 구현되어 있으며, 질문과 게임 상태는 DB 없이 코드와 서버 메모리로 관리합니다.

## 프론트엔드 팀 빠른 안내

- API 주소: `http://localhost:5000`
- Swagger 문서: [http://localhost:5000/docs](http://localhost:5000/docs)
- 상세 명세: [`docs/API_SPEC.md`](docs/API_SPEC.md)
- 현재 사용 가능한 게임 모드: `balance`
- 한 게임은 질문 3개로 진행됩니다.
- 요청의 `input`에는 응답으로 받은 `nextPrompt.choices` 중 하나를 그대로 보내면 됩니다.
- `ended: true`가 오면 결과 조회 API를 호출합니다.
- 서버를 재시작하면 진행 중인 게임은 사라집니다.

### 프론트엔드 호출 순서

```text
POST /api/games
  → POST /api/games/{gameId}/turn (총 3번)
  → GET /api/games/{gameId}/result
```

## 실행 방법

Python 3.11 이상이 필요합니다. 밸런스 게임 API는 MySQL이나 Gemini 없이 실행됩니다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 5000
```

```bash
curl http://localhost:5000/health
```

## 파일 구조

```text
hackathon-BE/
├── app/
│   ├── main.py                 # FastAPI 앱, CORS, 라우터 연결
│   ├── store.py                # 진행 중인 게임을 메모리에 저장
│   ├── api/routes/
│   │   ├── games.py            # 게임 시작·턴 진행·결과 API
│   │   └── health.py           # 서버·DB 상태 확인 API
│   ├── games/
│   │   ├── balance.py          # 밸런스 질문과 진행 규칙
│   │   ├── battle.py           # 말싸움 게임 자리, 추후 구현
│   │   └── word_chain.py       # 끝말잇기 판정 코드, 전체 진행은 추후 구현
│   ├── schemas/games.py        # 공통 게임 요청 데이터 검증
│   ├── services/gemini_games.py # Gemini JSON 호출 공통 도우미
│   ├── core/config.py          # .env 설정 로딩
│   └── db/session.py           # MySQL 세션, 현재 게임에는 사용하지 않음
├── docs/API_SPEC.md            # 프론트엔드용 API 요청·응답 명세
├── tests/                      # 게임 로직·API 흐름 테스트
├── requirements.txt
└── render.yaml
```

## 주요 함수

| 파일 | 함수 | 설명 |
| --- | --- | --- |
| `app/api/routes/games.py` | `create_game()` | `mode`를 받아 새 게임과 첫 질문을 반환합니다. |
|  | `play_turn()` | 사용자의 선택을 게임 로직으로 전달합니다. |
|  | `get_result()` | 종료된 게임의 결과를 반환합니다. |
|  | `error_response()` | 게임 API 오류를 동일한 JSON 형식으로 만듭니다. |
| `app/games/balance.py` | `start_game()` | 준비된 질문 중 3개를 무작위로 선택합니다. |
|  | `current_prompt()` | 현재 질문과 두 선택지를 반환합니다. |
|  | `play_turn()` | 선택 검증, AI 반응, 점수, 다음 라운드를 처리합니다. |
|  | `get_result()` | 취향 일치도와 최종 결과를 계산합니다. |
| `app/games/word_chain.py` | `validate_word_chain()` | 끝 글자 규칙과 Gemini 단어 판정을 수행합니다. |
| `app/services/gemini_games.py` | `get_gemini_client()` | Gemini 클라이언트를 한 번 생성해 재사용합니다. |
|  | `generate_json()` | Gemini 응답을 JSON 객체로 변환합니다. |
| `app/store.py` | `new_game_id()` | 새로운 게임 ID를 생성합니다. |
| `app/core/config.py` | `get_settings()` | `.env`의 설정을 읽어 재사용합니다. |

## 현재 API

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `GET` | `/health` | FastAPI 서버 상태 확인 |
| `GET` | `/health/database` | MySQL 연결 상태 확인 |
| `POST` | `/api/games` | 밸런스 게임 시작 |
| `POST` | `/api/games/{gameId}/turn` | 한 문제의 선택 전송 |
| `GET` | `/api/games/{gameId}/result` | 종료된 게임 결과 조회 |

## 환경 변수

`.env.example`을 복사해 `.env`를 만듭니다. 실제 키와 비밀번호는 Git에 커밋하지 않습니다.

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
APP_ENV=development
HOST=0.0.0.0
PORT=5000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DATABASE_URL=mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/ddangkongi?charset=utf8mb4
```

## 테스트

```bash
python -m unittest discover -s tests -v
```

## 커밋 메시지 타입

- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 변경
- `refactor`: 기능 변경 없는 코드 구조 변경
- `test`: 테스트 추가 또는 수정
- `chore`: 빌드·보조 설정 변경
