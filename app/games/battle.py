"""Gemini 페르소나와 점수 심사를 사용하는 말싸움 게임 로직."""

import json
import re
from pathlib import Path
from typing import Any

from app.services import gemini_battle


MAX_USER_TURNS = 5
DRAW_MARGIN = 3
RULES_FILE = Path(__file__).resolve().parents[1] / "data" / "battle_rules.json"

PERSONAS: dict[str, dict[str, Any]] = {
    "boss": {
        "label": "직장 상사",
        "description": "라떼는 말이야 직장 상사",
        "tags": ["꼰대퇴치", "격식"],
        "opening": "이 보고서, 이게 최선이야? 다시 설명해 봐.",
        "roleInstruction": (
            "성과와 근거를 중요하게 생각하는 까다로운 직장 상사다. "
            "단호한 존댓말로 업무 핑계를 따져 묻되 인신공격은 하지 않는다."
        ),
        "placeholder": "직장 상사에게 반박하기...",
        "quickReplies": ["근거부터 말씀해 주세요", "그 기준은 누가 정했나요?", "제 설명도 들어보시죠"],
    },
    "older_brother": {
        "label": "형",
        "description": "잔소리 만렙 현실 형",
        "tags": ["형제배틀", "반말"],
        "opening": "내가 너보다 오래 살아봐서 아는데, 그건 아니야.",
        "roleInstruction": (
            "현실적인 잔소리와 장난을 섞는 친형이다. 반말로 능청스럽게 받아치되 "
            "욕설이나 위협은 하지 않는다."
        ),
        "placeholder": "형에게 받아치기...",
        "quickReplies": ["나이 말고 근거는?", "형도 틀릴 때 있잖아", "그건 형 생각이고"],
    },
    "ex": {
        "label": "전애인",
        "description": "할 말 많은 전애인",
        "tags": ["미련없음", "팩트폭격"],
        "opening": "넌 아직도 네가 왜 차였는지 모르는구나?",
        "roleInstruction": (
            "눈치가 빠르고 차분한 전애인이다. 과거의 사소한 습관을 떠올리며 냉정하게 "
            "반박하되 모욕적이거나 집착하는 표현은 하지 않는다."
        ),
        "placeholder": "전애인에게 반박하기...",
        "quickReplies": ["그건 네 입장이고", "지금도 남 탓이네", "그래서 할 말은 그거야?"],
    },
}


def list_opponents() -> list[dict[str, object]]:
    """홈 화면의 상대 선택 카드에 필요한 공개 정보만 반환한다."""
    return [
        {
            "type": opponent_type,
            "name": profile["label"],
            "description": profile["description"],
            "tags": profile["tags"],
        }
        for opponent_type, profile in PERSONAS.items()
    ]


def load_battle_rules(file_path: Path = RULES_FILE) -> dict[str, tuple[str, ...]]:
    """로컬 반칙 판정용 단어 목록을 JSON에서 읽는다."""
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("말싸움 규칙 파일을 읽을 수 없습니다.") from error

    required_keys = ("profanity", "threats", "anger", "allowed")
    if not isinstance(payload, dict) or any(
        not isinstance(payload.get(key), list) or not payload[key]
        for key in required_keys
    ):
        raise RuntimeError("말싸움 규칙 파일 형식이 올바르지 않습니다.")
    if any(
        not isinstance(entry, str) or not entry.strip()
        for key in required_keys
        for entry in payload[key]
    ):
        raise RuntimeError("말싸움 규칙에는 빈 문자열을 넣을 수 없습니다.")

    return {key: tuple(payload[key]) for key in required_keys}


BATTLE_RULES = load_battle_rules()


def start_game(opponent_type: str | None) -> dict[str, Any]:
    """선택한 페르소나로 새로운 5턴 말싸움 상태를 만든다."""
    if not opponent_type:
        raise ValueError("말싸움은 opponentType을 선택해야 합니다.")
    if opponent_type not in PERSONAS:
        choices = ", ".join(PERSONAS)
        raise ValueError(f"opponentType은 {choices} 중 하나여야 합니다.")

    profile = PERSONAS[opponent_type]
    return {
        "status": "playing",
        "round": 1,
        "opponentType": opponent_type,
        "messages": [{"role": "assistant", "content": profile["opening"]}],
        "turns": [],
        "points": {"me": 0, "ai": 0},
        "score": {"me": 50, "ai": 50},
        "winner": None,
        "end_reason": None,
    }


def get_start_response(session: dict[str, Any]) -> dict[str, Any]:
    """채팅 화면에 필요한 상대 정보와 첫 대사를 반환한다."""
    profile = PERSONAS[session["opponentType"]]
    return {
        "status": session["status"],
        "round": session["round"],
        "maxRounds": MAX_USER_TURNS,
        "score": session["score"],
        "opponent": {
            "type": session["opponentType"],
            "name": profile["label"],
        },
        "message": profile["opening"],
        "placeholder": profile["placeholder"],
        "quickReplies": profile["quickReplies"],
    }


def play_turn(session: dict[str, Any], user_input: str) -> dict[str, Any]:
    """사용자 발언, 페르소나 답변, 심사 점수를 순서대로 처리한다."""
    if session["status"] == "finished":
        raise ValueError("이미 종료된 게임입니다.")

    text = user_input.strip()
    profile = PERSONAS[session["opponentType"]]
    local_violation = detect_critical_violation(text)
    if local_violation:
        return _finish_violation(
            session,
            offender="me",
            user_input=text,
            ai_reply="욕설이나 협박은 반칙이야. 이번 판은 네 패배야.",
            reason=local_violation,
        )

    ai_reply = gemini_battle.generate_persona_reply(
        profile["roleInstruction"],
        session["messages"],
        text,
    )
    ai_local_violation = detect_critical_violation(ai_reply)
    if ai_local_violation:
        return _finish_violation(
            session,
            offender="ai",
            user_input=text,
            ai_reply="상대가 반칙 표현을 사용해서 네가 이겼어.",
            reason=f"AI 답변에서 {ai_local_violation}",
        )

    judgement = gemini_battle.judge_turn(
        profile["label"],
        session["messages"],
        text,
        ai_reply,
    )
    user_judgement = dict(judgement["user"])
    ai_judgement = dict(judgement["ai"])
    user_judgement["aggressionLevel"] = max(
        int(user_judgement["aggressionLevel"]),
        detect_anger_level(text),
    )

    if is_critical_judgement(user_judgement):
        return _finish_violation(
            session,
            offender="me",
            user_input=text,
            ai_reply="과도한 욕설·협박·분노가 감지되어 이번 판은 네 패배야.",
            reason=str(user_judgement["reason"]),
        )
    if is_critical_judgement(ai_judgement):
        return _finish_violation(
            session,
            offender="ai",
            user_input=text,
            ai_reply="상대 답변이 규칙을 위반해서 네가 이겼어.",
            reason=str(ai_judgement["reason"]),
        )

    user_score, user_analysis = calculate_turn_score(user_judgement)
    ai_score, _ = calculate_turn_score(ai_judgement)
    turn = {
        "userInput": text,
        "aiReply": ai_reply,
        "userScore": user_score,
        "aiScore": ai_score,
        "analysis": user_analysis,
        "judgeReason": user_judgement["reason"],
        "violation": False,
    }
    session["turns"].append(turn)
    session["messages"].extend(
        [
            {"role": "user", "content": text},
            {"role": "assistant", "content": ai_reply},
        ]
    )
    session["points"]["me"] += user_score
    session["points"]["ai"] += ai_score
    session["score"] = score_gauge(session["points"])

    ended = len(session["turns"]) >= MAX_USER_TURNS
    if ended:
        _finish_by_score(session)
    else:
        session["round"] = len(session["turns"]) + 1

    return {
        "reply": ai_reply,
        "round": session["round"],
        "score": session["score"],
        "turnScore": {"me": user_score, "ai": ai_score},
        "analysis": user_analysis,
        "judgeReason": user_judgement["reason"],
        "quickReplies": profile["quickReplies"],
        "ended": ended,
        "winner": session["winner"],
    }


def calculate_turn_score(judgement: dict[str, object]) -> tuple[int, dict[str, object]]:
    """Gemini의 항목별 점수에 가중치와 분노 감점을 적용한다."""
    logic = _clamp_score(judgement.get("logic"))
    impact = _clamp_score(judgement.get("impact"))
    flow = _clamp_score(judgement.get("flow"))
    aggression_level = max(0, min(3, int(judgement.get("aggressionLevel", 0))))
    penalty = {0: 0, 1: 5, 2: 15, 3: 100}[aggression_level]
    base_score = round((logic * 0.4 + impact * 0.35 + flow * 0.25) * 10)
    final_score = max(0, base_score - penalty)
    return final_score, {
        "logic": logic * 10,
        "impact": impact * 10,
        "flow": flow * 10,
        "aggressionLevel": aggression_level,
        "angerPenalty": penalty,
    }


def detect_critical_violation(text: str) -> str | None:
    """명확한 욕설과 협박을 Gemini 호출 전에 빠르게 찾는다."""
    normalized = _normalize(text)
    for allowed_word in BATTLE_RULES["allowed"]:
        normalized = normalized.replace(_normalize(allowed_word), "")
    if any(_normalize(word) in normalized for word in BATTLE_RULES["profanity"]):
        return "욕설이 감지되었습니다."
    if any(_normalize(word) in normalized for word in BATTLE_RULES["threats"]):
        return "협박 표현이 감지되었습니다."
    return None


def detect_anger_level(text: str) -> int:
    """간단한 키워드와 느낌표로 분노 수준의 최솟값을 정한다."""
    normalized = _normalize(text)
    matches = sum(
        _normalize(word) in normalized for word in BATTLE_RULES["anger"]
    )
    if matches >= 2 or text.count("!") >= 3:
        return 2
    if matches == 1 or text.count("!") >= 2:
        return 1
    return 0


def is_critical_judgement(judgement: dict[str, object]) -> bool:
    """Gemini 심사에서 즉시 패배에 해당하는 위반을 확인한다."""
    violations = judgement.get("violations", [])
    return bool(violations) or int(judgement.get("aggressionLevel", 0)) >= 3


def score_gauge(points: dict[str, int]) -> dict[str, int]:
    """누적 원점수를 화면용 100% 게이지로 바꾼다."""
    total = points["me"] + points["ai"]
    if total <= 0:
        return {"me": 50, "ai": 50}
    my_score = round(points["me"] / total * 100)
    return {"me": my_score, "ai": 100 - my_score}


def get_result(session: dict[str, Any]) -> dict[str, Any]:
    """종료된 말싸움의 승패와 사용자 평균 능력치를 반환한다."""
    if session["status"] != "finished":
        raise ValueError("아직 게임이 끝나지 않았습니다.")

    valid_turns = [turn for turn in session["turns"] if not turn["violation"]]
    profile = PERSONAS[session["opponentType"]]
    if valid_turns:
        metrics = {
            key: round(sum(turn["analysis"][key] for turn in valid_turns) / len(valid_turns))
            for key in ("logic", "impact", "flow")
        }
        anger_penalty = sum(turn["analysis"]["angerPenalty"] for turn in valid_turns)
        best_line = max(valid_turns, key=lambda turn: turn["userScore"])["userInput"]
    else:
        metrics = {"logic": 0, "impact": 0, "flow": 0}
        anger_penalty = 0
        best_line = ""

    metrics.update(
        {
            "angerPenalty": anger_penalty,
            "completedRounds": len(session["turns"]),
            "violations": sum(turn["violation"] for turn in session["turns"]),
        }
    )
    title = {
        "me": "통쾌한 승리!",
        "ai": "아쉬운 패배!",
        "draw": "팽팽한 무승부!",
    }[session["winner"]]
    return {
        "mode": "battle",
        "opponentType": session["opponentType"],
        "opponentName": profile["label"],
        "winner": session["winner"],
        "title": title,
        "finalScore": session["score"]["me"],
        "metrics": metrics,
        "bestLine": best_line,
        "reason": session["end_reason"],
    }


def _finish_by_score(session: dict[str, Any]) -> None:
    difference = session["score"]["me"] - session["score"]["ai"]
    if difference > DRAW_MARGIN:
        winner = "me"
    elif difference < -DRAW_MARGIN:
        winner = "ai"
    else:
        winner = "draw"
    session["status"] = "finished"
    session["round"] = MAX_USER_TURNS
    session["winner"] = winner
    session["end_reason"] = "5라운드의 논리력, 타격감, 티키타카 점수를 합산했습니다."


def _finish_violation(
    session: dict[str, Any],
    *,
    offender: str,
    user_input: str,
    ai_reply: str,
    reason: str,
) -> dict[str, Any]:
    winner = "ai" if offender == "me" else "me"
    turn_score = {"me": 0, "ai": 100} if winner == "ai" else {"me": 100, "ai": 0}
    session["turns"].append(
        {
            "userInput": user_input,
            "aiReply": ai_reply,
            "userScore": turn_score["me"],
            "aiScore": turn_score["ai"],
            "analysis": {
                "logic": 0,
                "impact": 0,
                "flow": 0,
                "aggressionLevel": 3,
                "angerPenalty": 100,
            },
            "judgeReason": reason,
            "violation": True,
        }
    )
    session["messages"].extend(
        [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": ai_reply},
        ]
    )
    session["status"] = "finished"
    session["winner"] = winner
    session["end_reason"] = reason
    session["score"] = turn_score
    return {
        "reply": ai_reply,
        "round": session["round"],
        "score": session["score"],
        "turnScore": turn_score,
        "analysis": session["turns"][-1]["analysis"],
        "judgeReason": reason,
        "quickReplies": [],
        "ended": True,
        "winner": winner,
    }


def _normalize(text: str) -> str:
    return re.sub(r"[^0-9a-zㄱ-ㅎㅏ-ㅣ가-힣]", "", text.lower())


def _clamp_score(value: object) -> int:
    return max(0, min(10, int(value or 0)))
