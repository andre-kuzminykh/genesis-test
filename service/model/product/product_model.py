"""
ProductModel — root entity of the system.

## Traceability
Feature: F001 — Product Management
Scenarios: SC001, SC002, SC003
"""
from sqlalchemy import Column, String, Text

from model.base_model import Base, BaseModel


class ProductModel(Base, BaseModel):
    __tablename__ = "products"

    name = Column(String(200), nullable=False)
    short_description = Column(Text, nullable=True)
    goal = Column(Text, nullable=True)
    value_proposition = Column(Text, nullable=True)
    problem_statement = Column(Text, nullable=True)
    constraints = Column(Text, nullable=True)
    assumptions = Column(Text, nullable=True)
    target_users = Column(Text, nullable=True)
    business_contexts = Column(Text, nullable=True)
