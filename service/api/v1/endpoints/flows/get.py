"""
Flow GET endpoints.

## Traceability
Feature: F005 — User Flow Management
Scenarios: SC011 (list), SC012 (get by id)
"""
from typing import List, Optional
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.flows import router
from schema.flow.flow_schema import FlowResponseSchema
from service.flow.flow_service import FlowService
from core.database import db_connect

_service = FlowService()


@router.get("", response_model=List[FlowResponseSchema])
async def list_flows(
    story_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(db_connect.get_session),
):
    """List flows, optionally filtered by story_id."""
    return await _service.get_all(session, story_id=story_id)


@router.get("/{id}", response_model=FlowResponseSchema)
async def get_flow(id: str, session: AsyncSession = Depends(db_connect.get_session)):
    """Get a flow by id."""
    return await _service.get_by_id(session, id)
