"""Engineering truth entities per specification sections 8.2, 17-22, 26."""
from typing import Optional
from pydantic import Field

from src.models.base import ApprovableEntity
from src.enums.types import (
    ArchitectureArtifactType,
    TestCategory,
)


class ArchitectureArtifact(ApprovableEntity):
    """Section 17 — Architecture Artifact entity."""
    architecture_id: str
    product_id: str
    feature_id: Optional[str] = None
    artifact_type: ArchitectureArtifactType
    title: str
    description: Optional[str] = None
    mermaid_source: Optional[str] = None
    json_payload: Optional[str] = None


class Task(ApprovableEntity):
    """Section 21.1 — Task entity."""
    task_id: str
    product_id: str
    feature_id: str
    story_id: Optional[str] = None
    use_case_id: Optional[str] = None
    requirement_ids: list[str] = Field(default_factory=list)
    architecture_ids: list[str] = Field(default_factory=list)
    test_design_ids: list[str] = Field(default_factory=list)
    linked_test_ids: list[str] = Field(default_factory=list)
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = None
    owner_role: Optional[str] = None
    priority: Optional[str] = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    definition_of_done: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    context_package_ref: Optional[str] = None
    estimate: Optional[str] = None
    risk_level: Optional[str] = None


class Subtask(ApprovableEntity):
    """Section 21.2 — Subtask entity."""
    subtask_id: str
    task_id: str
    title: str
    description: Optional[str] = None
    linked_test_ids: list[str] = Field(default_factory=list)
    linked_artifact_ids: list[str] = Field(default_factory=list)
    context_package_ref: Optional[str] = None


class TestDesign(ApprovableEntity):
    """Section 19 — Test Design entity."""
    test_design_id: str
    product_id: str
    feature_id: Optional[str] = None
    story_id: Optional[str] = None
    flow_id: Optional[str] = None
    use_case_id: Optional[str] = None
    requirement_id: str
    title: str
    test_intent: Optional[str] = None
    test_type: Optional[str] = None
    category: Optional[str] = None
    coverage_notes: Optional[str] = None


class TestCase(ApprovableEntity):
    """Section 20 — Test Case entity."""
    test_id: str
    product_id: str
    feature_id: Optional[str] = None
    story_id: Optional[str] = None
    flow_id: Optional[str] = None
    use_case_id: Optional[str] = None
    requirement_id: Optional[str] = None
    test_design_id: Optional[str] = None
    task_id: Optional[str] = None
    architecture_id: Optional[str] = None
    code: Optional[str] = None
    title: str
    test_type: Optional[str] = None
    category: TestCategory = TestCategory.UNIT
    preconditions: Optional[str] = None
    steps: Optional[str] = None
    expected_result: Optional[str] = None
    automation_level: Optional[str] = None


class DependencyOutput(ApprovableEntity):
    """Section 22 — Dependency Output entity."""
    dependency_output_id: str
    task_id: str
    output_type: Optional[str] = None
    title: str
    summary: Optional[str] = None
    artifact_refs: list[str] = Field(default_factory=list)
    contract_refs: list[str] = Field(default_factory=list)
    schema_refs: list[str] = Field(default_factory=list)


class CodeArtifact(ApprovableEntity):
    """Section 26.1 — Code Artifact entity."""
    code_artifact_id: str
    task_id: str
    artifact_type: Optional[str] = None
    logical_name: str
    content_ref: Optional[str] = None


class ArtifactRegistryEntry(ApprovableEntity):
    """Section 26.2 — Artifact Registry Entry entity."""
    artifact_registry_entry_id: str
    code_artifact_id: str
    file_path: str
    content_hash: Optional[str] = None
    source_generation_run_id: Optional[str] = None
    repository_target_id: Optional[str] = None


class TestSuite(ApprovableEntity):
    """Test Suite — grouping of Test Cases."""
    test_suite_id: str
    product_id: str
    feature_id: Optional[str] = None
    title: str
    test_ids: list[str] = Field(default_factory=list)
