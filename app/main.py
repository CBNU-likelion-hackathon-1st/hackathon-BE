from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 시작 시 환경 변수 누락을 빠르게 확인한다. API 호출은 실제 채팅 요청에서만 한다.
    get_settings()
    yield


settings = get_settings()
app = FastAPI(
    title="땅콩이 API",
    description="AI 말싸움 미니게임 백엔드",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(chat_router, prefix="/api/v1")
