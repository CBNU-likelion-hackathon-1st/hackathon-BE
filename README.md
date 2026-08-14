# 땅콩이 백엔드

충북대학교 멋쟁이사자처럼 중앙 해커톤 1조의 미니게임 백엔드입니다. FastAPI를 기반으로 말싸움, 끝말잇기, 밸런스 게임 API를 개발합니다.

## 개발 현황

| 게임 | 상태 | 설명 |
| --- | --- | --- |
| 밸런스 게임 | ✅ 구현 완료 | 게임 시작, 3회 선택, 결과 조회 |
| 끝말잇기 | ✅ 구현 완료 | 최대 5라운드, 단어 검증, AI 응답, 결과 조회 |
| 말싸움 | ✅ 구현 완료 | 직장 상사·형·전애인 Gemini 대화, 점수 심사, 반칙 판정 |

밸런스 게임과 끝말잇기는 별도 DB와 Gemini 호출 없이 실행됩니다. 말싸움만 Gemini API를 사용하며, 진행 상태는 서버 메모리에 저장합니다. 끝말잇기 단어는 `app/data/word_chain_words.json`, 말싸움 반칙 키워드는 `app/data/battle_rules.json`에서 관리합니다.

## 기술 스택

- Python 3.11+
- FastAPI
- Pydantic
- Uvicorn
- Google Gemini API
- SQLAlchemy / MySQL

## 시작하기

```bash
git clone <repository-url>
cd hackathon-BE
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 5000
```

서버 실행 후 아래 주소에서 Swagger 문서를 확인할 수 있습니다.

- Swagger UI: [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs)
- 상태 확인: [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health)

> macOS에서 `localhost:5000` 접속 시 403 오류가 발생하면 `127.0.0.1:5000`을 사용하세요.

## 현재 API

| Method | Endpoint | 설명 |
| --- | --- | --- |
| `GET` | `/health` | 서버 상태 확인 |
| `GET` | `/health/database` | MySQL 연결 상태 확인 |
| `GET` | `/api/battle/opponents` | 홈 화면의 말싸움 상대 카드 목록 |
| `POST` | `/api/games` | 게임 시작 |
| `POST` | `/api/games/{gameId}/turn` | 한 턴 진행 |
| `GET` | `/api/games/{gameId}/result` | 게임 결과 조회 |

## 프로젝트 구조

```text
app/
├── main.py                 # FastAPI 앱 진입점
├── store.py                # 메모리 게임 저장소
├── api/routes/             # API 엔드포인트
├── data/                   # 질문·단어 등 정적 게임 데이터
├── games/                  # 게임별 진행 로직
├── schemas/                # 요청 데이터 검증
├── services/               # 외부 서비스 연동
├── core/                   # 환경 설정
└── db/                     # 데이터베이스 연결
```

게임별 핵심 파일은 다음과 같습니다.

- `app/games/balance.py`: 밸런스 게임 진행
- `app/games/word_chain.py`: 끝말잇기 진행
- `app/games/battle.py`: 말싸움 진행, 점수 계산, 반칙 판정
- `app/services/gemini_battle.py`: 말싸움 페르소나 답변과 별도 심사 호출

## 문서

- [프론트엔드 연동 가이드](docs/FRONTEND_GUIDE.md)
- [API 요청·응답 명세](docs/API_SPEC.md)

## 테스트

```bash
python -m unittest discover -s tests -v
```

## 환경 변수

`.env.example`을 복사해 사용합니다. 실제 API 키와 데이터베이스 비밀번호가 포함된 `.env`는 커밋하지 않습니다.

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-flash-latest
APP_ENV=development
HOST=0.0.0.0
PORT=5000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DATABASE_URL=mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/ddangkongi?charset=utf8mb4
```

## 커밋 메시지

- `feat`: 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 변경
- `refactor`: 코드 구조 개선
- `test`: 테스트 추가 또는 수정
- `chore`: 설정 및 보조 작업
