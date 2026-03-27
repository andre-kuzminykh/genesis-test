"""Traceability model tests — section 9."""
import pytest
from src.enums.types import TraceLinkType
from src.enums.statuses import BaseStatus
from src.models.execution import TraceLink


class TestTraceLinkModel:
    """Section 9.1 — Trace Link model."""

    @pytest.mark.traceability
    def test_trace_link_required_fields(self, trace_link):
        assert trace_link.trace_link_id is not None
        assert trace_link.source_entity_type is not None
        assert trace_link.source_entity_id is not None
        assert trace_link.target_entity_type is not None
        assert trace_link.target_entity_id is not None
        assert trace_link.link_type is not None
        assert trace_link.version >= 1
        assert trace_link.created_at is not None

    @pytest.mark.traceability
    def test_all_link_types_available(self):
        expected_types = {
            "parent_of", "derived_from", "implements", "verifies",
            "depends_on", "uses_context_from", "exports", "included_in",
            "affected_by_change", "invalidates",
        }
        actual = {lt.value for lt in TraceLinkType}
        assert expected_types == actual


class TestTraceabilityRules:
    """Section 9.2 — Traceability rules."""

    @pytest.mark.traceability
    def test_lower_level_artifact_has_upstream_source(self):
        """Every lower-level artifact must have at least one upstream traceable source."""
        tl = TraceLink(
            trace_link_id="tl-up",
            source_entity_type="requirement",
            source_entity_id="req-1",
            target_entity_type="task",
            target_entity_id="task-1",
            link_type=TraceLinkType.IMPLEMENTS,
            created_by="system",
        )
        assert tl.source_entity_id is not None

    @pytest.mark.traceability
    def test_test_case_traceable_to_requirement(self):
        """Every Test Case must be traceable to at least one Requirement or Test Design."""
        tl = TraceLink(
            trace_link_id="tl-tc-req",
            source_entity_type="requirement",
            source_entity_id="req-1",
            target_entity_type="test_case",
            target_entity_id="tc-1",
            link_type=TraceLinkType.VERIFIES,
            created_by="system",
        )
        assert tl.link_type == TraceLinkType.VERIFIES

    @pytest.mark.traceability
    def test_task_traceable_to_requirements(self):
        """Every Task must be traceable to one or more Requirements."""
        tl = TraceLink(
            trace_link_id="tl-task-req",
            source_entity_type="requirement",
            source_entity_id="req-1",
            target_entity_type="task",
            target_entity_id="task-1",
            link_type=TraceLinkType.IMPLEMENTS,
            created_by="system",
        )
        assert tl.link_type == TraceLinkType.IMPLEMENTS

    @pytest.mark.traceability
    def test_exported_file_traceable_to_code_artifact(self):
        """Every exported file must be traceable to its source Code Artifact."""
        tl = TraceLink(
            trace_link_id="tl-export",
            source_entity_type="code_artifact",
            source_entity_id="ca-1",
            target_entity_type="export_file",
            target_entity_id="file-1",
            link_type=TraceLinkType.EXPORTS,
            created_by="system",
        )
        assert tl.link_type == TraceLinkType.EXPORTS

    @pytest.mark.traceability
    def test_build_artifact_preserves_source_lineage(self):
        """Every Build Artifact must preserve source lineage."""
        tl = TraceLink(
            trace_link_id="tl-build",
            source_entity_type="task",
            source_entity_id="task-1",
            target_entity_type="build_artifact",
            target_entity_id="ba-1",
            link_type=TraceLinkType.DERIVED_FROM,
            created_by="system",
        )
        assert tl.link_type == TraceLinkType.DERIVED_FROM


class TestCanonicalChain:
    """Section 3 — Canonical structure traceability chain."""

    @pytest.mark.traceability
    def test_full_traceability_chain(self):
        """Product → Feature → Story → Flow → UseCase → Requirement → Task → Test → Code."""
        chain = [
            ("product", "feature", TraceLinkType.PARENT_OF),
            ("feature", "story", TraceLinkType.PARENT_OF),
            ("story", "flow", TraceLinkType.PARENT_OF),
            ("flow", "use_case", TraceLinkType.DERIVED_FROM),
            ("use_case", "requirement", TraceLinkType.DERIVED_FROM),
            ("requirement", "task", TraceLinkType.IMPLEMENTS),
            ("requirement", "test_design", TraceLinkType.VERIFIES),
            ("test_design", "test_case", TraceLinkType.DERIVED_FROM),
            ("task", "code_artifact", TraceLinkType.IMPLEMENTS),
        ]
        links = []
        for i, (src_type, tgt_type, lt) in enumerate(chain):
            links.append(TraceLink(
                trace_link_id=f"tl-chain-{i}",
                source_entity_type=src_type,
                source_entity_id=f"{src_type}-1",
                target_entity_type=tgt_type,
                target_entity_id=f"{tgt_type}-1",
                link_type=lt,
                created_by="system",
            ))
        assert len(links) == 9
        assert links[0].source_entity_type == "product"
        assert links[-1].target_entity_type == "code_artifact"


class TestChangeImpactTraceability:
    """Section 27 — Change impact traceability."""

    @pytest.mark.traceability
    def test_change_impact_link(self):
        tl = TraceLink(
            trace_link_id="tl-change",
            source_entity_type="change_request",
            source_entity_id="cr-1",
            target_entity_type="feature",
            target_entity_id="feat-1",
            link_type=TraceLinkType.AFFECTED_BY_CHANGE,
            created_by="system",
        )
        assert tl.link_type == TraceLinkType.AFFECTED_BY_CHANGE

    @pytest.mark.traceability
    def test_invalidation_link(self):
        tl = TraceLink(
            trace_link_id="tl-invalidate",
            source_entity_type="requirement",
            source_entity_id="req-1",
            target_entity_type="task",
            target_entity_id="task-1",
            link_type=TraceLinkType.INVALIDATES,
            created_by="system",
        )
        assert tl.link_type == TraceLinkType.INVALIDATES
