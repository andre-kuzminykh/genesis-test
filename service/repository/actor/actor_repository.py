"""
ActorRepository, FeatureActorLinkRepository.

## Traceability
Feature: F003 — Actor Management
Scenarios: SC007, SC008
"""
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from model.actor.actor_model import ActorModel, FeatureActorLinkModel
from repository.base_repository import BaseRepository


class ActorRepository(BaseRepository[ActorModel]):
    def __init__(self):
        super().__init__(ActorModel)


class FeatureActorLinkRepository(BaseRepository[FeatureActorLinkModel]):
    def __init__(self):
        super().__init__(FeatureActorLinkModel)

    async def link_exists(
        self, session: AsyncSession, feature_id: str, actor_id: str
    ) -> bool:
        result = await session.execute(
            select(self.model).where(
                and_(
                    self.model.feature_id == feature_id,
                    self.model.actor_id == actor_id,
                )
            )
        )
        return result.scalar_one_or_none() is not None
