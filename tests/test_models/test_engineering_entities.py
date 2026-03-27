"""Tests for engineering truth entities — sections 17-22, 26."""
import pytest
from src.enums.statuses import BaseStatus
from src.enums.types import ArchitectureArtifactType, TestCategory
from src.models.engineering import (
    ArchitectureArtifact, Task, Subtask, TestDesign, TestCase,
    DependencyOutput, CodeArtifact, ArtifactRegistryEntry, TestSuite,
)


class TestArchitectureArtifact:
    """Section 17 — Architecture Artifact tests."""

    def test_architecture_has_required_fields(self, architecture):
        assert architecture.architecture_id is not None
        assert architecture.product_id is not None
        assert architecture.artifact_type == ArchitectureArtifactType.SERVICE
        assert architecture.title is not None

    def test_architecture_versioned(self, architecture):
        assert architecture.version >= 1

    def test_architecture_can_be_product_scoped(self, product):
        """Architecture Artifacts may be product-scoped (section 17.3)."""
        a = ArchitectureArtifact(
            architecture_id="arch-prod",
            product_id=product.product_id,
            feature_id=None,
            artifact_type=ArchitectureArtifactType.INFRASTRUCTURE,
            title="Infrastructure arch",
            created_by="u",
            updated_by="u",
        )
        assert a.feature_id is None

    def test_architecture_can_be_feature_scoped(self, architecture):
        """Architecture Artifacts may be feature-scoped (section 17.3)."""
        assert architecture.feature_id is not None

    def test_architecture_supports_mermaid(self, architecture):
        assert architecture.mermaid_source is not None

    @pytest.mark.parametrize("art_type", list(ArchitectureArtifactType))
    def test_all_architecture_types(self, product, art_type):
        """Section 17.1 — all minimum artifact types."""
        a = ArchitectureArtifact(
            architecture_id=f"arch-{art_type.value}",
            product_id=product.product_id,
            artifact_type=art_type,
            title=f"Test {art_type.value}",
            created_by="u",
            updated_by="u",
        )
        assert a.artifact_type == art_type


class TestTask:
    """Section 21 — Task entity tests."""

    def test_task_has_required_fields(self, task):
        assert task.task_id is not None
        assert task.product_id is not None
        assert task.feature_id is not None
        assert task.title is not None

    def test_task_linked_to_requirements(self, task):
        """Task must be traceable to one or more Requirements (section 9.2)."""
        assert len(task.requirement_ids) > 0

    def test_task_linked_to_tests(self, task):
        assert len(task.linked_test_ids) > 0

    def test_task_has_context_package_ref(self, task):
        assert task.context_package_ref is not None

    def test_task_supports_acceptance_criteria(self):
        t = Task(
            task_id="t-ac",
            product_id="p-1",
            feature_id="f-1",
            requirement_ids=["r-1"],
            title="Task with AC",
            acceptance_criteria=["AC1: Validates input", "AC2: Returns error on failure"],
            definition_of_done=["DoD1: Tests pass", "DoD2: Code reviewed"],
            created_by="u",
            updated_by="u",
        )
        assert len(t.acceptance_criteria) == 2
        assert len(t.definition_of_done) == 2

    def test_task_supports_dependencies(self):
        t = Task(
            task_id="t-dep",
            product_id="p-1",
            feature_id="f-1",
            requirement_ids=["r-1"],
            title="Task with deps",
            dependencies=["task-upstream-1"],
            created_by="u",
            updated_by="u",
        )
        assert "task-upstream-1" in t.dependencies


class TestSubtask:
    """Section 21.2 — Subtask entity tests."""

    def test_subtask_belongs_to_task(self, subtask, task):
        assert subtask.task_id == task.task_id

    def test_subtask_has_title(self, subtask):
        assert subtask.title is not None

    def test_subtask_can_link_tests(self):
        s = Subtask(
            subtask_id="sub-linked",
            task_id="t-1",
            title="Subtask with tests",
            linked_test_ids=["tc-1", "tc-2"],
            created_by="u",
            updated_by="u",
        )
        assert len(s.linked_test_ids) == 2


class TestTestDesign:
    """Section 19 — Test Design entity tests."""

    def test_test_design_linked_to_requirement(self, test_design):
        """Section 19.3 — Test Design derived from Requirement."""
        assert test_design.requirement_id is not None

    def test_test_design_has_intent(self, test_design):
        assert test_design.test_intent is not None

    def test_test_design_versioned(self, test_design):
        assert test_design.version >= 1


class TestTestCase:
    """Section 20 — Test Case entity tests."""

    def test_test_case_has_required_fields(self, test_case):
        assert test_case.test_id is not None
        assert test_case.title is not None
        assert test_case.category == TestCategory.UNIT

    def test_test_case_traceable_to_requirement(self, test_case):
        assert test_case.requirement_id is not None

    def test_test_case_traceable_to_test_design(self, test_case):
        assert test_case.test_design_id is not None

    @pytest.mark.parametrize("cat", list(TestCategory))
    def test_all_test_categories(self, product, cat):
        """Section 20.2 — all minimum test categories."""
        tc = TestCase(
            test_id=f"tc-{cat.value}",
            product_id=product.product_id,
            title=f"Test {cat.value}",
            category=cat,
            requirement_id="req-1",
            created_by="u",
            updated_by="u",
        )
        assert tc.category == cat


class TestDependencyOutput:
    """Section 22 — Dependency Output tests."""

    def test_dependency_output_linked_to_task(self, dependency_output, task):
        assert dependency_output.task_id == task.task_id

    def test_dependency_output_has_status(self, dependency_output):
        assert dependency_output.status == BaseStatus.APPROVED

    def test_dependency_output_versioned(self, dependency_output):
        assert dependency_output.version >= 1


class TestCodeArtifact:
    """Section 26.1 — Code Artifact tests."""

    def test_code_artifact_linked_to_task(self, code_artifact, task):
        assert code_artifact.task_id == task.task_id

    def test_code_artifact_has_logical_name(self, code_artifact):
        assert code_artifact.logical_name == "auth_service.py"


class TestArtifactRegistryEntry:
    """Section 26.2 — Artifact Registry Entry tests."""

    def test_registry_entry_linked_to_code_artifact(self, registry_entry, code_artifact):
        assert registry_entry.code_artifact_id == code_artifact.code_artifact_id

    def test_registry_entry_has_file_path(self, registry_entry):
        assert registry_entry.file_path is not None

    def test_registry_entry_has_content_hash(self, registry_entry):
        assert registry_entry.content_hash is not None


class TestTestSuite:
    """Test Suite grouping."""

    def test_test_suite_groups_test_cases(self, product):
        ts = TestSuite(
            test_suite_id="ts-1",
            product_id=product.product_id,
            title="Auth test suite",
            test_ids=["tc-1", "tc-2", "tc-3"],
            created_by="u",
            updated_by="u",
        )
        assert len(ts.test_ids) == 3
