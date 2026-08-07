from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/database")
def database_health_check() -> dict[str, str]:
    """MySQL 연결 상태만 확인하며, 서비스 데이터를 조회하지 않는다."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except (RuntimeError, SQLAlchemyError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="데이터베이스에 연결할 수 없습니다.",
        ) from error

    return {"status": "ok", "database": "connected"}
