"""
Feature GET endpoints.

## Traceability
Feature: F002 — Feature Management
Scenarios: SC004 (list by product), SC005 (get by id)
"""
from typing import List, Optional
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.features import router
from schema.feature.feature_schema import FeatureResponseSchema
from service.feature.feature_service import FeatureService
from core.database import db_connect

_service = FeatureService()


@router.get("", response_model=List[FeatureResponseSchema])
async def list_features(
    product_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(db_connect.get_session),
):
    """List features, optionally filtered by product_id."""
    return await _service.get_all(session, product_id=product_id)


@router.get("/{id}", response_model=FeatureResponseSchema)
async def get_feature(id: str, session: AsyncSession = Depends(db_connect.get_session)):
    """Get a feature by id."""
    return await _service.get_by_id(session, id)
