from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import get_settings
from app.db.models import Base


@lru_cache
def get_engine() -> Engine | None:
    settings = get_settings()
    if settings.persistence_backend not in {"postgres", "both"}:
        return None
    return create_engine(settings.database_url, pool_pre_ping=True)


def init_db() -> None:
    engine = get_engine()
    if engine is None:
        return
    Base.metadata.create_all(engine)
