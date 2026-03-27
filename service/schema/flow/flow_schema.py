"""
Flow schemas.

## Traceability
Feature: F005 — User Flow Management
Scenarios: SC011, SC012
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class FlowCreateSchema(BaseModel):
    product_id: str
    feature_id: str
    story_id: str
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    flow_type: str = "primary"
    mermaid_source: Optional[str] = None


class FlowUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    mermaid_source: Optional[str] = None


class FlowResponseSchema(BaseModel):
    id: str
    product_id: str
    feature_id: str
    story_id: str
    title: str
    description: Optional[str] = None
    flow_type: str
    mermaid_source: Optional[str] = None
    version: int
    status: str
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_version: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
