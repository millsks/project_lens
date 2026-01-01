"""Database session configuration.

Provides async SQLAlchemy session management for PostgreSQL.
"""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine as sa_create_async_engine
from sqlalchemy.pool import NullPool


def get_database_url() -> str:
    """Get database URL from environment.

    Returns:
        PostgreSQL connection URL

    Raises:
        ValueError: If DATABASE_URL not set
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        # Fallback to constructing from individual vars
        user = os.getenv("POSTGRES_USER", "lens")
        password = os.getenv("POSTGRES_PASSWORD", "lens_dev_password")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "lens")

        url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    # Ensure using asyncpg driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url


def create_async_engine(database_url: str | None = None, **kwargs):
    """Create async SQLAlchemy engine.

    Args:
        database_url: PostgreSQL connection URL (uses env if None)
        **kwargs: Additional engine arguments

    Returns:
        Async SQLAlchemy engine
    """
    url = database_url or get_database_url()

    # Default engine configuration
    engine_config = {
        "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
        "pool_pre_ping": True,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    }

    # Override with provided kwargs
    engine_config.update(kwargs)

    # Use NullPool for testing to avoid connection issues
    if os.getenv("TESTING", "false").lower() == "true":
        engine_config["poolclass"] = NullPool

    return sa_create_async_engine(url, **engine_config)


# Global session maker (created once per application)
_engine = None
_session_maker = None


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create the global session maker.

    Returns:
        Async session maker
    """
    global _engine, _session_maker

    if _session_maker is None:
        _engine = create_async_engine()
        _session_maker = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    return _session_maker


# Convenience alias
async_session_maker = get_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session (for FastAPI dependency injection).

    Yields:
        Async SQLAlchemy session
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
