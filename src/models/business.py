"""Business truth entities per specification sections 8.1, 10-16."""
from datetime import datetime
from typing import Optional
from pydantic import Field

from src.models.base import ApprovableEntity
from src.enums.statuses import BaseStatus
from src.enums.types import FlowType, RequirementType


class Product(ApprovableEntity):
    """Section 10 — Product entity."""
    product_id: str
    name: str
    short_description: Optional[str] = None
    goal: Optional[str] = None
    value_proposition: Optional[str] = None
    problem_statement: Optional[str] = None
    constraints: Optional[str] = None
    assumptions: Optional[str] = None
    target_users: Optional[str] = None
    business_contexts: Optional[str] = None


class Feature(ApprovableEntity):
    """Section 11 — Feature entity."""
    feature_id: str
    product_id: str
    code: Optional[str] = None
    name: str
    description: Optional[str] = None
    goal: Optional[str] = None
    priority: Optional[str] = None
    sort_order: int = 0


class Actor(ApprovableEntity):
    """Section 12.2 — Actor entity."""
    actor_id: str
    product_id: str
    name: str
    description: Optional[str] = None
    role_type: Optional[str] = None


class FeatureActorLink(ApprovableEntity):
    """Section 12.3 — Feature-Actor link."""
    feature_actor_link_id: str
    product_id: str
    feature_id: str
    actor_id: str


class UserStory(ApprovableEntity):
    """Section 13 — User Story entity."""
    story_id: str
    product_id: str
    feature_id: str
    actor_id: Optional[str] = None
    title: str
    want_text: Optional[str] = None
    benefit_text: Optional[str] = None
    full_text: Optional[str] = None
    priority: Optional[str] = None
    sort_order: int = 0


class UserFlow(ApprovableEntity):
    """Section 14 — User Flow entity (Mermaid-based)."""
    flow_id: str
    product_id: str
    feature_id: str
    story_id: str
    title: str
    description: Optional[str] = None
    flow_type: FlowType = FlowType.PRIMARY
    mermaid_source: Optional[str] = None


class UseCase(ApprovableEntity):
    """Section 15 — Use Case entity."""
    use_case_id: str
    product_id: str
    feature_id: str
    actor_id: Optional[str] = None
    story_id: str
    flow_id: str
    title: str
    goal: Optional[str] = None
    preconditions: Optional[str] = None
    given_text: Optional[str] = None
    when_text: Optional[str] = None
    then_text: Optional[str] = None
    main_success_scenario: Optional[str] = None
    alternative_scenarios: Optional[str] = None
    edge_cases: Optional[str] = None
    exception_cases: Optional[str] = None
    sort_order: int = 0


class Requirement(ApprovableEntity):
    """Section 16 — Requirement entity."""
    requirement_id: str
    product_id: str
    feature_id: str
    primary_actor_id: Optional[str] = None
    primary_story_id: Optional[str] = None
    primary_flow_id: Optional[str] = None
    primary_use_case_id: Optional[str] = None
    code: Optional[str] = None
    title: str
    text: Optional[str] = None
    requirement_type: RequirementType
    priority: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
