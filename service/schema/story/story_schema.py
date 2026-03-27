"""
Story schemas.

## Traceability
Feature: F004 — User Story Management
Scenarios: SC009, SC010
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StoryCreateSchema(BaseModel):
    product_id: str
    feature_id: str
    actor_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    want_text: Optional[str] = None
    benefit_text: Optional[str] = None
    full_text: Optional[str] = None
    priority: Optional[str] = None
    sort_order: int = 0


class StoryUpdateSchema(BaseModel):
    actor_id: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    want_text: Optional[str] = None
    benefit_text: Optional[str] = None
    full_text: Optional[str] = None
    priority: Optional[str] = None
    sort_order: Optional[int] = None


class StoryResponseSchema(BaseModel):
    id: str
    product_id: str
    feature_id: str
    actor_id: Optional[str] = None
    title: str
    want_text: Optional[str] = None
    benefit_text: Optional[str] = None
    full_text: Optional[str] = None
    priority: Optional[str] = None
    sort_order: int
    version: int
    status: str
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_version: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
