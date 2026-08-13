# 땅콩이 프론트엔드 연동 가이드

프론트엔드 팀원이 밸런스 게임 API를 연결할 때 참고하는 문서입니다.

## 빠른 정보

- API 주소: `http://127.0.0.1:5000`
- Swagger: [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs)
- 현재 사용 가능한 게임: `balance`
- 게임당 질문 수: 3개
- 서버를 재시작하면 진행 중인 게임이 초기화됩니다.

## 연결 순서

```text
POST /api/games
  → POST /api/games/{gameId}/turn (총 3번)
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

## 백엔드 파일 구조

```text
hackathon-BE/
├── app/
│   ├── main.py                  # FastAPI 앱, CORS, 라우터 연결
│   ├── store.py                 # 진행 중인 게임을 메모리에 저장
│   ├── api/routes/
│   │   ├── games.py             # 게임 시작·턴 진행·결과 API
│   │   └── health.py            # 서버·DB 상태 확인 API
│   ├── games/
│   │   ├── balance.py           # 밸런스 질문과 진행 규칙
│   │   ├── battle.py            # 말싸움 게임, 추후 구현
│   │   └── word_chain.py        # 끝말잇기 판정 코드
│   ├── schemas/games.py         # 공통 게임 요청 검증
│   ├── services/gemini_games.py # Gemini JSON 호출 도우미
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
| `app/games/word_chain.py` | `validate_word_chain()` | 끝말 규칙과 단어 유효성 판정 |
| `app/services/gemini_games.py` | `get_gemini_client()` | Gemini 클라이언트 생성 및 재사용 |
|  | `generate_json()` | Gemini 응답을 JSON으로 변환 |
| `app/store.py` | `new_game_id()` | 게임 ID 생성 |
| `app/core/config.py` | `get_settings()` | 환경 변수 설정 로딩 |

## 자주 발생하는 오류

### `404 GAME_NOT_FOUND`

URL에 `nextPrompt.id`가 아니라 시작 응답의 `gameId`를 입력했는지 확인합니다.

### `400 INVALID_CHOICE`

현재 응답의 `nextPrompt.choices` 중 하나를 공백과 문구까지 동일하게 전송해야 합니다.

### 서버 재시작 후 기존 게임이 조회되지 않음

게임 상태가 메모리에 저장되므로 서버 재시작 후 `POST /api/games`부터 다시 호출해야 합니다.

### macOS에서 `localhost:5000`이 403을 반환함

AirPlay Receiver와 충돌할 수 있으므로 `http://127.0.0.1:5000`을 사용합니다.
