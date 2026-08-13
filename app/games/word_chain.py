"""끝말잇기 규칙과 Gemini 단어 판정 로직.

기존 작업을 게임별 파일 구조에 맞춰 보존했다. 전체 게임 진행 API는 추후 연결한다.
"""

from app.services.gemini_games import GeminiGameError, generate_json


IMPLEMENTED = False


def validate_word_chain(previous_word: str, proposed_word: str) -> dict[str, object]:
    """규칙을 먼저 확인하고 단어의 자연스러움은 Gemini로 판정한다."""
    required_syllable = previous_word[-1]
    if proposed_word[0] != required_syllable:
        return {
            "valid": False,
            "reason": f"‘{required_syllable}’로 시작하는 단어를 입력해 주세요.",
            "required_syllable": required_syllable,
            "next_syllable": None,
        }

    prompt = f"""
당신은 한국어 끝말잇기 심판입니다. 이전 단어는 '{previous_word}', 제출 단어는
'{proposed_word}'입니다. 제출 단어가 사전에 실린 일반적인 한국어 단어이고, 고유명사·비속어·문장·임의의 조합이 아닌지 판정하세요.
반드시 아래 JSON 객체만 반환하세요.
{{"valid": true 또는 false, "reason": "한국어로 30자 이내의 짧은 판정 이유"}}
""".strip()
    result = generate_json(prompt)
    valid = result.get("valid") is True
    reason = result.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        reason = "사용 가능한 단어입니다." if valid else "일반적인 한국어 단어로 확인되지 않았습니다."

    return {
        "valid": valid,
        "reason": reason.strip(),
        "required_syllable": required_syllable,
        "next_syllable": proposed_word[-1] if valid else None,
    }
