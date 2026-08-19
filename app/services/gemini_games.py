"""게임 모듈이 함께 사용하는 Gemini JSON 호출 도우미."""

import json
import logging
import time
from functools import lru_cache

from google import genai
from google.genai import types

from app.core.config import get_settings


logger = logging.getLogger(__name__)

GEMINI_MAX_ATTEMPTS = 3
GEMINI_RETRY_BASE_SECONDS = 0.5
GEMINI_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


class GeminiGameError(RuntimeError):
    """Gemini 응답을 안전하게 처리할 수 없을 때 발생한다."""


@lru_cache
def get_gemini_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key.get_secret_value())


def _get_status_code(error: Exception) -> int | None:
    """Gemini SDK 예외에서 HTTP 상태 코드를 안전하게 읽는다."""
    code = getattr(error, "code", None)
    if isinstance(code, int):
        return code

    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    return status_code if isinstance(status_code, int) else None


def _generate_content_with_retry(**kwargs: object):
    """요청량 급증 등 일시적인 Gemini 오류에 한해 지수 백오프로 재시도한다."""
    for attempt in range(1, GEMINI_MAX_ATTEMPTS + 1):
        try:
            return get_gemini_client().models.generate_content(**kwargs)
        except Exception as error:
            status_code = _get_status_code(error)
            should_retry = (
                status_code in GEMINI_RETRYABLE_STATUS_CODES
                and attempt < GEMINI_MAX_ATTEMPTS
            )
            if not should_retry:
                logger.exception(
                    "Gemini request failed after %s attempt(s) (status=%s)",
                    attempt,
                    status_code,
                )
                raise

            delay = GEMINI_RETRY_BASE_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "Transient Gemini error; retrying in %.1fs "
                "(attempt=%s/%s, status=%s)",
                delay,
                attempt,
                GEMINI_MAX_ATTEMPTS,
                status_code,
            )
            time.sleep(delay)

    raise RuntimeError("Gemini 재시도 횟수를 초과했습니다.")


def generate_json(
    prompt: str,
    *,
    system_instruction: str | None = None,
    temperature: float = 0.2,
    response_schema: type | dict[str, object] | None = None,
) -> dict[str, object]:
    """Gemini의 JSON 응답을 파싱해 반환한다."""
    settings = get_settings()
    try:
        response = _generate_content_with_retry(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=temperature,
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
