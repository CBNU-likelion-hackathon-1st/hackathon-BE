"""게임 종류에 상관없이 사용하는 공통 API 라우트."""

from types import ModuleType

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.games import balance, battle, word_chain
from app.schemas.games import CreateGameRequest, TurnRequest
from app.services.gemini_games import GeminiGameError
from app.store import games, new_game_id


router = APIRouter(prefix="/api", tags=["games"])

GAME_HANDLERS: dict[str, ModuleType] = {
    "balance": balance,
    "battle": battle,
    "word_chain": word_chain,
}


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """모든 게임 API 오류를 같은 JSON 형식으로 반환한다."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def get_handler(mode: str) -> ModuleType | None:
    """게임 mode에 해당하는 로직 모듈을 반환한다."""
    return GAME_HANDLERS.get(mode)


@router.post("/games", status_code=201)
def create_game(payload: CreateGameRequest):
    """선택한 모드의 새 게임과 첫 질문 또는 단어를 반환한다."""
    handler = get_handler(payload.mode)
    if handler is None:
        return error_response(400, "GAME_NOT_IMPLEMENTED", "지원하지 않는 게임입니다.")

    game_id = new_game_id()
    try:
        session = (
            handler.start_game(payload.opponentType)
            if payload.mode == "battle"
            else handler.start_game()
        )
    except ValueError as error:
        return error_response(400, "INVALID_INPUT", str(error))
    session.update({"gameId": game_id, "mode": payload.mode})
    games[game_id] = session

    return {
        "gameId": game_id,
        "mode": payload.mode,
        **handler.get_start_response(session),
    }


@router.post("/games/{game_id}/turn")
def play_turn(game_id: str, payload: TurnRequest):
    """현재 게임 mode에 맞는 로직으로 한 턴을 처리한다."""
    session = games.get(game_id)
    if session is None:
        return error_response(404, "GAME_NOT_FOUND", "게임을 찾을 수 없습니다.")
    if session["status"] == "finished":
        return error_response(409, "GAME_ALREADY_FINISHED", "이미 종료된 게임입니다.")

    handler = get_handler(session["mode"])
    if handler is None:
        return error_response(400, "GAME_NOT_IMPLEMENTED", "아직 구현되지 않은 게임입니다.")

    try:
        return handler.play_turn(session, payload.input)
    except ValueError as error:
        return error_response(400, "INVALID_INPUT", str(error))
    except GeminiGameError:
        return error_response(
            503,
            "AI_SERVICE_ERROR",
            "AI 응답을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.",
        )


@router.get("/games/{game_id}/result")
def get_result(game_id: str):
    """현재 게임 mode에 맞는 최종 결과를 반환한다."""
    session = games.get(game_id)
    if session is None:
        return error_response(404, "GAME_NOT_FOUND", "게임을 찾을 수 없습니다.")
    if session["status"] != "finished":
        return error_response(409, "GAME_NOT_FINISHED", "아직 게임이 끝나지 않았습니다.")

    handler = get_handler(session["mode"])
    if handler is None:
        return error_response(400, "GAME_NOT_IMPLEMENTED", "아직 구현되지 않은 게임입니다.")
    return {"gameId": game_id, **handler.get_result(session)}
