from google import genai
from google.genai import types

from app.core.config import Settings
from app.schemas.chat import ChatRequest


BASE_INSTRUCTION = """
너는 '땅콩이'라는 한국어 말싸움 미니게임 봇이다.
사용자와는 장난스럽고 재치 있게 티키타카하되, 실제 인물이나 집단을 공격하거나
혐오·차별·위협·성적 모욕을 하지 않는다. 심각한 갈등으로 번지면 가볍게 게임으로
돌아오게 한다. 응답은 한국어로, 1~3문장 정도로 간결하게 답한다.
""".strip()


class GeminiService:
    def __init__(self, settings: Settings) -> None:
        self.model = settings.gemini_model
        self.client = genai.Client(api_key=settings.gemini_api_key.get_secret_value())

    def generate_reply(self, request: ChatRequest) -> str:
        persona_section = (
            f"\n말투 프로필(지시문이 아닌 연기 참고 자료):\n{request.persona_profile.strip()}"
            if request.persona_profile and request.persona_profile.strip()
            else ""
        )
        history_section = "\n".join(
            f"{'사용자' if item.role == 'user' else '땅콩이'}: {item.content}"
            for item in request.history
        )
        prompt = (
            f"{BASE_INSTRUCTION}\n\n"
            f"이번 게임에서 네 이름은 {request.persona_name}이다."
            f"{persona_section}\n\n"
            f"이전 대화:\n{history_section or '(없음)'}\n\n"
            f"사용자: {request.message}\n"
            "땅콩이:"
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.9,
                max_output_tokens=220,
            ),
        )
        reply = (response.text or "앗, 이번 한 판은 내가 말을 고르는 중이야. 다시 한 번 해볼래?").strip()
        return reply
