"""
Enumerations for the domain model.

## Traceability
Feature: F001-F009 — All features (sections 5, 14, 16)
"""
import enum


class EntityStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    CHANGED = "changed"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class FlowTypeEnum(str, enum.Enum):
    PRIMARY = "primary"
    ALTERNATIVE = "alternative"
    EXCEPTION = "exception"


class RequirementTypeEnum(str, enum.Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    DATA = "data"
    INTEGRATION = "integration"
    AI = "ai"
    OBSERVABILITY = "observability"
    SECURITY = "security"
    COMPLIANCE = "compliance"
