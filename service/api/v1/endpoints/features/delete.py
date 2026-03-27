"""
Feature DELETE endpoints.

## Traceability
Feature: F002 — Feature Management
Scenarios: SC006 (delete)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.features import router
from service.feature.feature_service import FeatureService
from core.database import db_connect

_service = FeatureService()


@router.delete("/{id}", status_code=204)
async def delete_feature(
    id: str,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Delete a draft feature with no downstream references."""
    await _service.delete(session, id)
