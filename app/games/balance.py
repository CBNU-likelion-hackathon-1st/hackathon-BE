"""DB와 Gemini 없이 동작하는 밸런스 게임 로직."""

from copy import deepcopy
from random import Random
from typing import Any


ROUND_COUNT = 3

QUESTIONS = (
    {
        "id": "food-01",
        "question": "평생 하나만 먹을 수 있다면?",
        "choices": ["평생 라면만 먹기", "평생 치킨만 먹기"],
        "ai_choice": 1,
        "reaction": "치킨은 매일 다른 맛으로 먹을 수 있잖아!",
    },
    {
        "id": "message-01",
        "question": "더 신경 쓰이는 답장은?",
        "choices": ["읽고 답장 안 하기", "안 읽고 하루 지나기"],
        "ai_choice": 0,
        "reaction": "읽었으면 한마디라도 해줘야지.",
    },
    {
        "id": "season-01",
        "question": "더 견디기 힘든 것은?",
        "choices": ["에어컨 없는 여름", "히터 없는 겨울"],
        "ai_choice": 0,
        "reaction": "더운 건 정말 피할 곳이 없어.",
    },
    {
        "id": "travel-01",
        "question": "휴가를 떠난다면?",
        "choices": ["친구 10명과 단체 여행", "혼자 조용한 호캉스"],
        "ai_choice": 1,
        "reaction": "휴가에서는 아무 일정도 없는 게 최고야.",
    },
    {
        "id": "time-01",
        "question": "하나의 능력을 가질 수 있다면?",
        "choices": ["10분 전으로 돌아가기", "10분 뒤 미래 보기"],
        "ai_choice": 0,
        "reaction": "실수한 말을 바로 주워 담을 수 있잖아.",
    },
    {
        "id": "work-01",
        "question": "둘 중 하나를 꼭 골라야 한다면?",
        "choices": ["월요일에 야근하기", "토요일 오전에 출근하기"],
        "ai_choice": 0,
        "reaction": "주말만큼은 무조건 지키고 싶어.",
    },
)


def start_game(rng: Random | None = None) -> dict[str, Any]:
    """질문 3개를 골라 새로운 게임 상태를 만든다."""
    randomizer = rng or Random()
    questions = deepcopy(randomizer.sample(list(QUESTIONS), ROUND_COUNT))
    return {
        "status": "playing",
        "round": 1,
        "current_index": 0,
        "questions": questions,
        "answers": [],
        "match_count": 0,
        "score": {"me": 50, "ai": 50},
    }


def current_prompt(session: dict[str, Any]) -> dict[str, Any] | None:
    """현재 라운드의 질문과 선택지를 프론트엔드 형식으로 반환한다."""
    index = session["current_index"]
    if index >= len(session["questions"]):
        return None

    question = session["questions"][index]
    return {
        "id": question["id"],
        "question": question["question"],
        "choices": question["choices"],
    }


def play_turn(session: dict[str, Any], user_input: str) -> dict[str, Any]:
    """선택을 검증하고 AI 반응, 점수, 다음 질문을 만든다."""
    if session["status"] == "finished":
        raise ValueError("이미 종료된 게임입니다.")

    question = session["questions"][session["current_index"]]
    selected_choice = user_input.strip()
    if selected_choice not in question["choices"]:
        raise ValueError("현재 질문의 두 선택지 중 하나를 골라주세요.")

    ai_choice = question["choices"][question["ai_choice"]]
    matched = selected_choice == ai_choice

    if matched:
        session["match_count"] += 1
        session["score"]["me"] += 5
        session["score"]["ai"] -= 5
        reply = f"오, 나랑 같은 선택이네! {question['reaction']}"
    else:
        session["score"]["me"] -= 5
        session["score"]["ai"] += 5
        reply = f"나는 '{ai_choice}' 쪽인데? {question['reaction']}"

    session["answers"].append(
        {
            "questionId": question["id"],
            "selectedChoice": selected_choice,
            "aiChoice": ai_choice,
            "matched": matched,
        }
    )
    session["current_index"] += 1

    ended = session["current_index"] >= len(session["questions"])
    if ended:
        session["status"] = "finished"
        session["round"] = ROUND_COUNT
    else:
        session["round"] = session["current_index"] + 1

    return {
        "reply": reply,
        "round": session["round"],
        "score": session["score"],
        "nextPrompt": current_prompt(session),
        "ended": ended,
    }


def get_result(session: dict[str, Any]) -> dict[str, Any]:
    """종료된 게임의 취향 일치도와 최종 점수를 반환한다."""
    if session["status"] != "finished":
        raise ValueError("아직 게임이 끝나지 않았습니다.")

    agreement = round(session["match_count"] / ROUND_COUNT * 100)
    my_score = session["score"]["me"]
    ai_score = session["score"]["ai"]
    winner = "me" if my_score > ai_score else "ai" if my_score < ai_score else "draw"

    if agreement >= 67:
        title = "AI와 취향이 통했어요!"
    elif agreement >= 34:
        title = "반은 같고 반은 다르네요!"
    else:
        title = "AI와 완전히 다른 취향!"

    return {
        "mode": "balance",
        "winner": winner,
        "title": title,
        "finalScore": my_score,
        "metrics": {
            "agreement": agreement,
            "difference": 100 - agreement,
            "completedRounds": len(session["answers"]),
        },
        "bestLine": session["answers"][-1]["selectedChoice"],
    }
