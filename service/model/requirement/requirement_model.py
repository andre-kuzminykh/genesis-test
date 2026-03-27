"""
RequirementModel — requirement entity.

## Traceability
Feature: F007 — Requirement Management
Scenarios: SC014
"""
from sqlalchemy import Column, String, Text, ForeignKey

from model.base_model import Base, BaseModel


class RequirementModel(Base, BaseModel):
    __tablename__ = "requirements"

    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    feature_id = Column(String, ForeignKey("features.id"), nullable=False, index=True)
    primary_actor_id = Column(String, ForeignKey("actors.id"), nullable=True)
    primary_story_id = Column(String, ForeignKey("stories.id"), nullable=True)
    primary_flow_id = Column(String, ForeignKey("flows.id"), nullable=True)
    primary_use_case_id = Column(String, ForeignKey("use_cases.id"), nullable=True)
    code = Column(String(50), nullable=True)
    title = Column(String(500), nullable=False)
    text = Column(Text, nullable=True)
    requirement_type = Column(String(32), nullable=False)
    priority = Column(String(50), nullable=True)
    source_type = Column(String(100), nullable=True)
    source_id = Column(String, nullable=True)
