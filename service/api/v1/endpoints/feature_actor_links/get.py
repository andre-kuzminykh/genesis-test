"""
Feature-Actor Link GET endpoints.

## Traceability
Feature: F003 — Actor Management
Scenarios: SC008 (list)
"""
from typing import List, Optional
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.feature_actor_links import router
from schema.actor.actor_schema import FeatureActorLinkResponseSchema
from service.actor.actor_service import FeatureActorLinkService
from core.database import db_connect

_service = FeatureActorLinkService()


@router.get("", response_model=List[FeatureActorLinkResponseSchema])
async def list_feature_actor_links(
    feature_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(db_connect.get_session),
):
    """List feature-actor links, optionally filtered by feature_id."""
    return await _service.get_all(session, feature_id=feature_id)
