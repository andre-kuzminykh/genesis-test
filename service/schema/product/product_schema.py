"""
Product schemas.

## Traceability
Feature: F001 — Product Management
Scenarios: SC001, SC002, SC003
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    short_description: Optional[str] = None
    goal: Optional[str] = None
    value_proposition: Optional[str] = None
    problem_statement: Optional[str] = None
    constraints: Optional[str] = None
    assumptions: Optional[str] = None
    target_users: Optional[str] = None
    business_contexts: Optional[str] = None


class ProductUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    short_description: Optional[str] = None
    goal: Optional[str] = None
    value_proposition: Optional[str] = None
    problem_statement: Optional[str] = None
    constraints: Optional[str] = None
    assumptions: Optional[str] = None
    target_users: Optional[str] = None
    business_contexts: Optional[str] = None


class ProductResponseSchema(BaseModel):
    id: str
    name: str
    short_description: Optional[str] = None
    goal: Optional[str] = None
    value_proposition: Optional[str] = None
    problem_statement: Optional[str] = None
    constraints: Optional[str] = None
    assumptions: Optional[str] = None
    target_users: Optional[str] = None
    business_contexts: Optional[str] = None
    version: int
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_version: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
