"""
Use Case GET endpoints.

## Traceability
Feature: F006 — Use Case Management
Scenarios: SC013 (list, get by id)
"""
from typing import List, Optional
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.use_cases import router
from schema.use_case.use_case_schema import UseCaseResponseSchema
from service.use_case.use_case_service import UseCaseService
from core.database import db_connect

_service = UseCaseService()


@router.get("", response_model=List[UseCaseResponseSchema])
async def list_use_cases(
    flow_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(db_connect.get_session),
):
    """List use cases, optionally filtered by flow_id."""
    return await _service.get_all(session, flow_id=flow_id)


@router.get("/{id}", response_model=UseCaseResponseSchema)
async def get_use_case(id: str, session: AsyncSession = Depends(db_connect.get_session)):
    """Get a use case by id."""
    return await _service.get_by_id(session, id)
