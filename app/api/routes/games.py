"""게임 종류에 상관없이 사용하는 공통 API 라우트."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.games import balance
from app.schemas.games import CreateGameRequest, TurnRequest
from app.store import games, new_game_id


router = APIRouter(prefix="/api", tags=["games"])


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """모든 게임 API 오류를 같은 JSON 형식으로 반환한다."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


@router.post("/games", status_code=201)
def create_game(payload: CreateGameRequest):
    """선택한 모드의 새 게임을 만든다. 현재는 밸런스 게임만 지원한다."""
    if payload.mode != "balance":
        return error_response(
            400,
            "GAME_NOT_IMPLEMENTED",
            "현재는 밸런스 게임만 이용할 수 있습니다.",
        )

    game_id = new_game_id()
    session = balance.start_game()
    session.update({"gameId": game_id, "mode": payload.mode})
    games[game_id] = session

    return {
        "gameId": game_id,
        "mode": payload.mode,
        "status": session["status"],
        "round": session["round"],
        "score": session["score"],
        "message": "둘 중 하나를 골라보세요!",
        "nextPrompt": balance.current_prompt(session),
    }


@router.post("/games/{game_id}/turn")
def play_turn(game_id: str, payload: TurnRequest):
    """사용자 선택을 처리하고 다음 질문 또는 종료 여부를 반환한다."""
    session = games.get(game_id)
    if session is None:
        return error_response(404, "GAME_NOT_FOUND", "게임을 찾을 수 없습니다.")
    if session["status"] == "finished":
        return error_response(409, "GAME_ALREADY_FINISHED", "이미 종료된 게임입니다.")

    try:
        return balance.play_turn(session, payload.input)
    except ValueError as error:
        return error_response(400, "INVALID_CHOICE", str(error))


@router.get("/games/{game_id}/result")
def get_result(game_id: str):
    """종료된 게임의 결과 화면 데이터를 반환한다."""
    session = games.get(game_id)
    if session is None:
        return error_response(404, "GAME_NOT_FOUND", "게임을 찾을 수 없습니다.")
    if session["status"] != "finished":
        return error_response(409, "GAME_NOT_FINISHED", "아직 게임이 끝나지 않았습니다.")

    return {"gameId": game_id, **balance.get_result(session)}
