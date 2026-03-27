"""
Story PUT endpoints.

## Traceability
Feature: F004 — User Story Management
Scenarios: SC009 (update)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.stories import router
from schema.story.story_schema import StoryUpdateSchema, StoryResponseSchema
from service.story.story_service import StoryService
from core.database import db_connect

_service = StoryService()


@router.put("/{id}", response_model=StoryResponseSchema)
async def update_story(
    id: str,
    payload: StoryUpdateSchema,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Update a story."""
    return await _service.update(session, id, **payload.model_dump(exclude_unset=True))
