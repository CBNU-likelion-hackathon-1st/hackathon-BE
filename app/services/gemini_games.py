"""게임 모듈이 함께 사용하는 Gemini JSON 호출 도우미."""

import json
from functools import lru_cache

from google import genai
from google.genai import types

from app.core.config import get_settings
class GeminiGameError(RuntimeError):
    """Gemini 응답을 안전하게 처리할 수 없을 때 발생한다."""


@lru_cache
def get_gemini_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key.get_secret_value())


def generate_json(prompt: str) -> dict[str, object]:
    """Gemini의 JSON 응답을 파싱해 반환한다."""
    settings = get_settings()
    try:
        response = get_gemini_client().models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        if not response.text:
            raise GeminiGameError("Gemini가 비어 있는 응답을 반환했습니다.")
        payload = json.loads(response.text)
    except GeminiGameError:
        raise
    except Exception as error:
        raise GeminiGameError("Gemini 응답을 가져오지 못했습니다.") from error

    if not isinstance(payload, dict):
        raise GeminiGameError("Gemini 응답 형식이 올바르지 않습니다.")
    return payload
