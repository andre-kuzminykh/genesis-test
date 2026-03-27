"""
FlowModel — user flow stored in Mermaid.

## Traceability
Feature: F005 — User Flow Management
Scenarios: SC011, SC012
"""
from sqlalchemy import Column, String, Text, ForeignKey

from model.base_model import Base, BaseModel


class FlowModel(Base, BaseModel):
    __tablename__ = "flows"

    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    feature_id = Column(String, ForeignKey("features.id"), nullable=False, index=True)
    story_id = Column(String, ForeignKey("stories.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    flow_type = Column(String(32), nullable=False, default="primary")
    mermaid_source = Column(Text, nullable=True)
