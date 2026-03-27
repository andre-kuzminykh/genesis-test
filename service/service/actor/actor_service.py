"""
ActorService, FeatureActorLinkService.

## Traceability
Feature: F003 — Actor Management
Scenarios: SC007, SC008

## Dependencies
- ActorRepository, FeatureActorLinkRepository
"""
from sqlalchemy.ext.asyncio import AsyncSession

from repository.actor.actor_repository import ActorRepository, FeatureActorLinkRepository
from repository.product.product_repository import ProductRepository
from core.exceptions import NotFoundError, ConflictError


class ActorService:
    def __init__(self):
        self._repo = ActorRepository()
        self._product_repo = ProductRepository()

    async def create(self, session: AsyncSession, **kwargs):
        product = await self._product_repo.get_by_id(session, kwargs.get("product_id", ""))
        if not product:
            raise NotFoundError("Product", kwargs.get("product_id", ""))
        return await self._repo.create(session, **kwargs)

    async def get_by_id(self, session: AsyncSession, actor_id: str):
        actor = await self._repo.get_by_id(session, actor_id)
        if not actor:
            raise NotFoundError("Actor", actor_id)
        return actor

    async def get_all(self, session: AsyncSession, product_id: str | None = None):
        if product_id:
            return await self._repo.get_all(session, product_id=product_id)
        return await self._repo.get_all(session)


class FeatureActorLinkService:
    def __init__(self):
        self._repo = FeatureActorLinkRepository()

    async def create(self, session: AsyncSession, **kwargs):
        exists = await self._repo.link_exists(
            session, kwargs["feature_id"], kwargs["actor_id"]
        )
        if exists:
            raise ConflictError("FeatureActorLink already exists.")
        return await self._repo.create(session, **kwargs)

    async def get_all(self, session: AsyncSession, feature_id: str | None = None):
        if feature_id:
            return await self._repo.get_all(session, feature_id=feature_id)
        return await self._repo.get_all(session)

    async def link_exists(self, session: AsyncSession, feature_id: str, actor_id: str) -> bool:
        return await self._repo.link_exists(session, feature_id, actor_id)
