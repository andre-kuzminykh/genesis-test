"""Tests for business truth entities — sections 10-16."""
import pytest
from datetime import datetime

from src.enums.statuses import BaseStatus
from src.enums.types import FlowType, RequirementType
from src.models.business import (
    Product, Feature, Actor, FeatureActorLink, UserStory, UserFlow, UseCase, Requirement,
)


class TestProduct:
    """Section 10 — Product entity tests."""

    def test_product_creation_with_required_fields(self, product):
        assert product.product_id == "prod-1"
        assert product.name == "Test Product"
        assert product.version == 1
        assert product.status == BaseStatus.DRAFT

    def test_product_has_base_metadata(self, product):
        """Section 6 — base entity metadata."""
        assert product.created_at is not None
        assert product.updated_at is not None
        assert product.created_by == "system"
        assert product.updated_by == "system"

    def test_product_default_status_is_draft(self, product):
        assert product.status == BaseStatus.DRAFT

    def test_product_supports_approval_fields(self, approved_product):
        """Section 6 — approval metadata."""
        assert approved_product.approved_at is not None
        assert approved_product.approved_by == "tester"
        assert approved_product.approved_version == approved_product.version

    def test_product_all_fields(self):
        p = Product(
            product_id="p-full",
            name="Full Product",
            short_description="Desc",
            goal="Goal",
            value_proposition="VP",
            problem_statement="PS",
            constraints="C",
            assumptions="A",
            target_users="TU",
            business_contexts="BC",
            created_by="user",
            updated_by="user",
        )
        assert p.value_proposition == "VP"
        assert p.problem_statement == "PS"
        assert p.constraints == "C"
        assert p.assumptions == "A"
        assert p.target_users == "TU"
        assert p.business_contexts == "BC"


class TestFeature:
    """Section 11 — Feature entity tests."""

    def test_feature_belongs_to_product(self, feature, product):
        assert feature.product_id == product.product_id

    def test_feature_has_code_and_sort_order(self):
        f = Feature(
            feature_id="f-1",
            product_id="p-1",
            code="AUTH",
            name="Auth",
            sort_order=5,
            created_by="u",
            updated_by="u",
        )
        assert f.code == "AUTH"
        assert f.sort_order == 5

    def test_feature_default_status_is_draft(self, feature):
        assert feature.status == BaseStatus.DRAFT

    def test_feature_versioned(self, feature):
        assert feature.version >= 1


class TestActor:
    """Section 12 — Actor entity tests."""

    def test_actor_belongs_to_product(self, actor, product):
        """Actor belongs to exactly one Product (section 12.4)."""
        assert actor.product_id == product.product_id

    def test_actor_has_role_type(self, actor):
        assert actor.role_type == "primary"

    def test_feature_actor_link_fields(self, feature_actor_link):
        """Section 12.3 — FeatureActorLink."""
        assert feature_actor_link.product_id == "prod-1"
        assert feature_actor_link.feature_id == "feat-1"
        assert feature_actor_link.actor_id == "actor-1"


class TestUserStory:
    """Section 13 — User Story entity tests."""

    def test_story_belongs_to_feature(self, story, feature):
        assert story.feature_id == feature.feature_id

    def test_story_references_actor(self, story, actor):
        assert story.actor_id == actor.actor_id

    def test_story_canonical_format(self, story):
        """As [actor], I want [capability], so that [benefit]."""
        assert story.want_text is not None
        assert story.benefit_text is not None

    def test_story_full_text_format(self, story):
        assert "As" in story.full_text
        assert "I want" in story.full_text
        assert "so that" in story.full_text

    def test_story_without_actor(self, product, feature):
        s = UserStory(
            story_id="s-no-actor",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            title="No actor story",
            created_by="u",
            updated_by="u",
        )
        assert s.actor_id is None


class TestUserFlow:
    """Section 14 — User Flow entity tests."""

    def test_flow_belongs_to_story(self, flow, story):
        assert flow.story_id == story.story_id

    def test_flow_has_mermaid_source(self, flow):
        """All User Flows must be stored in Mermaid (section 14)."""
        assert flow.mermaid_source is not None
        assert "graph" in flow.mermaid_source

    def test_flow_type_is_primary(self, flow):
        assert flow.flow_type == FlowType.PRIMARY

    def test_alternative_flow(self, product, feature, story):
        alt = UserFlow(
            flow_id="flow-alt",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            story_id=story.story_id,
            title="Alternative flow",
            flow_type=FlowType.ALTERNATIVE,
            mermaid_source="graph TD\n  A --> B",
            created_by="u",
            updated_by="u",
        )
        assert alt.flow_type == FlowType.ALTERNATIVE

    def test_exception_flow(self, product, feature, story):
        exc = UserFlow(
            flow_id="flow-exc",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            story_id=story.story_id,
            title="Exception flow",
            flow_type=FlowType.EXCEPTION,
            mermaid_source="graph TD\n  A --> Error",
            created_by="u",
            updated_by="u",
        )
        assert exc.flow_type == FlowType.EXCEPTION


class TestUseCase:
    """Section 15 — Use Case entity tests."""

    def test_use_case_belongs_to_flow(self, use_case, flow):
        assert use_case.flow_id == flow.flow_id

    def test_use_case_mandatory_structure(self, use_case):
        """Section 15.1 — mandatory Use Case structure."""
        assert use_case.title is not None
        assert use_case.goal is not None
        assert use_case.preconditions is not None
        assert use_case.given_text is not None
        assert use_case.when_text is not None
        assert use_case.then_text is not None
        assert use_case.main_success_scenario is not None

    def test_use_case_traceable_to_story(self, use_case, story):
        """Use Case is traceable to exactly one Story through its parent Flow (section 15.2)."""
        assert use_case.story_id == story.story_id


class TestRequirement:
    """Section 16 — Requirement entity tests."""

    def test_requirement_has_type(self, requirement):
        """requirement_type must explicitly classify the requirement (section 16.5)."""
        assert requirement.requirement_type == RequirementType.FUNCTIONAL

    def test_requirement_traceable_to_product_and_feature(self, requirement, product, feature):
        """Requirement must be traceable to Product and Feature (section 16.5)."""
        assert requirement.product_id == product.product_id
        assert requirement.feature_id == feature.feature_id

    def test_requirement_has_upstream_source(self, requirement):
        assert requirement.primary_use_case_id is not None

    def test_non_functional_requirement(self, product, feature):
        nfr = Requirement(
            requirement_id="req-nfr",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            title="Response time < 200ms",
            requirement_type=RequirementType.NON_FUNCTIONAL,
            source_id="product-constraint-1",
            created_by="u",
            updated_by="u",
        )
        assert nfr.requirement_type == RequirementType.NON_FUNCTIONAL

    def test_requirement_supports_tags(self, requirement):
        requirement.tags = ["security", "auth"]
        assert "security" in requirement.tags

    @pytest.mark.parametrize("req_type", [
        RequirementType.FUNCTIONAL,
        RequirementType.NON_FUNCTIONAL,
        RequirementType.DATA,
        RequirementType.INTEGRATION,
        RequirementType.AI,
        RequirementType.OBSERVABILITY,
        RequirementType.SECURITY,
        RequirementType.COMPLIANCE,
    ])
    def test_all_requirement_types_supported(self, product, feature, req_type):
        """Sections 16.2-16.3 — all requirement categories."""
        r = Requirement(
            requirement_id=f"req-{req_type.value}",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            title=f"Test {req_type.value}",
            requirement_type=req_type,
            source_id="uc-1",
            created_by="u",
            updated_by="u",
        )
        assert r.requirement_type == req_type
