"""JSON 단어 목록으로 동작하는 끝말잇기 게임 로직."""

import json
from pathlib import Path
from random import Random
from typing import Any


MAX_USER_TURNS = 5
WORD_DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "word_chain_words.json"


def load_word_data(file_path: Path = WORD_DATA_FILE) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """JSON에서 시작 단어와 전체 단어를 읽고 형식을 검사한다."""
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("끝말잇기 단어 파일을 읽을 수 없습니다.") from error

    if not isinstance(payload, dict):
        raise RuntimeError("끝말잇기 단어 파일은 JSON 객체여야 합니다.")

    start_words = payload.get("start_words")
    words = payload.get("words")
    if not isinstance(start_words, list) or not isinstance(words, list):
        raise RuntimeError("단어 파일에는 start_words와 words 목록이 필요합니다.")

    all_entries = [*start_words, *words]
    if not start_words or not words:
        raise RuntimeError("시작 단어와 일반 단어를 한 개 이상 등록해야 합니다.")
    if any(
        not isinstance(word, str)
        or len(word) < 2
        or not all("가" <= character <= "힣" for character in word)
        for word in all_entries
    ):
        raise RuntimeError("모든 끝말잇기 단어는 한글 두 글자 이상이어야 합니다.")
    if len(start_words) != len(set(start_words)) or len(words) != len(set(words)):
        raise RuntimeError("단어 목록에 중복 단어가 있습니다.")
    if any(not any(word.startswith(start_word[-1]) for word in words) for start_word in start_words):
        raise RuntimeError("이어갈 단어가 없는 시작 단어가 있습니다.")

    return tuple(start_words), tuple(words)


START_WORDS, WORDS = load_word_data()
WORD_SET = frozenset(WORDS)


def start_game(rng: Random | None = None) -> dict[str, Any]:
    """시작 단어를 하나 골라 새로운 끝말잇기 상태를 만든다."""
    randomizer = rng or Random()
    start_word = randomizer.choice(START_WORDS)
    return {
        "status": "playing",
        "round": 1,
        "last_word": start_word,
        "used_words": [start_word],
        "user_words": [],
        "user_turns": 0,
        "winner": None,
        "end_reason": None,
        "score": {"me": 50, "ai": 50},
    }


def get_start_response(session: dict[str, Any]) -> dict[str, Any]:
    """게임 시작 화면에 필요한 첫 단어와 다음 글자를 반환한다."""
    start_word = session["last_word"]
    return {
        "status": session["status"],
        "round": session["round"],
        "score": session["score"],
        "message": start_word,
        "nextPrompt": start_word[-1],
        "wordHistory": session["used_words"],
    }


def validate_word(session: dict[str, Any], proposed_word: str) -> tuple[bool, str]:
    """첫 글자, 중복, 글자 형식, 준비된 단어 목록을 순서대로 검사한다."""
    if len(proposed_word) < 2:
        return False, "두 글자 이상의 단어를 입력해 주세요."
    if not all("가" <= character <= "힣" for character in proposed_word):
        return False, "한글 단어만 입력할 수 있습니다."

    required_syllable = session["last_word"][-1]
    if proposed_word[0] != required_syllable:
        return False, f"‘{required_syllable}’로 시작하는 단어를 입력해야 합니다."
    if proposed_word in session["used_words"]:
        return False, "이미 나온 단어입니다."
    if proposed_word not in WORD_SET:
        return False, "현재 단어 목록에서 확인되지 않는 단어입니다."
    return True, "사용 가능한 단어입니다."


def find_ai_word(session: dict[str, Any], required_syllable: str) -> str | None:
    """필요한 글자로 시작하고 아직 사용하지 않은 AI 단어를 찾는다."""
    return next(
        (
            word
            for word in WORDS
            if word.startswith(required_syllable) and word not in session["used_words"]
        ),
        None,
    )


def play_turn(session: dict[str, Any], user_input: str) -> dict[str, Any]:
    """사용자 단어를 판정하고 AI 단어 또는 게임 종료 결과를 반환한다."""
    if session["status"] == "finished":
        raise ValueError("이미 종료된 게임입니다.")

    proposed_word = "".join(user_input.split())
    valid, reason = validate_word(session, proposed_word)
    if not valid:
        _finish_game(session, winner="ai", reason=reason)
        return {
            "reply": reason,
            "accepted": False,
            "round": session["round"],
            "score": session["score"],
            "nextPrompt": None,
            "wordHistory": session["used_words"],
            "ended": True,
            "winner": session["winner"],
        }

    session["used_words"].append(proposed_word)
    session["user_words"].append(proposed_word)
    session["user_turns"] += 1
    session["last_word"] = proposed_word

    ai_word = find_ai_word(session, proposed_word[-1])
    if ai_word is None:
        _finish_game(session, winner="me", reason="AI가 이어갈 단어를 찾지 못했습니다.")
        return {
            "reply": "생각나는 단어가 없어! 네가 이겼어.",
            "accepted": True,
            "round": session["round"],
            "score": session["score"],
            "nextPrompt": None,
            "wordHistory": session["used_words"],
            "ended": True,
            "winner": session["winner"],
        }

    session["used_words"].append(ai_word)
    session["last_word"] = ai_word

    if session["user_turns"] >= MAX_USER_TURNS:
        _finish_game(session, winner="me", reason="5라운드를 모두 완료했습니다.")
        return {
            "reply": ai_word,
            "accepted": True,
            "round": session["round"],
            "score": session["score"],
            "nextPrompt": None,
            "wordHistory": session["used_words"],
            "ended": True,
            "winner": session["winner"],
        }

    session["round"] = session["user_turns"] + 1
    return {
        "reply": ai_word,
        "accepted": True,
        "round": session["round"],
        "score": session["score"],
        "nextPrompt": ai_word[-1],
        "wordHistory": session["used_words"],
        "ended": False,
        "winner": None,
    }


def get_result(session: dict[str, Any]) -> dict[str, Any]:
    """종료된 끝말잇기의 승패와 단어 기록 요약을 반환한다."""
    if session["status"] != "finished":
        raise ValueError("아직 게임이 끝나지 않았습니다.")

    longest_word = max(session["user_words"], key=len, default=session["used_words"][0])
    title = "끝말잇기 승리!" if session["winner"] == "me" else "끝말잇기 패배!"
    return {
        "mode": "word_chain",
        "winner": session["winner"],
        "title": title,
        "finalScore": session["score"]["me"],
        "metrics": {
            "completedRounds": session["user_turns"],
            "wordCount": len(session["used_words"]),
            "longestWordLength": len(longest_word),
        },
        "bestLine": longest_word,
        "reason": session["end_reason"],
        "wordHistory": session["used_words"],
    }


def _finish_game(session: dict[str, Any], winner: str, reason: str) -> None:
    """종료 상태와 최종 점수를 한곳에서 설정한다."""
    session["status"] = "finished"
    session["winner"] = winner
    session["end_reason"] = reason
    session["score"] = {"me": 70, "ai": 30} if winner == "me" else {"me": 30, "ai": 70}
