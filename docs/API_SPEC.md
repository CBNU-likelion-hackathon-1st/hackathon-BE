# 땅콩이 MVP API 명세서

- Base URL: `http://127.0.0.1:5000`
- 구현 완료: 말싸움, 밸런스 게임, 끝말잇기
- 게임 상태: 서버 메모리에 저장하며 서버 재시작 시 초기화

## 공통 API

| Method | URL | 설명 |
| --- | --- | --- |
| `GET` | `/api/battle/opponents` | 홈 화면의 말싸움 상대 목록 조회 |
| `POST` | `/api/games` | `mode`에 맞는 게임 시작 |
| `POST` | `/api/games/{gameId}/turn` | 한 턴 진행 |
| `GET` | `/api/games/{gameId}/result` | 종료된 게임 결과 조회 |

---

## 말싸움

### 1. 상대 목록 조회

`GET /api/battle/opponents`

요청 Body는 없다.

```json
{
  "opponents": [
    {
      "type": "boss",
      "name": "직장 상사",
      "description": "라떼는 말이야 직장 상사",
      "tags": ["꼰대퇴치", "격식"]
    },
    {
      "type": "older_brother",
      "name": "형",
      "description": "잔소리 만렙 현실 형",
      "tags": ["형제배틀", "반말"]
    },
    {
      "type": "ex",
      "name": "전애인",
      "description": "할 말 많은 전애인",
      "tags": ["미련없음", "팩트폭격"]
    }
  ],
  "count": 3
}
```

프론트는 선택한 카드의 `type`을 게임 시작 요청의 `opponentType`으로 보낸다.

### 2. 게임 시작

`POST /api/games`

```json
{
  "mode": "battle",
  "opponentType": "boss"
}
```

`opponentType`은 아래 3개만 사용할 수 있다.

| 값 | 역할 |
| --- | --- |
| `boss` | 직장 상사 |
| `older_brother` | 형 |
| `ex` | 전애인 |

```json
{
  "gameId": "game-b1c2d3e4",
  "mode": "battle",
  "status": "playing",
  "round": 1,
  "maxRounds": 5,
  "score": {"me": 50, "ai": 50},
  "opponent": {"type": "boss", "name": "직장 상사"},
  "message": "이 보고서, 이게 최선이야? 다시 설명해 봐.",
  "placeholder": "직장 상사에게 반박하기...",
  "quickReplies": [
    "근거부터 말씀해 주세요",
    "그 기준은 누가 정했나요?",
    "제 설명도 들어보시죠"
  ]
}
```

### 3. 대사 전송

`POST /api/games/{gameId}/turn`

```json
{
  "input": "지난달보다 성과가 20% 올랐습니다."
}
```

```json
{
  "reply": "수치는 좋아졌지만 목표를 달성했는지가 더 중요하지 않겠어요?",
  "round": 2,
  "score": {"me": 56, "ai": 44},
  "turnScore": {"me": 80, "ai": 64},
  "analysis": {
    "logic": 80,
    "impact": 70,
    "flow": 80,
    "aggressionLevel": 0,
    "angerPenalty": 0
  },
  "judgeReason": "수치 근거로 상대의 지적을 잘 받아쳤습니다.",
  "quickReplies": [
    "근거부터 말씀해 주세요",
    "그 기준은 누가 정했나요?",
    "제 설명도 들어보시죠"
  ],
  "ended": false,
  "winner": null
}
```

- Gemini의 상대 답변 생성과 점수 심사는 별도 요청으로 실행된다.
- 점수는 `논리력 40% + 타격감 35% + 티키타카 25% - 분노 감점`이다.
- 가벼운 짜증은 5점, 공격적인 분노는 15점을 감점한다.
- 욕설·협박·혐오 표현은 즉시 패배 처리한다.
- 5라운드 후 사용자와 AI의 누적 점수를 비교한다. 화면용 점수 차이가 3점 이하면 무승부다.

### 4. 결과 조회

`GET /api/games/{gameId}/result`

```json
{
  "gameId": "game-b1c2d3e4",
  "mode": "battle",
  "opponentType": "boss",
  "opponentName": "직장 상사",
  "winner": "me",
  "title": "통쾌한 승리!",
  "finalScore": 56,
  "metrics": {
    "logic": 82,
    "impact": 76,
    "flow": 79,
    "angerPenalty": 0,
    "completedRounds": 5,
    "violations": 0
  },
  "bestLine": "지난달보다 성과가 20% 올랐습니다.",
  "reason": "5라운드의 논리력, 타격감, 티키타카 점수를 합산했습니다."
}
```

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
- 한글 두 글자 이상이며 `app/data/word_chain_words.json`에 준비된 단어만 사용할 수 있다.
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
| `503` | Gemini 응답 생성 또는 심사 실패 |
