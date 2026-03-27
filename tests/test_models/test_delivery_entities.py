"""Tests for delivery truth entities — sections 8.4, 29."""
import pytest
from src.enums.statuses import ExportStatus
from src.models.delivery import (
    GitExportRun, RepositoryTarget, ExportManifest, CommitBundle,
    ReleasePackage, FileEntry, LineageEntry,
)


class TestGitExportRun:
    """Section 29.4 — Git Export Run tests."""

    def test_git_export_run_fields(self, git_export_run):
        assert git_export_run.git_export_run_id is not None
        assert git_export_run.product_id == "prod-1"
        assert git_export_run.build_run_id == "br-1"
        assert git_export_run.branch_name == "feature/auth"

    def test_git_export_run_default_status(self, git_export_run):
        assert git_export_run.status == ExportStatus.DRAFT

    @pytest.mark.parametrize("status", list(ExportStatus))
    def test_all_export_statuses(self, status):
        """Section 29.10 — all export statuses."""
        ger = GitExportRun(
            git_export_run_id=f"ger-{status.value}",
            product_id="p-1",
            status=status,
            created_by="u",
            updated_by="u",
        )
        assert ger.status == status


class TestRepositoryTarget:
    """Section 29.5 — Repository Target tests."""

    def test_repository_target_fields(self, repository_target):
        assert repository_target.repository_target_id is not None
        assert repository_target.provider == "github"
        assert repository_target.default_branch == "main"


class TestExportManifest:
    """Section 29.6 — Export Manifest tests."""

    def test_export_manifest_fields(self, export_manifest):
        assert export_manifest.export_manifest_id is not None
        assert len(export_manifest.included_artifact_ids) > 0
        assert len(export_manifest.file_entries) > 0
        assert len(export_manifest.lineage_entries) > 0

    def test_file_entry_structure(self, export_manifest):
        fe = export_manifest.file_entries[0]
        assert fe.target_file_path is not None
        assert fe.source_artifact_id is not None
        assert fe.artifact_type is not None

    def test_lineage_entry_structure(self, export_manifest):
        """Section 29.6 — lineage_entry fields."""
        le = export_manifest.lineage_entries[0]
        assert le.file_path is not None
        assert le.task_id is not None
        assert len(le.requirement_ids) > 0
        assert len(le.test_ids) > 0
        assert le.code_artifact_id is not None
        assert le.generation_run_id is not None


class TestCommitBundle:
    """Section 29.7 — Commit Bundle tests."""

    def test_commit_bundle_fields(self, commit_bundle):
        assert commit_bundle.commit_bundle_id is not None
        assert commit_bundle.branch_name is not None
        assert commit_bundle.commit_message is not None
        assert len(commit_bundle.changed_files) > 0


class TestReleasePackage:
    """Section 29.8 — Release Package tests."""

    def test_release_package_fields(self, release_package):
        assert release_package.release_package_id is not None
        assert release_package.build_run_id is not None
        assert release_package.git_export_run_id is not None
        assert release_package.handoff_notes is not None
