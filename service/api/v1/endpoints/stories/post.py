"""
Story POST endpoints.

## Traceability
Feature: F004 — User Story Management
Scenarios: SC009 (create), SC010 (approve)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.stories import router
from schema.story.story_schema import StoryCreateSchema, StoryResponseSchema
from service.story.story_service import StoryService
from core.database import db_connect

_service = StoryService()


@router.post("", response_model=StoryResponseSchema, status_code=201)
async def create_story(
    payload: StoryCreateSchema,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Create a new story."""
    return await _service.create(session, **payload.model_dump())


@router.post("/{id}/approve", response_model=StoryResponseSchema)
async def approve_story(
    id: str,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Approve a story at its current version."""
    return await _service.approve(session, id)
