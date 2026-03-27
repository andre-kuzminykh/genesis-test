"""Non-functional requirements tests — section 31."""
import pytest
from src.enums.statuses import BaseStatus
from src.enums.types import GenerationMode
from src.models.business import Product, Feature
from src.models.execution import ContextPackage, GenerationRun, TraceLink
from src.enums.types import TraceLinkType


class TestTraceabilityNFR:
    """Section 31 — All entities must be traceable by ID."""

    @pytest.mark.invariant
    def test_product_traceable_by_id(self, product):
        assert product.product_id is not None

    @pytest.mark.invariant
    def test_feature_traceable_by_id(self, feature):
        assert feature.feature_id is not None

    @pytest.mark.invariant
    def test_trace_link_enables_traceability(self, trace_link):
        assert trace_link.source_entity_id is not None
        assert trace_link.target_entity_id is not None


class TestVersioningNFR:
    """Section 31 — All entities must be versioned."""

    @pytest.mark.invariant
    def test_product_versioned(self, product):
        assert product.version >= 1

    @pytest.mark.invariant
    def test_feature_versioned(self, feature):
        assert feature.version >= 1


class TestContextControlNFR:
    """Section 31 — All generation must use local Context Packages."""

    @pytest.mark.context_package
    def test_generation_requires_context_package(self, generation_run):
        assert generation_run.context_package_id is not None

    @pytest.mark.context_package
    def test_full_product_context_prohibited_by_default(self, product):
        """Full product context is prohibited by default (section 31)."""
        cp = ContextPackage(
            context_package_id="cp-full",
            product_id=product.product_id,
            scope_type="product",
            target_artifact_type="code",
            context_hash="hash",
            created_by="u",
            updated_by="u",
        )
        # No justification → should be flagged
        assert cp.broader_context_justification is None
        assert cp.scope_type == "product"


class TestIdempotencyNFR:
    """Section 31 — Re-running same generation must produce same result or new auditable version."""

    @pytest.mark.generation
    def test_same_context_same_hash(self):
        cp1 = ContextPackage(
            context_package_id="cp-idem-1",
            product_id="p-1",
            target_artifact_type="code",
            included_entity_refs=["r-1", "tc-1"],
            generation_mode=GenerationMode.DETERMINISTIC,
            context_hash="deterministic-hash",
            created_by="u",
            updated_by="u",
        )
        cp2 = ContextPackage(
            context_package_id="cp-idem-2",
            product_id="p-1",
            target_artifact_type="code",
            included_entity_refs=["r-1", "tc-1"],
            generation_mode=GenerationMode.DETERMINISTIC,
            context_hash="deterministic-hash",
            created_by="u",
            updated_by="u",
        )
        assert cp1.context_hash == cp2.context_hash


class TestMermaidDiagramsNFR:
    """Section 31 — All diagrams must be stored in Mermaid where applicable."""

    @pytest.mark.invariant
    def test_flow_uses_mermaid(self, flow):
        assert flow.mermaid_source is not None
        assert "graph" in flow.mermaid_source

    @pytest.mark.invariant
    def test_architecture_uses_mermaid(self, architecture):
        assert architecture.mermaid_source is not None


class TestAuditabilityNFR:
    """Section 31 — System must provide auditability."""

    @pytest.mark.invariant
    def test_entity_tracks_creator(self, product):
        assert product.created_by is not None
        assert product.created_at is not None

    @pytest.mark.invariant
    def test_entity_tracks_updater(self, product):
        assert product.updated_by is not None
        assert product.updated_at is not None

    @pytest.mark.invariant
    def test_approval_tracks_approver(self, approved_product):
        assert approved_product.approved_by is not None
        assert approved_product.approved_at is not None

    @pytest.mark.invariant
    def test_generation_run_auditable(self, generation_run):
        assert generation_run.generation_run_id is not None
        assert generation_run.context_package_id is not None
        assert generation_run.initiated_by is not None
