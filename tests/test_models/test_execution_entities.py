"""Tests for execution truth entities — sections 8.3, 9, 23-24, 27-28."""
import pytest
from src.enums.statuses import BaseStatus, ExecutionStatus
from src.enums.types import GenerationMode, ChangeType, TraceLinkType
from src.models.execution import (
    TraceLink, ContextPackage, GenerationRun,
    ChangeRequest, ChangeSetItem, ChangeImpactMap,
    BuildArtifact, BuildRun,
)


class TestTraceLink:
    """Section 9.1 — Trace Link tests."""

    def test_trace_link_fields(self, trace_link):
        assert trace_link.trace_link_id is not None
        assert trace_link.source_entity_type == "requirement"
        assert trace_link.source_entity_id == "req-1"
        assert trace_link.target_entity_type == "task"
        assert trace_link.target_entity_id == "task-1"
        assert trace_link.link_type == TraceLinkType.IMPLEMENTS

    def test_trace_link_versioned(self, trace_link):
        assert trace_link.version >= 1

    @pytest.mark.parametrize("link_type", list(TraceLinkType))
    def test_all_link_types(self, link_type):
        """Section 9.1 — all typical link types."""
        tl = TraceLink(
            trace_link_id=f"tl-{link_type.value}",
            source_entity_type="entity_a",
            source_entity_id="a-1",
            target_entity_type="entity_b",
            target_entity_id="b-1",
            link_type=link_type,
            created_by="u",
        )
        assert tl.link_type == link_type


class TestContextPackage:
    """Section 23 — Context Package tests."""

    def test_context_package_fields(self, context_package):
        assert context_package.context_package_id is not None
        assert context_package.target_artifact_type == "code"
        assert context_package.context_hash is not None

    def test_context_package_included_refs(self, context_package):
        assert len(context_package.included_entity_refs) > 0

    def test_context_package_generation_mode(self, context_package):
        assert context_package.generation_mode == GenerationMode.DETERMINISTIC


class TestGenerationRun:
    """Section 24 — Generation Run tests."""

    def test_generation_run_fields(self, generation_run):
        assert generation_run.generation_run_id is not None
        assert generation_run.context_package_id == "cp-1"
        assert generation_run.target_entity_type == "code_artifact"
        assert generation_run.status == ExecutionStatus.QUEUED

    def test_generation_run_modes(self):
        for mode in GenerationMode:
            gr = GenerationRun(
                generation_run_id=f"gr-{mode.value}",
                target_entity_type="code",
                target_entity_id="ca-1",
                context_package_id="cp-1",
                generation_mode=mode,
            )
            assert gr.generation_mode == mode


class TestChangeRequest:
    """Section 27.2 — Change Request tests."""

    def test_change_request_fields(self, change_request):
        assert change_request.change_request_id is not None
        assert change_request.product_id == "prod-1"
        assert change_request.title is not None
        assert change_request.change_reason is not None

    def test_change_request_versioned(self, change_request):
        assert change_request.version >= 1


class TestChangeSetItem:
    """Section 27.3 — Change Set Item tests."""

    def test_change_set_item_fields(self, change_set_item):
        assert change_set_item.change_request_id == "cr-1"
        assert change_set_item.target_entity_type == "feature"
        assert change_set_item.change_type == ChangeType.UPDATE

    @pytest.mark.parametrize("ct", list(ChangeType))
    def test_all_change_types(self, ct):
        """Section 27.1 — all supported change types."""
        csi = ChangeSetItem(
            change_set_item_id=f"csi-{ct.value}",
            change_request_id="cr-1",
            target_entity_type="entity",
            target_entity_id="e-1",
            change_type=ct,
            created_by="u",
            updated_by="u",
        )
        assert csi.change_type == ct


class TestChangeImpactMap:
    """Section 27.4 — Change Impact Map tests."""

    def test_impact_map_fields(self, change_impact_map):
        assert change_impact_map.change_request_id == "cr-1"
        assert len(change_impact_map.affected_entity_refs) > 0
        assert len(change_impact_map.invalidated_entity_refs) > 0
        assert len(change_impact_map.regeneration_candidates) > 0


class TestBuildArtifact:
    """Section 28.2 — Build Artifact tests."""

    def test_build_artifact_fields(self, build_artifact):
        assert build_artifact.build_artifact_id is not None
        assert build_artifact.product_id == "prod-1"
        assert len(build_artifact.artifact_refs) > 0


class TestBuildRun:
    """Section 28.3 — Build Run tests."""

    def test_build_run_fields(self, build_run):
        assert build_run.build_run_id is not None
        assert build_run.build_artifact_id == "ba-1"
        assert build_run.status == ExecutionStatus.QUEUED

    def test_build_run_execution_statuses(self):
        for status in ExecutionStatus:
            br = BuildRun(
                build_run_id=f"br-{status.value}",
                product_id="p-1",
                build_artifact_id="ba-1",
                status=status,
            )
            assert br.status == status
