# 땅콩이 프론트엔드 연동 가이드

프론트엔드 팀원이 말싸움, 밸런스 게임, 끝말잇기 API를 연결할 때 참고하는 문서입니다.

## 빠른 정보

- API 주소: `http://127.0.0.1:5000`
- Swagger: [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs)
- 현재 사용 가능한 게임: `battle`, `balance`, `word_chain`
- 말싸움: 직장 상사·형·전애인 중 선택, 최대 5라운드
- 밸런스 게임: 질문 3개
- 끝말잇기: 최대 5라운드
- 서버를 재시작하면 진행 중인 게임이 초기화됩니다.

## 연결 순서

```text
POST /api/games
  → POST /api/games/{gameId}/turn (게임별 정해진 횟수)
  → GET /api/games/{gameId}/result
```

### 1. 게임 시작

```http
POST /api/games
Content-Type: application/json
```

```json
{
  "mode": "balance"
}
```

응답에서 다음 두 값을 저장합니다.

- `gameId`: 턴 진행 및 결과 조회 URL에 사용
- `nextPrompt`: 화면에 표시할 현재 질문과 선택지

> `nextPrompt.id`는 질문 ID입니다. URL의 `{gameId}` 자리에 사용하면 안 됩니다.

### 2. 선택 전송

`nextPrompt.choices` 중 사용자가 고른 문구를 그대로 `input`에 넣습니다.

```http
POST /api/games/{gameId}/turn
Content-Type: application/json
```

```json
{
  "input": "평생 치킨만 먹기"
}
```

응답 처리 방법:

- `reply`: AI 말풍선에 표시
- `score`: 화면의 점수 게이지 갱신
- `nextPrompt`: 다음 질문 표시
- `ended`: `true`이면 결과 화면으로 이동

### 3. 결과 조회

```http
GET /api/games/{gameId}/result
```

주요 결과값:

- `winner`: `me`, `ai`, `draw` 중 하나
- `title`: 결과 화면 제목
- `finalScore`: 사용자 최종 점수
- `metrics.agreement`: AI와 같은 답을 고른 비율
- `bestLine`: 마지막으로 선택한 문구

전체 요청·응답 JSON은 [API 명세](API_SPEC.md)를 확인하세요.

## 말싸움 연결

시작할 때 역할을 함께 보냅니다.

```json
{
  "mode": "battle",
  "opponentType": "boss"
}
```

- `boss`: 직장 상사
- `older_brother`: 형
- `ex`: 전애인

시작 응답의 `message`는 첫 AI 말풍선, `quickReplies`는 하단 추천 답변으로 표시합니다. 사용자가 직접 입력하거나 추천 답변을 누르면 공통 턴 API의 `input`으로 전송합니다.

턴 응답 처리:

- `reply`: 페르소나가 유지된 AI 답변
- `score`: 상단 승부 게이지 (`me + ai = 100`)
- `turnScore`: 이번 턴의 원점수
- `analysis`: 논리력, 타격감, 티키타카, 분노 단계와 감점
- `judgeReason`: 이번 점수의 짧은 설명
- `ended`: `true`이면 결과 API 호출
- `winner`: 종료 시 `me`, `ai`, `draw`

말싸움은 Gemini API를 사용하므로 일시적으로 `503 AI_SERVICE_ERROR`가 올 수 있습니다. 이때는 입력을 유지하고 재시도 안내를 보여주세요. 욕설·협박이 감지되면 해당 턴에서 바로 게임이 끝납니다.

## 프론트엔드 예시

```ts
const API_BASE_URL = "http://127.0.0.1:5000";

export async function startBalanceGame() {
  const response = await fetch(`${API_BASE_URL}/api/games`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: "balance" }),
  });

  if (!response.ok) throw new Error("게임을 시작하지 못했습니다.");
  return response.json();
}

export async function submitBalanceChoice(gameId: string, input: string) {
  const response = await fetch(`${API_BASE_URL}/api/games/${gameId}/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input }),
  });

  if (!response.ok) throw new Error("선택을 전송하지 못했습니다.");
  return response.json();
}

export async function getBalanceResult(gameId: string) {
  const response = await fetch(`${API_BASE_URL}/api/games/${gameId}/result`);

  if (!response.ok) throw new Error("결과를 불러오지 못했습니다.");
  return response.json();
}
```

## 끝말잇기 연결

API URL은 밸런스 게임과 동일하며 시작할 때 `mode`만 변경합니다.

```ts
export async function startWordChainGame() {
  const response = await fetch(`${API_BASE_URL}/api/games`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: "word_chain" }),
  });

  if (!response.ok) throw new Error("끝말잇기를 시작하지 못했습니다.");
  return response.json();
}
```

시작 응답 처리:

- `message`: 화면에 표시할 시작 단어
- `nextPrompt`: 입력창에 안내할 필수 첫 글자
- `wordHistory`: 단어 기록 영역에 표시할 목록

턴 요청은 밸런스 게임과 같은 `submitBalanceChoice()` 형태를 사용하고 `input`에 사용자가 작성한 단어를 넣습니다. 함수 이름은 프론트에서 `submitGameTurn()`처럼 공통 이름으로 변경해도 됩니다.

턴 응답 처리:

- `accepted`: 사용자 단어의 규칙 통과 여부
- `reply`: AI 단어 또는 패배 이유
- `nextPrompt`: 다음에 입력할 첫 글자
- `wordHistory`: 갱신된 전체 단어 기록
- `ended`: 결과 화면 이동 여부
- `winner`: 게임 종료 전에는 `null`, 종료 후 `me` 또는 `ai`

현재는 `app/data/word_chain_words.json`에 준비된 단어만 사용할 수 있습니다. 잘못된 단어는 HTTP 오류가 아니라 `ended: true`인 패배 결과로 반환됩니다.

## 백엔드 파일 구조

```text
hackathon-BE/
├── app/
│   ├── main.py                  # FastAPI 앱, CORS, 라우터 연결
│   ├── store.py                 # 진행 중인 게임을 메모리에 저장
│   ├── data/
│   │   ├── battle_rules.json     # 욕설·협박·분노 판정용 키워드
│   │   └── word_chain_words.json # 시작 단어와 전체 끝말잇기 단어
│   ├── api/routes/
│   │   ├── games.py             # 게임 시작·턴 진행·결과 API
│   │   └── health.py            # 서버·DB 상태 확인 API
│   ├── games/
│   │   ├── balance.py           # 밸런스 질문과 진행 규칙
│   │   ├── battle.py            # 말싸움 진행, 점수와 승패 계산
│   │   └── word_chain.py        # 끝말잇기 단어 목록과 전체 진행 규칙
│   ├── schemas/games.py         # 공통 게임 요청 검증
│   ├── services/gemini_games.py # Gemini JSON 공통 호출 도우미
│   ├── services/gemini_battle.py # 페르소나 답변과 점수 심사
│   ├── core/config.py           # .env 설정 로딩
│   └── db/session.py            # MySQL 연결 세션
├── docs/API_SPEC.md             # 상세 API 명세
└── tests/                       # 게임 로직과 API 테스트
```

## 주요 함수

| 파일 | 함수 | 역할 |
| --- | --- | --- |
| `app/api/routes/games.py` | `create_game()` | 새 게임과 첫 질문 반환 |
|  | `play_turn()` | 사용자 선택 처리 |
|  | `get_result()` | 종료된 게임 결과 반환 |
|  | `error_response()` | 공통 오류 JSON 생성 |
| `app/games/balance.py` | `start_game()` | 질문 3개 선택 및 게임 상태 생성 |
|  | `current_prompt()` | 현재 질문과 선택지 반환 |
|  | `play_turn()` | 선택 검증, 점수 계산, 다음 라운드 진행 |
|  | `get_result()` | 취향 일치도와 최종 결과 계산 |
| `app/games/word_chain.py` | `start_game()` | 시작 단어와 게임 상태 생성 |
|  | `load_word_data()` | JSON 단어 목록 로딩 및 형식 검사 |
|  | `get_start_response()` | 시작 단어와 필수 첫 글자 반환 |
|  | `validate_word()` | 첫 글자, 중복, 단어 목록 검사 |
|  | `find_ai_word()` | AI가 이어갈 단어 선택 |
|  | `play_turn()` | 사용자 단어 판정과 AI 턴 진행 |
|  | `get_result()` | 승패와 단어 기록 결과 계산 |
| `app/games/battle.py` | `start_game()` | 선택한 상대 역할로 말싸움 상태 생성 |
|  | `play_turn()` | 반칙 검사, Gemini 답변·심사, 점수 누적 |
|  | `calculate_turn_score()` | 항목별 가중치와 분노 감점 계산 |
|  | `get_result()` | 최종 승패와 평균 능력치 반환 |
| `app/services/gemini_battle.py` | `generate_persona_reply()` | 역할에 맞는 AI 대사 생성 |
|  | `judge_turn()` | 사용자와 AI 답변을 별도 Gemini 요청으로 심사 |
| `app/services/gemini_games.py` | `get_gemini_client()` | Gemini 클라이언트 생성 및 재사용 |
|  | `generate_json()` | Gemini 응답을 JSON으로 변환 |
| `app/store.py` | `new_game_id()` | 게임 ID 생성 |
| `app/core/config.py` | `get_settings()` | 환경 변수 설정 로딩 |

## 자주 발생하는 오류

### `404 GAME_NOT_FOUND`

URL에 `nextPrompt.id`가 아니라 시작 응답의 `gameId`를 입력했는지 확인합니다.

### `400 INVALID_INPUT`

현재 응답의 `nextPrompt.choices` 중 하나를 공백과 문구까지 동일하게 전송해야 합니다.

끝말잇기의 규칙 위반은 400 오류가 아니라 정상 응답의 `accepted: false`, `ended: true`로 반환됩니다.

### 서버 재시작 후 기존 게임이 조회되지 않음

게임 상태가 메모리에 저장되므로 서버 재시작 후 `POST /api/games`부터 다시 호출해야 합니다.

### macOS에서 `localhost:5000`이 403을 반환함

AirPlay Receiver와 충돌할 수 있으므로 `http://127.0.0.1:5000`을 사용합니다.
