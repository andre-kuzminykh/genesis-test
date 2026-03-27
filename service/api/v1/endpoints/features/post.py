"""
Feature POST endpoints.

## Traceability
Feature: F002 — Feature Management
Scenarios: SC004 (create), SC006 (approve)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.features import router
from schema.feature.feature_schema import FeatureCreateSchema, FeatureResponseSchema
from service.feature.feature_service import FeatureService
from core.database import db_connect

_service = FeatureService()


@router.post("", response_model=FeatureResponseSchema, status_code=201)
async def create_feature(
    payload: FeatureCreateSchema,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Create a new feature."""
    return await _service.create(session, **payload.model_dump())


@router.post("/{id}/approve", response_model=FeatureResponseSchema)
async def approve_feature(
    id: str,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Approve a feature at its current version."""
    return await _service.approve(session, id)
