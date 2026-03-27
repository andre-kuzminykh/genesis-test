"""
StoryModel — user story entity.

## Traceability
Feature: F004 — User Story Management
Scenarios: SC009, SC010
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey

from model.base_model import Base, BaseModel


class StoryModel(Base, BaseModel):
    __tablename__ = "stories"

    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    feature_id = Column(String, ForeignKey("features.id"), nullable=False, index=True)
    actor_id = Column(String, ForeignKey("actors.id"), nullable=True)
    title = Column(String(500), nullable=False)
    want_text = Column(Text, nullable=True)
    benefit_text = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    priority = Column(String(50), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
