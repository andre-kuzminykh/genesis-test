"""
Flow PUT endpoints.

## Traceability
Feature: F005 — User Flow Management
Scenarios: SC011 (update)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.flows import router
from schema.flow.flow_schema import FlowUpdateSchema, FlowResponseSchema
from service.flow.flow_service import FlowService
from core.database import db_connect

_service = FlowService()


@router.put("/{id}", response_model=FlowResponseSchema)
async def update_flow(
    id: str,
    payload: FlowUpdateSchema,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Update a flow."""
    return await _service.update(session, id, **payload.model_dump(exclude_unset=True))
