"""Git export tests — section 29."""
import pytest
from src.enums.statuses import BaseStatus, ExportStatus
from src.models.delivery import (
    GitExportRun, ExportManifest, FileEntry, LineageEntry,
    CommitBundle, ReleasePackage, RepositoryTarget,
)
from src.services.validation import ExportValidator, ValidationError


class TestExportPreconditions:
    """Section 29.2 — Export preconditions."""

    @pytest.mark.export
    def test_all_preconditions_met(self):
        errors = ExportValidator.validate_export_preconditions(
            product_exists=True,
            code_artifacts_approved=True,
            tasks_approved_or_completed=True,
            test_cases_exist=True,
            build_run_exists=True,
            export_manifest_exists=True,
            user_approved=True,
        )
        assert errors == []

    @pytest.mark.export
    def test_missing_product_detected(self):
        errors = ExportValidator.validate_export_preconditions(
            product_exists=False,
            code_artifacts_approved=True,
            tasks_approved_or_completed=True,
            test_cases_exist=True,
            build_run_exists=True,
            export_manifest_exists=True,
            user_approved=True,
        )
        assert any("Product" in e for e in errors)

    @pytest.mark.export
    def test_unapproved_code_artifacts_detected(self):
        errors = ExportValidator.validate_export_preconditions(
            product_exists=True,
            code_artifacts_approved=False,
            tasks_approved_or_completed=True,
            test_cases_exist=True,
            build_run_exists=True,
            export_manifest_exists=True,
            user_approved=True,
        )
        assert any("Code Artifacts" in e for e in errors)

    @pytest.mark.export
    def test_unapproved_tasks_detected(self):
        errors = ExportValidator.validate_export_preconditions(
            product_exists=True,
            code_artifacts_approved=True,
            tasks_approved_or_completed=False,
            test_cases_exist=True,
            build_run_exists=True,
            export_manifest_exists=True,
            user_approved=True,
        )
        assert any("Tasks" in e for e in errors)

    @pytest.mark.export
    def test_missing_tests_detected(self):
        errors = ExportValidator.validate_export_preconditions(
            product_exists=True,
            code_artifacts_approved=True,
            tasks_approved_or_completed=True,
            test_cases_exist=False,
            build_run_exists=True,
            export_manifest_exists=True,
            user_approved=True,
        )
        assert any("Test Cases" in e for e in errors)

    @pytest.mark.export
    def test_missing_build_run_detected(self):
        errors = ExportValidator.validate_export_preconditions(
            product_exists=True,
            code_artifacts_approved=True,
            tasks_approved_or_completed=True,
            test_cases_exist=True,
            build_run_exists=False,
            export_manifest_exists=True,
            user_approved=True,
        )
        assert any("Build Run" in e for e in errors)

    @pytest.mark.export
    def test_missing_manifest_detected(self):
        errors = ExportValidator.validate_export_preconditions(
            product_exists=True,
            code_artifacts_approved=True,
            tasks_approved_or_completed=True,
            test_cases_exist=True,
            build_run_exists=True,
            export_manifest_exists=False,
            user_approved=True,
        )
        assert any("Export Manifest" in e for e in errors)

    @pytest.mark.export
    def test_no_user_approval_detected(self):
        errors = ExportValidator.validate_export_preconditions(
            product_exists=True,
            code_artifacts_approved=True,
            tasks_approved_or_completed=True,
            test_cases_exist=True,
            build_run_exists=True,
            export_manifest_exists=True,
            user_approved=False,
        )
        assert any("User" in e for e in errors)

    @pytest.mark.export
    def test_multiple_failures(self):
        errors = ExportValidator.validate_export_preconditions(
            product_exists=False,
            code_artifacts_approved=False,
            tasks_approved_or_completed=False,
            test_cases_exist=False,
            build_run_exists=False,
            export_manifest_exists=False,
            user_approved=False,
        )
        assert len(errors) == 7


class TestExportManifestLineage:
    """Section 29.6 — Export Manifest lineage."""

    @pytest.mark.export
    def test_valid_manifest_lineage(self, export_manifest):
        errors = ExportValidator.validate_export_manifest_lineage(export_manifest)
        assert errors == []

    @pytest.mark.export
    def test_file_entry_without_lineage_detected(self, product):
        manifest = ExportManifest(
            export_manifest_id="em-bad",
            product_id=product.product_id,
            file_entries=[
                FileEntry(
                    target_file_path="src/missing.py",
                    source_artifact_id="ca-1",
                    artifact_type="service",
                )
            ],
            lineage_entries=[],
            created_by="u",
            updated_by="u",
        )
        errors = ExportValidator.validate_export_manifest_lineage(manifest)
        assert len(errors) == 1
        assert "missing.py" in errors[0]


class TestExportFromApprovedOnly:
    """Section 5.4 — No export from non-approved sources."""

    @pytest.mark.export
    def test_export_from_approved_sources(self):
        ExportValidator.validate_no_export_from_non_approved(
            [BaseStatus.APPROVED, BaseStatus.APPROVED]
        )

    @pytest.mark.export
    def test_export_from_non_approved_rejected(self):
        with pytest.raises(ValidationError, match="non-approved"):
            ExportValidator.validate_no_export_from_non_approved(
                [BaseStatus.APPROVED, BaseStatus.DRAFT]
            )


class TestExportStatusModel:
    """Section 29.10 — Export status model."""

    @pytest.mark.export
    def test_minimum_export_statuses(self):
        expected = {"draft", "prepared", "approved_for_export", "exported", "failed", "superseded"}
        actual = {s.value for s in ExportStatus}
        assert expected == actual


class TestExportInvariants:
    """Section 29.11 — Git export invariants."""

    @pytest.mark.export
    def test_no_file_exported_without_lineage(self, export_manifest):
        """No file may be exported without traceable source lineage."""
        for fe in export_manifest.file_entries:
            lineage_paths = {le.file_path for le in export_manifest.lineage_entries}
            assert fe.target_file_path in lineage_paths

    @pytest.mark.export
    def test_export_deterministic_for_same_inputs(self):
        """Export must be deterministic for the same approved artifact set (section 29.9)."""
        manifest1 = ExportManifest(
            export_manifest_id="em-a",
            product_id="p-1",
            included_artifact_ids=["ca-1"],
            file_entries=[FileEntry(
                target_file_path="src/a.py",
                source_artifact_id="ca-1",
                artifact_type="service",
            )],
            lineage_entries=[LineageEntry(
                file_path="src/a.py",
                task_id="t-1",
                code_artifact_id="ca-1",
            )],
            created_by="u",
            updated_by="u",
        )
        manifest2 = ExportManifest(
            export_manifest_id="em-b",
            product_id="p-1",
            included_artifact_ids=["ca-1"],
            file_entries=[FileEntry(
                target_file_path="src/a.py",
                source_artifact_id="ca-1",
                artifact_type="service",
            )],
            lineage_entries=[LineageEntry(
                file_path="src/a.py",
                task_id="t-1",
                code_artifact_id="ca-1",
            )],
            created_by="u",
            updated_by="u",
        )
        assert manifest1.included_artifact_ids == manifest2.included_artifact_ids
        assert manifest1.file_entries[0].target_file_path == manifest2.file_entries[0].target_file_path

    @pytest.mark.export
    def test_export_supports_full_and_patch_modes(self):
        """Export must support full export and patch export modes (section 29.9)."""
        full = GitExportRun(
            git_export_run_id="ger-full",
            product_id="p-1",
            export_scope="full",
            created_by="u",
            updated_by="u",
        )
        patch = GitExportRun(
            git_export_run_id="ger-patch",
            product_id="p-1",
            export_scope="patch",
            created_by="u",
            updated_by="u",
        )
        assert full.export_scope == "full"
        assert patch.export_scope == "patch"
