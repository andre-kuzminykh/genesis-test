"""
Requirement GET endpoints.

## Traceability
Feature: F007 — Requirement Management
Scenarios: SC014 (list, get by id)
"""
from typing import List, Optional
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.requirements import router
from schema.requirement.requirement_schema import RequirementResponseSchema
from service.requirement.requirement_service import RequirementService
from core.database import db_connect

_service = RequirementService()


@router.get("", response_model=List[RequirementResponseSchema])
async def list_requirements(
    feature_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(db_connect.get_session),
):
    """List requirements, optionally filtered by feature_id."""
    return await _service.get_all(session, feature_id=feature_id)


@router.get("/{id}", response_model=RequirementResponseSchema)
async def get_requirement(id: str, session: AsyncSession = Depends(db_connect.get_session)):
    """Get a requirement by id."""
    return await _service.get_by_id(session, id)
