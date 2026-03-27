"""
Requirement schemas.

## Traceability
Feature: F007 — Requirement Management
Scenarios: SC014
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RequirementCreateSchema(BaseModel):
    product_id: str
    feature_id: str
    primary_actor_id: Optional[str] = None
    primary_story_id: Optional[str] = None
    primary_flow_id: Optional[str] = None
    primary_use_case_id: Optional[str] = None
    code: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    text: Optional[str] = None
    requirement_type: str
    priority: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None


class RequirementResponseSchema(BaseModel):
    id: str
    product_id: str
    feature_id: str
    primary_use_case_id: Optional[str] = None
    code: Optional[str] = None
    title: str
    text: Optional[str] = None
    requirement_type: str
    priority: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    version: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
