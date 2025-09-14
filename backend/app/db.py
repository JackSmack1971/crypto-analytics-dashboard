"""Database engine and session utilities."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    create_async_engine)
from sqlalchemy.orm import sessionmaker


def create_engine(db_url: str) -> AsyncEngine:
    """Create an async SQLAlchemy engine.

    Args:
        db_url: Database connection URL.

    Returns:
        Configured :class:`~sqlalchemy.ext.asyncio.AsyncEngine`.

    Raises:
        RuntimeError: If ``db_url`` is falsy.
    """

    if not db_url:
        raise RuntimeError("Database URL is required")
    return create_async_engine(db_url, future=True)


def create_session_factory(engine: AsyncEngine) -> sessionmaker[AsyncSession]:
    """Create an async session factory bound to ``engine``."""

    return sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def session_scope(
    session_factory: sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope around a series of operations."""

    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
