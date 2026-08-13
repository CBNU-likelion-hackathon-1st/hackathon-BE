# 땅콩이 MVP API 명세서

- Base URL: `http://localhost:5000`
- 현재 구현 완료: 밸런스 게임
- 게임 상태: 서버 메모리에 저장하며 서버 재시작 시 초기화

## 1. 밸런스 게임 시작

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

## 2. 한 턴 진행

`POST /api/games/{gameId}/turn`

`input`에는 현재 `nextPrompt.choices` 중 하나를 그대로 보낸다.

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

## 3. 결과 조회

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
| `400` | 잘못된 선택 또는 아직 구현되지 않은 게임 |
| `404` | 게임을 찾을 수 없음 |
| `409` | 게임이 아직 끝나지 않았거나 이미 끝남 |
