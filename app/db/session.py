from functools import lru_cache
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    database_url = get_settings().database_url
    if not database_url:
        raise RuntimeError("DATABASE_URL 환경 변수가 설정되지 않았습니다.")

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=3_600,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    """라우터에서 사용할 데이터베이스 세션 의존성."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
