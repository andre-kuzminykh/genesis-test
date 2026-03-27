"""
Actor and FeatureActorLink schemas.

## Traceability
Feature: F003 — Actor Management
Scenarios: SC007, SC008
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ActorCreateSchema(BaseModel):
    product_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    role_type: Optional[str] = None


class ActorResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    name: str
    description: Optional[str] = None
    role_type: Optional[str] = None
    version: int
    status: str
    created_at: datetime
    updated_at: datetime


class FeatureActorLinkCreateSchema(BaseModel):
    product_id: str
    feature_id: str
    actor_id: str


class FeatureActorLinkResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    feature_id: str
    actor_id: str
    version: int
    status: str
    created_at: datetime
