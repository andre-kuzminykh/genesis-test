"""
Actor POST endpoints.

## Traceability
Feature: F003 — Actor Management
Scenarios: SC007 (create)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.actors import router
from schema.actor.actor_schema import ActorCreateSchema, ActorResponseSchema
from service.actor.actor_service import ActorService
from core.database import db_connect

_service = ActorService()


@router.post("", response_model=ActorResponseSchema, status_code=201)
async def create_actor(
    payload: ActorCreateSchema,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Create a new actor."""
    return await _service.create(session, **payload.model_dump())
