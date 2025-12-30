"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.config import settings


# Convert postgresql:// to postgresql+asyncpg:// for async
async_database_url = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Async engine for SQLAlchemy 2.0
async_engine = create_async_engine(
    async_database_url,
    echo=settings.debug,
    future=True,
)

# Sync engine for Alembic migrations
sync_engine = create_engine(
    settings.database_url,
    echo=settings.debug,
)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


async def get_db() -> AsyncSession:
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

