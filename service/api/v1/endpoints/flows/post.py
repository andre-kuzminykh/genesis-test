"""
Flow POST endpoints.

## Traceability
Feature: F005 — User Flow Management
Scenarios: SC011 (create), SC012 (approve)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.flows import router
from schema.flow.flow_schema import FlowCreateSchema, FlowResponseSchema
from service.flow.flow_service import FlowService
from core.database import db_connect

_service = FlowService()


@router.post("", response_model=FlowResponseSchema, status_code=201)
async def create_flow(
    payload: FlowCreateSchema,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Create a new flow."""
    return await _service.create(session, **payload.model_dump())


@router.post("/{id}/approve", response_model=FlowResponseSchema)
async def approve_flow(
    id: str,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Approve a flow at its current version."""
    return await _service.approve(session, id)
