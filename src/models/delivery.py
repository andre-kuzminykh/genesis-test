"""Delivery truth entities per specification sections 8.4, 29."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from src.models.base import ApprovableEntity
from src.enums.statuses import ExportStatus


class FileEntry(BaseModel):
    """Export manifest file entry (section 29.6)."""
    target_file_path: str
    source_artifact_id: str
    artifact_type: str
    overwrite_mode: str = "create"
    checksum: Optional[str] = None


class LineageEntry(BaseModel):
    """Export manifest lineage entry (section 29.6)."""
    file_path: str
    task_id: str
    requirement_ids: list[str] = Field(default_factory=list)
    test_ids: list[str] = Field(default_factory=list)
    architecture_ids: list[str] = Field(default_factory=list)
    dependency_output_refs: list[str] = Field(default_factory=list)
    code_artifact_id: Optional[str] = None
    generation_run_id: Optional[str] = None


class GitExportRun(ApprovableEntity):
    """Section 29.4 — Git Export Run entity."""
    git_export_run_id: str
    product_id: str
    build_run_id: Optional[str] = None
    repository_target_id: Optional[str] = None
    export_manifest_id: Optional[str] = None
    branch_name: Optional[str] = None
    commit_message: Optional[str] = None
    export_scope: Optional[str] = None
    status: ExportStatus = ExportStatus.DRAFT  # type: ignore[assignment]


class RepositoryTarget(ApprovableEntity):
    """Section 29.5 — Repository Target entity."""
    repository_target_id: str
    product_id: str
    provider: Optional[str] = None
    repository_name: Optional[str] = None
    default_branch: str = "main"
    target_path_strategy: Optional[str] = None


class ExportManifest(ApprovableEntity):
    """Section 29.6 — Export Manifest entity."""
    export_manifest_id: str
    product_id: str
    build_run_id: Optional[str] = None
    included_artifact_ids: list[str] = Field(default_factory=list)
    file_entries: list[FileEntry] = Field(default_factory=list)
    lineage_entries: list[LineageEntry] = Field(default_factory=list)


class CommitBundle(ApprovableEntity):
    """Section 29.7 — Commit Bundle entity."""
    commit_bundle_id: str
    repository_target_id: str
    branch_name: Optional[str] = None
    commit_message: Optional[str] = None
    export_manifest_id: Optional[str] = None
    changed_files: list[str] = Field(default_factory=list)
    build_run_id: Optional[str] = None
    generation_run_ids: list[str] = Field(default_factory=list)


class ReleasePackage(ApprovableEntity):
    """Section 29.8 — Release Package entity."""
    release_package_id: str
    product_id: str
    build_run_id: Optional[str] = None
    git_export_run_id: Optional[str] = None
    included_refs: list[str] = Field(default_factory=list)
    handoff_notes: Optional[str] = None
