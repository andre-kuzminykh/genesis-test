"""
StoryService — story management with actor-feature link validation.

## Traceability
Feature: F004 — User Story Management
Scenarios: SC009, SC010

## Dependencies
- StoryRepository
- FeatureActorLinkRepository (for actor-feature validation)
"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from repository.story.story_repository import StoryRepository
from repository.actor.actor_repository import FeatureActorLinkRepository
from core.exceptions import NotFoundError, ValidationError


class StoryService:
    def __init__(self):
        self._repo = StoryRepository()
        self._fal_repo = FeatureActorLinkRepository()

    async def create(self, session: AsyncSession, **kwargs):
        # Section 12.4: Story Actor must be linked to Story's Feature
        actor_id = kwargs.get("actor_id")
        feature_id = kwargs.get("feature_id")
        if actor_id and feature_id:
            linked = await self._fal_repo.link_exists(session, feature_id, actor_id)
            if not linked:
                raise ValidationError(
                    "Story's Actor must be linked to the Story's Feature via FeatureActorLink."
                )
        return await self._repo.create(session, **kwargs)

    async def get_by_id(self, session: AsyncSession, story_id: str):
        story = await self._repo.get_by_id(session, story_id)
        if not story:
            raise NotFoundError("Story", story_id)
        return story

    async def get_all(self, session: AsyncSession, feature_id: str | None = None):
        if feature_id:
            return await self._repo.get_all(session, feature_id=feature_id)
        return await self._repo.get_all(session)

    async def update(self, session: AsyncSession, story_id: str, **kwargs):
        story = await self.get_by_id(session, story_id)
        content_changed = any(
            getattr(story, k, None) != v
            for k, v in kwargs.items()
            if v is not None and hasattr(story, k)
        )
        if content_changed:
            kwargs["version"] = story.version + 1
            kwargs["updated_at"] = datetime.utcnow()
            if story.approved_version is not None:
                kwargs["status"] = "changed"
                kwargs["approved_at"] = None
                kwargs["approved_by"] = None
                kwargs["approved_version"] = None
        return await self._repo.update(session, story_id, **kwargs)

    async def approve(self, session: AsyncSession, story_id: str, approver: str = "system"):
        story = await self.get_by_id(session, story_id)
        if not story.actor_id:
            raise ValidationError("Story cannot be approved without an Actor.")
        story.status = "approved"
        story.approved_at = datetime.utcnow()
        story.approved_by = approver
        story.approved_version = story.version
        await session.flush()
        await session.refresh(story)
        return story
