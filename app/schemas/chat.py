from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|model)$")
    content: str = Field(min_length=1, max_length=2_000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
    persona_name: str = Field(default="땅콩이", min_length=1, max_length=30)
    persona_profile: str | None = Field(default=None, max_length=1_500)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)


class ChatResponse(BaseModel):
    reply: str
    model: str
