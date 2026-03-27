"""
UseCase schemas.

## Traceability
Feature: F006 — Use Case Management
Scenarios: SC013
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UseCaseCreateSchema(BaseModel):
    product_id: str
    feature_id: str
    story_id: str
    flow_id: str
    actor_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    goal: Optional[str] = None
    preconditions: Optional[str] = None
    given_text: Optional[str] = None
    when_text: Optional[str] = None
    then_text: Optional[str] = None
    main_success_scenario: Optional[str] = None
    alternative_scenarios: Optional[str] = None
    edge_cases: Optional[str] = None
    exception_cases: Optional[str] = None


class UseCaseResponseSchema(BaseModel):
    id: str
    product_id: str
    feature_id: str
    story_id: str
    flow_id: str
    actor_id: Optional[str] = None
    title: str
    goal: Optional[str] = None
    preconditions: Optional[str] = None
    given_text: Optional[str] = None
    when_text: Optional[str] = None
    then_text: Optional[str] = None
    main_success_scenario: Optional[str] = None
    version: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
