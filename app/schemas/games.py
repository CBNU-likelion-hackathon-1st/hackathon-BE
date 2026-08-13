"""공통 게임 API의 요청 스키마."""

from typing import Literal

from pydantic import BaseModel, Field


class CreateGameRequest(BaseModel):
    mode: Literal["battle", "word_chain", "balance"]
    opponentType: str | None = None


class TurnRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=200)
