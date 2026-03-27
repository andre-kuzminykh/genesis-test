"""Status enums per specification sections 5.1-5.5."""
from enum import Enum


class BaseStatus(str, Enum):
    """Section 5.1 — Base status vocabulary."""
    DRAFT = "draft"
    GENERATED = "generated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    CHANGED = "changed"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    """Section 5.2 — Execution status vocabulary."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class DeliveryStatus(str, Enum):
    """Section 5.3 — Delivery status vocabulary."""
    PREPARED = "prepared"
    APPROVED_FOR_EXPORT = "approved_for_export"
    EXPORTED = "exported"
    SUPERSEDED = "superseded"


class ExportStatus(str, Enum):
    """Section 29.10 — Export status model."""
    DRAFT = "draft"
    PREPARED = "prepared"
    APPROVED_FOR_EXPORT = "approved_for_export"
    EXPORTED = "exported"
    FAILED = "failed"
    SUPERSEDED = "superseded"
