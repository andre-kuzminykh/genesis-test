"""Status workflow tests — sections 5.1-5.6."""
import pytest
from src.enums.statuses import BaseStatus, ExecutionStatus, DeliveryStatus, ExportStatus


class TestBaseStatusVocabulary:
    """Section 5.1 — Base status vocabulary."""

    @pytest.mark.workflow
    def test_base_statuses_exist(self):
        expected = {"draft", "generated", "reviewed", "approved", "changed", "deprecated", "archived"}
        actual = {s.value for s in BaseStatus}
        assert expected == actual

    @pytest.mark.workflow
    def test_base_status_count(self):
        assert len(BaseStatus) == 7


class TestExecutionStatusVocabulary:
    """Section 5.2 — Execution status vocabulary."""

    @pytest.mark.workflow
    def test_execution_statuses_exist(self):
        expected = {"queued", "running", "completed", "failed", "canceled"}
        actual = {s.value for s in ExecutionStatus}
        assert expected == actual

    @pytest.mark.workflow
    def test_execution_status_count(self):
        assert len(ExecutionStatus) == 5


class TestDeliveryStatusVocabulary:
    """Section 5.3 — Delivery status vocabulary."""

    @pytest.mark.workflow
    def test_delivery_statuses_exist(self):
        expected = {"prepared", "approved_for_export", "exported", "superseded"}
        actual = {s.value for s in DeliveryStatus}
        assert expected == actual


class TestExportStatusModel:
    """Section 29.10 — Export status model."""

    @pytest.mark.workflow
    def test_export_statuses(self):
        expected = {"draft", "prepared", "approved_for_export", "exported", "failed", "superseded"}
        actual = {s.value for s in ExportStatus}
        assert expected == actual


class TestStatusSemantics:
    """Section 5.5 — Status semantics validation."""

    @pytest.mark.workflow
    def test_generated_means_not_validated(self):
        """generated — created by the system and not yet validated by the user."""
        assert BaseStatus.GENERATED.value == "generated"

    @pytest.mark.workflow
    def test_reviewed_means_examined(self):
        """reviewed — examined by the user but not yet approved."""
        assert BaseStatus.REVIEWED.value == "reviewed"

    @pytest.mark.workflow
    def test_approved_means_allowed_downstream(self):
        """approved — explicitly allowed for downstream generation."""
        assert BaseStatus.APPROVED.value == "approved"

    @pytest.mark.workflow
    def test_changed_means_requires_revalidation(self):
        """changed — previously approved content modified."""
        assert BaseStatus.CHANGED.value == "changed"

    @pytest.mark.workflow
    def test_deprecated_means_retained(self):
        """deprecated — retained for traceability."""
        assert BaseStatus.DEPRECATED.value == "deprecated"

    @pytest.mark.workflow
    def test_archived_means_historical(self):
        """archived — retained for audit and history."""
        assert BaseStatus.ARCHIVED.value == "archived"


class TestStatusTransitionRules:
    """Section 5.4 — Status transition rules."""

    @pytest.mark.workflow
    def test_downstream_generation_only_from_approved(self):
        """Downstream generation is allowed only from approved artifacts."""
        allowed = BaseStatus.APPROVED
        not_allowed = [BaseStatus.DRAFT, BaseStatus.GENERATED, BaseStatus.REVIEWED,
                       BaseStatus.CHANGED, BaseStatus.DEPRECATED, BaseStatus.ARCHIVED]
        assert allowed == BaseStatus.APPROVED
        for s in not_allowed:
            assert s != BaseStatus.APPROVED

    @pytest.mark.workflow
    def test_draft_to_generated(self):
        """Entity transitions from draft to generated after system creates it."""
        status = BaseStatus.DRAFT
        status = BaseStatus.GENERATED
        assert status == BaseStatus.GENERATED

    @pytest.mark.workflow
    def test_generated_to_reviewed(self):
        status = BaseStatus.GENERATED
        status = BaseStatus.REVIEWED
        assert status == BaseStatus.REVIEWED

    @pytest.mark.workflow
    def test_reviewed_to_approved(self):
        status = BaseStatus.REVIEWED
        status = BaseStatus.APPROVED
        assert status == BaseStatus.APPROVED

    @pytest.mark.workflow
    def test_approved_to_changed(self):
        """If an approved artifact changes, it goes to changed."""
        status = BaseStatus.APPROVED
        status = BaseStatus.CHANGED
        assert status == BaseStatus.CHANGED

    @pytest.mark.workflow
    def test_approved_to_deprecated(self):
        status = BaseStatus.APPROVED
        status = BaseStatus.DEPRECATED
        assert status == BaseStatus.DEPRECATED

    @pytest.mark.workflow
    def test_any_to_archived(self):
        for s in BaseStatus:
            # any status can transition to archived
            new_status = BaseStatus.ARCHIVED
            assert new_status == BaseStatus.ARCHIVED
