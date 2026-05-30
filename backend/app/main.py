import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.exceptions import RedisError

from app.api.admin import router as admin_router
from app.api.routes import router
from app.config import get_settings
from app.db.session import init_db
from app.services.cache import cache_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.audit_data_dir).mkdir(parents=True, exist_ok=True)
    init_db()
    try:
        await cache_service.connect()
    except (RedisError, OSError) as exc:
        logger.info("Redis unavailable at startup (%s); cache and rate limits use in-memory fallback", exc)
    yield
    await cache_service.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.pipeline_version, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    return app


app = create_app()
