"""
Feature PUT endpoints.

## Traceability
Feature: F002 — Feature Management
Scenarios: SC005 (update)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.features import router
from schema.feature.feature_schema import FeatureUpdateSchema, FeatureResponseSchema
from service.feature.feature_service import FeatureService
from core.database import db_connect

_service = FeatureService()


@router.put("/{id}", response_model=FeatureResponseSchema)
async def update_feature(
    id: str,
    payload: FeatureUpdateSchema,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Update a feature."""
    return await _service.update(session, id, **payload.model_dump(exclude_unset=True))
