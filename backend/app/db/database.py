"""
Database configuration and session management.
Uses SQLAlchemy async with PostgreSQL via Supabase.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.core.config import settings


# Create async engine
engine_args = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
}

if "sqlite" not in settings.DATABASE_URL:
    engine_args.update({
        "pool_size": 10,
        "max_overflow": 20
    })

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_args
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    Ensures proper cleanup after request completion.
    Endpoints are responsible for calling commit() explicitly.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
