"""
Generic CRUD repository.

## Traceability
Feature: F001-F009 — All features
"""
from __future__ import annotations

from typing import TypeVar, Generic, Type, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    async def get_by_id(self, session: AsyncSession, entity_id: str) -> Optional[T]:
        result = await session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession, **filters) -> list[T]:
        query = select(self.model)
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, **kwargs) -> T:
        instance = self.model(**kwargs)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def update(self, session: AsyncSession, entity_id: str, **kwargs) -> Optional[T]:
        instance = await self.get_by_id(session, entity_id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def delete(self, session: AsyncSession, entity_id: str) -> bool:
        instance = await self.get_by_id(session, entity_id)
        if instance is None:
            return False
        await session.delete(instance)
        await session.flush()
        return True

    async def count(self, session: AsyncSession, **filters) -> int:
        query = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        result = await session.execute(query)
        return result.scalar()
