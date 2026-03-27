"""
UseCaseModel — use case entity.

## Traceability
Feature: F006 — Use Case Management
Scenarios: SC013
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey

from model.base_model import Base, BaseModel


class UseCaseModel(Base, BaseModel):
    __tablename__ = "use_cases"

    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    feature_id = Column(String, ForeignKey("features.id"), nullable=False, index=True)
    actor_id = Column(String, ForeignKey("actors.id"), nullable=True)
    story_id = Column(String, ForeignKey("stories.id"), nullable=False)
    flow_id = Column(String, ForeignKey("flows.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    goal = Column(Text, nullable=True)
    preconditions = Column(Text, nullable=True)
    given_text = Column(Text, nullable=True)
    when_text = Column(Text, nullable=True)
    then_text = Column(Text, nullable=True)
    main_success_scenario = Column(Text, nullable=True)
    alternative_scenarios = Column(Text, nullable=True)
    edge_cases = Column(Text, nullable=True)
    exception_cases = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
