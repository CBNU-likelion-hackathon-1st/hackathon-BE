# 땅콩이 MVP API 명세서

- Base URL: `http://127.0.0.1:5000`
- 구현 완료: 밸런스 게임, 끝말잇기
- 게임 상태: 서버 메모리에 저장하며 서버 재시작 시 초기화

## 공통 API

| Method | URL | 설명 |
| --- | --- | --- |
| `POST` | `/api/games` | `mode`에 맞는 게임 시작 |
| `POST` | `/api/games/{gameId}/turn` | 한 턴 진행 |
| `GET` | `/api/games/{gameId}/result` | 종료된 게임 결과 조회 |

---

## 밸런스 게임

### 1. 게임 시작

`POST /api/games`

```json
{
  "mode": "balance"
}
```

```json
{
  "gameId": "game-a1b2c3d4",
  "mode": "balance",
  "status": "playing",
  "round": 1,
  "score": {"me": 50, "ai": 50},
  "message": "둘 중 하나를 골라보세요!",
  "nextPrompt": {
    "id": "food-01",
    "question": "평생 하나만 먹을 수 있다면?",
    "choices": ["평생 라면만 먹기", "평생 치킨만 먹기"]
  }
}
```

### 2. 선택 전송

`POST /api/games/{gameId}/turn`

```json
{
  "input": "평생 치킨만 먹기"
}
```

```json
{
  "reply": "오, 나랑 같은 선택이네! 치킨은 매일 다른 맛으로 먹을 수 있잖아!",
  "round": 2,
  "score": {"me": 55, "ai": 45},
  "nextPrompt": {
    "id": "travel-01",
    "question": "휴가를 떠난다면?",
    "choices": ["친구 10명과 단체 여행", "혼자 조용한 호캉스"]
  },
  "ended": false
}
```

세 번째 선택 후에는 `ended`가 `true`, `nextPrompt`가 `null`이다.

### 3. 결과 조회

`GET /api/games/{gameId}/result`

```json
{
  "gameId": "game-a1b2c3d4",
  "mode": "balance",
  "winner": "me",
  "title": "AI와 취향이 통했어요!",
  "finalScore": 55,
  "metrics": {
    "agreement": 67,
    "difference": 33,
    "completedRounds": 3
  },
  "bestLine": "혼자 조용한 호캉스"
}
```

---

## 끝말잇기

### 1. 게임 시작

`POST /api/games`

```json
{
  "mode": "word_chain"
}
```

```json
{
  "gameId": "game-e5f6g7h8",
  "mode": "word_chain",
  "status": "playing",
  "round": 1,
  "score": {"me": 50, "ai": 50},
  "message": "사과",
  "nextPrompt": "과",
  "wordHistory": ["사과"]
}
```

- `message`: AI가 제시한 시작 단어
- `nextPrompt`: 사용자가 입력해야 하는 첫 글자
- `wordHistory`: 지금까지 사용한 단어 목록

### 2. 단어 전송

`POST /api/games/{gameId}/turn`

```json
{
  "input": "과자"
}
```

```json
{
  "reply": "자동차",
  "accepted": true,
  "round": 2,
  "score": {"me": 50, "ai": 50},
  "nextPrompt": "차",
  "wordHistory": ["사과", "과자", "자동차"],
  "ended": false,
  "winner": null
}
```

- 사용자는 `nextPrompt`로 시작하는 단어를 입력한다.
- 한글 두 글자 이상이며 코드에 준비된 단어만 사용할 수 있다.
- 이미 나온 단어는 다시 사용할 수 없다.
- 잘못된 단어를 입력하면 `ended: true`, `winner: "ai"`로 종료된다.
- AI가 이어갈 단어가 없거나 사용자가 5라운드를 완료하면 사용자가 승리한다.

### 3. 규칙 위반 응답

규칙 위반은 HTTP 오류가 아니라 게임 패배 응답으로 반환한다.

```json
{
  "reply": "‘과’로 시작하는 단어를 입력해야 합니다.",
  "accepted": false,
  "round": 1,
  "score": {"me": 30, "ai": 70},
  "nextPrompt": null,
  "wordHistory": ["사과"],
  "ended": true,
  "winner": "ai"
}
```

### 4. 결과 조회

`GET /api/games/{gameId}/result`

```json
{
  "gameId": "game-e5f6g7h8",
  "mode": "word_chain",
  "winner": "me",
  "title": "끝말잇기 승리!",
  "finalScore": 70,
  "metrics": {
    "completedRounds": 5,
    "wordCount": 11,
    "longestWordLength": 3
  },
  "bestLine": "자동차",
  "reason": "5라운드를 모두 완료했습니다.",
  "wordHistory": ["사과", "과자", "자동차"]
}
```

---

## 오류 형식

```json
{
  "error": {
    "code": "GAME_NOT_FOUND",
    "message": "게임을 찾을 수 없습니다."
  }
}
```

| 상태 | 상황 |
| --- | --- |
| `400` | 아직 구현되지 않은 게임 또는 잘못된 요청 형식 |
| `404` | 게임을 찾을 수 없음 |
| `409` | 게임이 아직 끝나지 않았거나 이미 끝남 |
