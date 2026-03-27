"""Domain invariant tests — enforcing rules from sections 4, 10-22."""
import pytest
from src.enums.statuses import BaseStatus
from src.enums.types import FlowType, RequirementType
from src.models.business import (
    Product, Feature, Actor, FeatureActorLink, UserStory, UserFlow, UseCase, Requirement,
)
from src.models.engineering import (
    Task, TestDesign, TestCase, DependencyOutput, CodeArtifact, ArtifactRegistryEntry,
)
from src.models.execution import ContextPackage
from src.services.validation import DomainValidator, ValidationError


class TestProductInvariants:
    """Section 10 — Product must exist before any child entity."""

    @pytest.mark.invariant
    def test_product_must_exist_before_children(self):
        with pytest.raises(ValidationError, match="Product must exist"):
            DomainValidator.validate_product_exists_before_children(None)

    @pytest.mark.invariant
    def test_product_exists_allows_children(self, product):
        DomainValidator.validate_product_exists_before_children(product)


class TestFeatureInvariants:
    """Section 11 — Feature invariants."""

    @pytest.mark.invariant
    def test_feature_belongs_to_product(self, feature, product):
        DomainValidator.validate_feature_belongs_to_product(feature, product)

    @pytest.mark.invariant
    def test_feature_wrong_product_rejected(self, product):
        f = Feature(
            feature_id="f-wrong",
            product_id="other-product",
            name="Wrong",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="must belong"):
            DomainValidator.validate_feature_belongs_to_product(f, product)

    @pytest.mark.invariant
    def test_draft_unreferenced_feature_can_be_deleted(self, feature):
        DomainValidator.validate_feature_deletion(feature, has_downstream_refs=False)

    @pytest.mark.invariant
    def test_referenced_feature_cannot_be_deleted(self, feature):
        with pytest.raises(ValidationError, match="downstream references"):
            DomainValidator.validate_feature_deletion(feature, has_downstream_refs=True)

    @pytest.mark.invariant
    def test_approved_feature_cannot_be_physically_deleted(self, approved_feature):
        with pytest.raises(ValidationError):
            DomainValidator.validate_feature_deletion(approved_feature, has_downstream_refs=False)


class TestActorInvariants:
    """Section 12 — Actor invariants."""

    @pytest.mark.invariant
    def test_actor_belongs_to_product(self, actor, product):
        DomainValidator.validate_actor_belongs_to_product(actor, product)

    @pytest.mark.invariant
    def test_story_actor_must_be_linked_to_feature(self, story, feature_actor_link):
        """Section 12.4 — Story Actor must be linked to Story's Feature."""
        DomainValidator.validate_story_actor_linked_to_feature(
            story, [feature_actor_link]
        )

    @pytest.mark.invariant
    def test_story_actor_not_linked_to_feature_rejected(self, story):
        """Reject if Actor is not linked to Feature."""
        with pytest.raises(ValidationError, match="must be linked"):
            DomainValidator.validate_story_actor_linked_to_feature(story, [])

    @pytest.mark.invariant
    def test_story_without_actor_rejected(self, product, feature):
        s = UserStory(
            story_id="s-no-actor",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            title="No actor",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="exactly one Actor"):
            DomainValidator.validate_story_actor_linked_to_feature(s, [])


class TestStoryInvariants:
    """Section 13 — Story invariants."""

    @pytest.mark.invariant
    def test_story_has_actor(self, story):
        DomainValidator.validate_story_has_actor(story)

    @pytest.mark.invariant
    def test_story_without_actor_fails(self, product, feature):
        s = UserStory(
            story_id="s-no-actor",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            title="Missing actor",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="exactly one Actor"):
            DomainValidator.validate_story_has_actor(s)

    @pytest.mark.invariant
    def test_story_cannot_move_downstream_without_actor_and_approval(self, story):
        """Story cannot move downstream until Actor is assigned and Story is approved."""
        with pytest.raises(ValidationError, match="without approval"):
            DomainValidator.validate_story_cannot_move_downstream_without_actor_and_approval(story)

    @pytest.mark.invariant
    def test_approved_story_can_move_downstream(self, approved_story):
        DomainValidator.validate_story_cannot_move_downstream_without_actor_and_approval(
            approved_story
        )


class TestFlowInvariants:
    """Section 14 — Flow invariants."""

    @pytest.mark.invariant
    def test_flow_belongs_to_story(self, flow, story):
        DomainValidator.validate_flow_belongs_to_story(flow, story)

    @pytest.mark.invariant
    def test_primary_flow_uniqueness(self, story, flow):
        """One Story must support exactly one primary Flow."""
        DomainValidator.validate_primary_flow_uniqueness(story, [flow])

    @pytest.mark.invariant
    def test_duplicate_primary_flow_rejected(self, product, feature, story):
        flows = [
            UserFlow(
                flow_id="f-a", product_id=product.product_id,
                feature_id=feature.feature_id, story_id=story.story_id,
                title="A", flow_type=FlowType.PRIMARY,
                mermaid_source="graph TD\n A-->B",
                created_by="u", updated_by="u",
            ),
            UserFlow(
                flow_id="f-b", product_id=product.product_id,
                feature_id=feature.feature_id, story_id=story.story_id,
                title="B", flow_type=FlowType.PRIMARY,
                mermaid_source="graph TD\n A-->C",
                created_by="u", updated_by="u",
            ),
        ]
        with pytest.raises(ValidationError, match="at most one primary"):
            DomainValidator.validate_primary_flow_uniqueness(story, flows)

    @pytest.mark.invariant
    def test_flow_must_be_approved_before_use_case_generation(self, flow):
        with pytest.raises(ValidationError, match="approved before Use Case"):
            DomainValidator.validate_flow_approved_before_use_case_generation(flow)

    @pytest.mark.invariant
    def test_approved_flow_allows_use_case_generation(self, approved_flow):
        DomainValidator.validate_flow_approved_before_use_case_generation(approved_flow)

    @pytest.mark.invariant
    def test_flow_must_have_mermaid(self):
        """Section 14 — all User Flows must be stored in Mermaid."""
        f = UserFlow(
            flow_id="f-no-mermaid",
            product_id="p-1",
            feature_id="f-1",
            story_id="s-1",
            title="No mermaid",
            mermaid_source=None,
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="Mermaid source"):
            DomainValidator.validate_flow_is_mermaid(f)

    @pytest.mark.invariant
    def test_empty_mermaid_rejected(self):
        f = UserFlow(
            flow_id="f-empty",
            product_id="p-1",
            feature_id="f-1",
            story_id="s-1",
            title="Empty mermaid",
            mermaid_source="  ",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="Mermaid source"):
            DomainValidator.validate_flow_is_mermaid(f)


class TestUseCaseInvariants:
    """Section 15 — Use Case invariants."""

    @pytest.mark.invariant
    def test_use_case_belongs_to_flow(self, use_case, flow):
        DomainValidator.validate_use_case_belongs_to_flow(use_case, flow)

    @pytest.mark.invariant
    def test_use_case_must_be_approved_before_requirement(self, use_case):
        with pytest.raises(ValidationError, match="approved before Requirement"):
            DomainValidator.validate_use_case_approved_before_requirement(use_case)

    @pytest.mark.invariant
    def test_approved_use_case_allows_requirement(self, approved_use_case):
        DomainValidator.validate_use_case_approved_before_requirement(approved_use_case)


class TestRequirementInvariants:
    """Section 16 — Requirement invariants."""

    @pytest.mark.invariant
    def test_requirement_has_upstream_source(self, requirement):
        DomainValidator.validate_requirement_has_upstream_source(requirement)

    @pytest.mark.invariant
    def test_requirement_without_source_rejected(self, product, feature):
        r = Requirement(
            requirement_id="r-no-source",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            title="No source",
            requirement_type=RequirementType.FUNCTIONAL,
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="upstream traceable source"):
            DomainValidator.validate_requirement_has_upstream_source(r)

    @pytest.mark.invariant
    def test_cross_cutting_requirement_with_source_id(self, product, feature):
        """Section 16.1 — cross-cutting requirements supported."""
        r = Requirement(
            requirement_id="r-cross",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            title="Security constraint",
            requirement_type=RequirementType.SECURITY,
            source_id="product-security-policy",
            created_by="u",
            updated_by="u",
        )
        DomainValidator.validate_requirement_has_upstream_source(r)


class TestArchitectureInvariants:
    """Section 17 — Architecture invariants."""

    @pytest.mark.invariant
    def test_architecture_only_from_approved_requirements(self, approved_requirement):
        DomainValidator.validate_architecture_only_from_approved([approved_requirement])

    @pytest.mark.invariant
    def test_architecture_from_unapproved_requirements_rejected(self, requirement):
        with pytest.raises(ValidationError, match="approved"):
            DomainValidator.validate_architecture_only_from_approved([requirement])


class TestTestDesignInvariants:
    """Section 19 — Test Design invariants."""

    @pytest.mark.invariant
    def test_test_design_linked_to_requirement(self, test_design):
        DomainValidator.validate_test_design_linked_to_requirement(test_design)

    @pytest.mark.invariant
    def test_test_design_without_requirement_rejected(self, product):
        td = TestDesign(
            test_design_id="td-bad",
            product_id=product.product_id,
            requirement_id="",
            title="No req",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="linked to a Requirement"):
            DomainValidator.validate_test_design_linked_to_requirement(td)


class TestTestCaseInvariants:
    """Section 20 — Test Case invariants."""

    @pytest.mark.invariant
    def test_test_case_traceable(self, test_case):
        DomainValidator.validate_test_case_traceable(test_case)

    @pytest.mark.invariant
    def test_test_case_without_traceability_rejected(self, product):
        tc = TestCase(
            test_id="tc-bad",
            product_id=product.product_id,
            title="No trace",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="traceable"):
            DomainValidator.validate_test_case_traceable(tc)


class TestTaskInvariants:
    """Section 21 — Task invariants."""

    @pytest.mark.invariant
    def test_task_has_requirements(self, task):
        DomainValidator.validate_task_has_requirements(task)

    @pytest.mark.invariant
    def test_task_without_requirements_rejected(self, product, feature):
        t = Task(
            task_id="t-bad",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            title="No reqs",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="at least one Requirement"):
            DomainValidator.validate_task_has_requirements(t)

    @pytest.mark.invariant
    def test_task_needs_tests_for_code_gen(self, task):
        DomainValidator.validate_task_has_linked_tests_for_code_gen(task)

    @pytest.mark.invariant
    def test_task_without_tests_cannot_generate_code(self, product, feature):
        t = Task(
            task_id="t-no-tests",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            requirement_ids=["r-1"],
            title="No tests",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="linked Test Cases"):
            DomainValidator.validate_task_has_linked_tests_for_code_gen(t)

    @pytest.mark.invariant
    def test_task_needs_context_package(self, task):
        DomainValidator.validate_task_has_context_package(task)

    @pytest.mark.invariant
    def test_task_without_context_package_rejected(self, product, feature):
        t = Task(
            task_id="t-no-cp",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            requirement_ids=["r-1"],
            title="No CP",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="Context Package"):
            DomainValidator.validate_task_has_context_package(t)


class TestDependencyOutputInvariants:
    """Section 22 — Dependency Output invariants."""

    @pytest.mark.invariant
    def test_approved_dep_output_for_downstream(self, dependency_output):
        DomainValidator.validate_dependency_output_approved_for_downstream(dependency_output)

    @pytest.mark.invariant
    def test_unapproved_dep_output_rejected(self, task):
        dep = DependencyOutput(
            dependency_output_id="dep-bad",
            task_id=task.task_id,
            title="Not approved",
            status=BaseStatus.DRAFT,
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="approved for downstream"):
            DomainValidator.validate_dependency_output_approved_for_downstream(dep)


class TestDeletionRules:
    """Section 4 — deletion rules."""

    @pytest.mark.invariant
    def test_referenced_entity_cannot_be_physically_deleted(self):
        with pytest.raises(ValidationError, match="referenced downstream"):
            DomainValidator.validate_traceable_entity_not_physically_deleted(
                BaseStatus.APPROVED, has_downstream=True
            )

    @pytest.mark.invariant
    def test_unreferenced_draft_can_be_deleted(self):
        DomainValidator.validate_physical_deletion_allowed(
            BaseStatus.DRAFT, has_downstream=False
        )

    @pytest.mark.invariant
    def test_non_draft_cannot_be_deleted(self):
        with pytest.raises(ValidationError, match="not in draft"):
            DomainValidator.validate_physical_deletion_allowed(
                BaseStatus.APPROVED, has_downstream=False
            )

    @pytest.mark.invariant
    def test_referenced_draft_cannot_be_deleted(self):
        with pytest.raises(ValidationError, match="downstream references"):
            DomainValidator.validate_physical_deletion_allowed(
                BaseStatus.DRAFT, has_downstream=True
            )


class TestCodeGenerationInvariants:
    """Section 25 — Code generation invariants."""

    @pytest.mark.invariant
    def test_code_gen_valid(self, task, context_package):
        DomainValidator.validate_code_generation_prerequisites(
            task, context_package, upstream_approved=True
        )

    @pytest.mark.invariant
    def test_code_gen_without_context_package(self, task):
        with pytest.raises(ValidationError, match="Context Package"):
            DomainValidator.validate_code_generation_prerequisites(
                task, None, upstream_approved=True
            )

    @pytest.mark.invariant
    def test_code_gen_from_unapproved_upstream(self, task, context_package):
        with pytest.raises(ValidationError, match="non-approved"):
            DomainValidator.validate_code_generation_prerequisites(
                task, context_package, upstream_approved=False
            )

    @pytest.mark.invariant
    def test_code_gen_without_requirements(self, product, feature, context_package):
        t = Task(
            task_id="t-no-req",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            linked_test_ids=["tc-1"],
            title="No reqs",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="linked Requirements"):
            DomainValidator.validate_code_generation_prerequisites(
                t, context_package, upstream_approved=True
            )

    @pytest.mark.invariant
    def test_code_gen_without_tests(self, product, feature, context_package):
        t = Task(
            task_id="t-no-tests",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            requirement_ids=["r-1"],
            title="No tests",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="linked Test Cases"):
            DomainValidator.validate_code_generation_prerequisites(
                t, context_package, upstream_approved=True
            )


class TestArtifactRegistryInvariants:
    """Section 26 — Artifact Registry invariants."""

    @pytest.mark.invariant
    def test_code_artifact_has_registry_entry(self, code_artifact, registry_entry):
        DomainValidator.validate_code_artifact_registered(
            code_artifact, [registry_entry]
        )

    @pytest.mark.invariant
    def test_code_artifact_without_registry_rejected(self, code_artifact):
        with pytest.raises(ValidationError, match="Artifact Registry Entry"):
            DomainValidator.validate_code_artifact_registered(code_artifact, [])
