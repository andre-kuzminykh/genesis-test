"""
Feature schemas.

## Traceability
Feature: F002 — Feature Management
Scenarios: SC004, SC005, SC006
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class FeatureCreateSchema(BaseModel):
    product_id: str
    code: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    goal: Optional[str] = None
    priority: Optional[str] = None
    sort_order: int = 0


class FeatureUpdateSchema(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    goal: Optional[str] = None
    priority: Optional[str] = None
    sort_order: Optional[int] = None


class FeatureResponseSchema(BaseModel):
    id: str
    product_id: str
    code: Optional[str] = None
    name: str
    description: Optional[str] = None
    goal: Optional[str] = None
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
