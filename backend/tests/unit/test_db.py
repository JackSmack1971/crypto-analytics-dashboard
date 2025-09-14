"""Database session tests using in-memory SQLite."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func, select

from app.db import create_engine, create_session_factory

Base = declarative_base()


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = create_session_factory(engine)
    async with Session() as sess:
        yield sess
    await engine.dispose()


@pytest.mark.asyncio
async def test_engine_connects():
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_simple_crud(session: AsyncSession):
    item = Item(name="foo")
    session.add(item)
    await session.commit()
    assert item.id is not None

    item.name = "bar"
    await session.commit()
    fetched = await session.get(Item, item.id)
    assert fetched and fetched.name == "bar"

    await session.delete(fetched)
    await session.commit()
    assert await session.get(Item, item.id) is None


@pytest.mark.asyncio
async def test_rollback_on_error(session: AsyncSession):
    item = Item(name="ok")
    session.add(item)
    await session.commit()

    try:
        session.add(Item(id=item.id, name="dup"))
        await session.commit()
    except Exception:
        await session.rollback()

    count = (await session.execute(select(func.count()).select_from(Item))).scalar()
    assert count == 1
