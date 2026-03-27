"""
Story GET endpoints.

## Traceability
Feature: F004 — User Story Management
Scenarios: SC009 (list), SC010 (get by id)
"""
from typing import List, Optional
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.stories import router
from schema.story.story_schema import StoryResponseSchema
from service.story.story_service import StoryService
from core.database import db_connect

_service = StoryService()


@router.get("", response_model=List[StoryResponseSchema])
async def list_stories(
    feature_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(db_connect.get_session),
):
    """List stories, optionally filtered by feature_id."""
    return await _service.get_all(session, feature_id=feature_id)


@router.get("/{id}", response_model=StoryResponseSchema)
async def get_story(id: str, session: AsyncSession = Depends(db_connect.get_session)):
    """Get a story by id."""
    return await _service.get_by_id(session, id)
