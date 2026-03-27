"""
FeatureModel — primary decomposition unit for product scope.

## Traceability
Feature: F002 — Feature Management
Scenarios: SC004, SC005, SC006
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey

from model.base_model import Base, BaseModel


class FeatureModel(Base, BaseModel):
    __tablename__ = "features"

    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    code = Column(String(50), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    goal = Column(Text, nullable=True)
    priority = Column(String(50), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
