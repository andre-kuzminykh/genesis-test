"""
ActorModel — product-level domain entity.
FeatureActorLinkModel — links actors to features.

## Traceability
Feature: F003 — Actor Management
Scenarios: SC007, SC008
"""
from sqlalchemy import Column, String, Text, ForeignKey

from model.base_model import Base, BaseModel


class ActorModel(Base, BaseModel):
    __tablename__ = "actors"

    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    role_type = Column(String(50), nullable=True)


class FeatureActorLinkModel(Base, BaseModel):
    __tablename__ = "feature_actor_links"

    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    feature_id = Column(String, ForeignKey("features.id"), nullable=False, index=True)
    actor_id = Column(String, ForeignKey("actors.id"), nullable=False, index=True)
