"""
Actor GET endpoints.

## Traceability
Feature: F003 — Actor Management
Scenarios: SC007 (list), SC008 (get by id)
"""
from typing import List, Optional
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.actors import router
from schema.actor.actor_schema import ActorResponseSchema
from service.actor.actor_service import ActorService
from core.database import db_connect

_service = ActorService()


@router.get("", response_model=List[ActorResponseSchema])
async def list_actors(
    product_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(db_connect.get_session),
):
    """List actors, optionally filtered by product_id."""
    return await _service.get_all(session, product_id=product_id)


@router.get("/{id}", response_model=ActorResponseSchema)
async def get_actor(id: str, session: AsyncSession = Depends(db_connect.get_session)):
    """Get an actor by id."""
    return await _service.get_by_id(session, id)
