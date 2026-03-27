"""Type enums per specification."""
from enum import Enum


class FlowType(str, Enum):
    """Section 14.2 — Supported flow types."""
    PRIMARY = "primary"
    ALTERNATIVE = "alternative"
    EXCEPTION = "exception"


class RequirementType(str, Enum):
    """Sections 16.2-16.3 — Requirement categories."""
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    DATA = "data"
    INTEGRATION = "integration"
    AI = "ai"
    OBSERVABILITY = "observability"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class ArchitectureArtifactType(str, Enum):
    """Section 17.1 — Architecture artifact types."""
    INFRASTRUCTURE = "infrastructure_architecture"
    DATA = "data_architecture"
    SERVICE = "service_architecture"
    FRONTEND = "frontend_architecture"
    AI = "ai_architecture"
    ER_DIAGRAM = "er_diagram"
    INTEGRATION = "integration_architecture"
    DEPLOYMENT = "deployment_architecture"


class TestCategory(str, Enum):
    """Section 20.2 — Test case categories."""
    UNIT = "unit"
    INTEGRATION = "integration"
    END_TO_END = "end_to_end"
    INFRASTRUCTURE = "infrastructure"
    DATA = "data"
    SERVICE = "service"
    LLM_PROMPT = "llm_prompt"
    ACCEPTANCE_BEHAVIOR = "acceptance_behavior"


class GenerationMode(str, Enum):
    """Section 24.2 — Generation modes."""
    DETERMINISTIC = "deterministic"
    EXPLORATORY = "exploratory"
    REPAIR = "repair"
    PATCH = "patch"
    REGENERATE = "regenerate"


class ChangeType(str, Enum):
    """Section 27.1 — Supported change types."""
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    SPLIT = "split"
    MERGE = "merge"
    MOVE = "move"


class TraceLinkType(str, Enum):
    """Section 9.1 — Trace link types."""
    PARENT_OF = "parent_of"
    DERIVED_FROM = "derived_from"
    IMPLEMENTS = "implements"
    VERIFIES = "verifies"
    DEPENDS_ON = "depends_on"
    USES_CONTEXT_FROM = "uses_context_from"
    EXPORTS = "exports"
    INCLUDED_IN = "included_in"
    AFFECTED_BY_CHANGE = "affected_by_change"
    INVALIDATES = "invalidates"


class TelegramScreen(str, Enum):
    """Section 30 — Minimum Telegram UX screens."""
    PRODUCT_LIST = "product_list"
    PRODUCT_HOME = "product_home"
    PRODUCT_GENERAL_INFO = "product_general_info"
    FEATURE_LIST = "feature_list"
    FEATURE_HOME = "feature_home"
    ACTOR_LIST = "actor_list"
    STORY_LIST = "story_list"
    FLOW_VIEW = "flow_view"
    USE_CASE_LIST = "use_case_list"
    REQUIREMENT_LIST = "requirement_list"
    ARCHITECTURE_CENTER = "architecture_center"
    TASK_CENTER = "task_center"
    TEST_CENTER = "test_center"
    CHANGE_CENTER = "change_center"
    BUILD_CENTER = "build_center"
    GIT_EXPORT_CENTER = "git_export_center"
