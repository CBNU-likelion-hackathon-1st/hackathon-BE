"""게임 상태를 임시로 보관하는 메모리 저장소."""

from typing import Any
from uuid import uuid4


games: dict[str, dict[str, Any]] = {}


def new_game_id() -> str:
    """충돌 가능성이 낮은 짧은 게임 ID를 만든다."""
    return f"game-{uuid4().hex[:8]}"
