"""
Use Case POST endpoints.

## Traceability
Feature: F006 — Use Case Management
Scenarios: SC013 (create, approve)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.use_cases import router
from schema.use_case.use_case_schema import UseCaseCreateSchema, UseCaseResponseSchema
from service.use_case.use_case_service import UseCaseService
from core.database import db_connect

_service = UseCaseService()


@router.post("", response_model=UseCaseResponseSchema, status_code=201)
async def create_use_case(
    payload: UseCaseCreateSchema,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Create a new use case."""
    return await _service.create(session, **payload.model_dump())


@router.post("/{id}/approve", response_model=UseCaseResponseSchema)
async def approve_use_case(
    id: str,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Approve a use case at its current version."""
    return await _service.approve(session, id)
