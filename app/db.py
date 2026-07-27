import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db(max_attempts: int = 30, delay_seconds: float = 2.0) -> None:
    """Create tables, retrying while PostgreSQL is still starting."""
    from app import models  # noqa: F401

    for attempt in range(1, max_attempts + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database schema is ready")
            return
        except Exception:
            if attempt == max_attempts:
                raise
            logger.warning("Database unavailable, retry %s/%s", attempt, max_attempts)
            await asyncio.sleep(delay_seconds)
