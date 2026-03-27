"""
Requirement POST endpoints.

## Traceability
Feature: F007 — Requirement Management
Scenarios: SC014 (create, approve)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.requirements import router
from schema.requirement.requirement_schema import (
    RequirementCreateSchema,
    RequirementResponseSchema,
)
from service.requirement.requirement_service import RequirementService
from core.database import db_connect

_service = RequirementService()


@router.post("", response_model=RequirementResponseSchema, status_code=201)
async def create_requirement(
    payload: RequirementCreateSchema,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Create a new requirement."""
    return await _service.create(session, **payload.model_dump())


@router.post("/{id}/approve", response_model=RequirementResponseSchema)
async def approve_requirement(
    id: str,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Approve a requirement at its current version."""
    return await _service.approve(session, id)
