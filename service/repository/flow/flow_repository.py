"""
FlowRepository.

## Traceability
Feature: F005 — User Flow Management
Scenarios: SC011, SC012
"""
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from model.flow.flow_model import FlowModel
from repository.base_repository import BaseRepository


class FlowRepository(BaseRepository[FlowModel]):
    def __init__(self):
        super().__init__(FlowModel)

    async def has_primary_flow(self, session: AsyncSession, story_id: str) -> bool:
        result = await session.execute(
            select(self.model).where(
                and_(
                    self.model.story_id == story_id,
                    self.model.flow_type == "primary",
                )
            )
        )
        return result.scalar_one_or_none() is not None
