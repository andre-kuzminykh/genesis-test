"""
Feature-Actor Link POST endpoints.

## Traceability
Feature: F003 — Actor Management
Scenarios: SC008 (create link)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.feature_actor_links import router
from schema.actor.actor_schema import (
    FeatureActorLinkCreateSchema,
    FeatureActorLinkResponseSchema,
)
from service.actor.actor_service import FeatureActorLinkService
from core.database import db_connect

_service = FeatureActorLinkService()


@router.post("", response_model=FeatureActorLinkResponseSchema, status_code=201)
async def create_feature_actor_link(
    payload: FeatureActorLinkCreateSchema,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Create a feature-actor link."""
    return await _service.create(session, **payload.model_dump())
