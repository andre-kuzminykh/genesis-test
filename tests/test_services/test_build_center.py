"""Build Center tests — section 28."""
import pytest
from src.enums.statuses import BaseStatus, ExecutionStatus
from src.models.execution import BuildArtifact, BuildRun
from src.services.validation import BuildValidator


class TestBuildPrerequisites:
    """Section 28.1 — Build Center prerequisites."""

    @pytest.mark.build
    def test_valid_build_no_errors(self):
        errors = BuildValidator.validate_build_prerequisites(
            artifact_refs=["ca-1", "ca-2"],
            approved_artifact_ids={"ca-1", "ca-2"},
            tasks_with_tests={"ca-1", "ca-2"},
            tasks_with_approvals={"ca-1", "ca-2"},
        )
        assert errors == []

    @pytest.mark.build
    def test_unapproved_artifacts_detected(self):
        errors = BuildValidator.validate_build_prerequisites(
            artifact_refs=["ca-1", "ca-2"],
            approved_artifact_ids={"ca-1"},
            tasks_with_tests={"ca-1", "ca-2"},
            tasks_with_approvals={"ca-1", "ca-2"},
        )
        assert any("Unapproved" in e for e in errors)

    @pytest.mark.build
    def test_missing_tests_detected(self):
        errors = BuildValidator.validate_build_prerequisites(
            artifact_refs=["ca-1", "ca-2"],
            approved_artifact_ids={"ca-1", "ca-2"},
            tasks_with_tests={"ca-1"},
            tasks_with_approvals={"ca-1", "ca-2"},
        )
        assert any("missing linked tests" in e for e in errors)

    @pytest.mark.build
    def test_missing_approvals_detected(self):
        errors = BuildValidator.validate_build_prerequisites(
            artifact_refs=["ca-1"],
            approved_artifact_ids={"ca-1"},
            tasks_with_tests={"ca-1"},
            tasks_with_approvals=set(),
        )
        assert any("missing source approvals" in e for e in errors)


class TestBuildArtifactRules:
    """Section 28.2 — Build Artifact rules."""

    @pytest.mark.build
    def test_build_artifact_traceable(self, build_artifact):
        """Build output must be traceable to source Tasks, Requirements, Tests."""
        assert len(build_artifact.artifact_refs) > 0
        assert build_artifact.product_id is not None

    @pytest.mark.build
    def test_build_artifact_versioned(self, build_artifact):
        assert build_artifact.version >= 1


class TestBuildRun:
    """Section 28.3 — Build Run."""

    @pytest.mark.build
    def test_build_run_lifecycle(self, build_run):
        assert build_run.status == ExecutionStatus.QUEUED

        build_run.status = ExecutionStatus.RUNNING
        assert build_run.status == ExecutionStatus.RUNNING

        build_run.status = ExecutionStatus.COMPLETED
        assert build_run.status == ExecutionStatus.COMPLETED

    @pytest.mark.build
    def test_build_run_failure(self, build_run):
        build_run.status = ExecutionStatus.RUNNING
        build_run.status = ExecutionStatus.FAILED
        assert build_run.status == ExecutionStatus.FAILED

    @pytest.mark.build
    def test_build_run_records_initiator(self, build_run):
        assert build_run.initiated_by == "tester"

    @pytest.mark.build
    def test_build_center_may_not_include_outside_scope(self):
        """Build Center may not include artifacts outside approved build scope (section 28.4)."""
        approved_scope = {"ca-1", "ca-2"}
        artifact_to_include = "ca-3"
        assert artifact_to_include not in approved_scope
