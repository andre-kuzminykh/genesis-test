"""Execution truth entities per specification sections 8.3, 23-24, 27-28."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from src.models.base import BaseEntity, ApprovableEntity
from src.enums.statuses import BaseStatus, ExecutionStatus
from src.enums.types import GenerationMode, ChangeType, TraceLinkType


class TraceLink(BaseModel):
    """Section 9.1 — Trace Link entity."""
    trace_link_id: str
    source_entity_type: str
    source_entity_id: str
    target_entity_type: str
    target_entity_id: str
    link_type: TraceLinkType
    status: BaseStatus = BaseStatus.DRAFT
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = ""


class ContextPackage(ApprovableEntity):
    """Section 23 — Context Package entity."""
    context_package_id: str
    product_id: str
    feature_id: Optional[str] = None
    scope_type: Optional[str] = None
    scope_entity_id: Optional[str] = None
    target_artifact_type: str
    target_artifact_id: Optional[str] = None
    included_entity_refs: list[str] = Field(default_factory=list)
    excluded_entity_refs: list[str] = Field(default_factory=list)
    dependency_output_refs: list[str] = Field(default_factory=list)
    linked_code_artifact_refs: list[str] = Field(default_factory=list)
    broader_context_justification: Optional[str] = None
    generation_mode: GenerationMode = GenerationMode.DETERMINISTIC
    context_hash: Optional[str] = None


class GenerationRun(BaseModel):
    """Section 24 — Generation Run entity."""
    generation_run_id: str
    target_entity_type: str
    target_entity_id: str
    context_package_id: str
    generation_mode: GenerationMode = GenerationMode.DETERMINISTIC
    model_ref: Optional[str] = None
    prompt_template_ref: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.QUEUED
    input_snapshot_ref: Optional[str] = None
    output_snapshot_ref: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    initiated_by: str = ""
    version: int = 1


class ChangeRequest(ApprovableEntity):
    """Section 27.2 — Change Request entity."""
    change_request_id: str
    product_id: str
    title: str
    description: Optional[str] = None
    change_reason: Optional[str] = None
    requested_by: str = ""


class ChangeSetItem(ApprovableEntity):
    """Section 27.3 — Change Set Item entity."""
    change_set_item_id: str
    change_request_id: str
    target_entity_type: str
    target_entity_id: str
    change_type: ChangeType
    proposed_operation: Optional[str] = None


class ChangeImpactMap(ApprovableEntity):
    """Section 27.4 — Change Impact Map entity."""
    change_impact_map_id: str
    change_request_id: str
    affected_entity_refs: list[str] = Field(default_factory=list)
    invalidated_entity_refs: list[str] = Field(default_factory=list)
    regeneration_candidates: list[str] = Field(default_factory=list)


class BuildArtifact(ApprovableEntity):
    """Section 28.2 — Build Artifact entity."""
    build_artifact_id: str
    product_id: str
    artifact_refs: list[str] = Field(default_factory=list)
    manifest_ref: Optional[str] = None


class BuildRun(BaseModel):
    """Section 28.3 — Build Run entity."""
    build_run_id: str
    product_id: str
    build_artifact_id: str
    status: ExecutionStatus = ExecutionStatus.QUEUED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    initiated_by: str = ""
    version: int = 1
