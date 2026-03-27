"""Validation service — enforces domain invariants from the specification."""
from typing import Optional

from src.enums.statuses import BaseStatus, ExportStatus, ExecutionStatus
from src.enums.types import FlowType
from src.models.business import (
    Product, Feature, Actor, FeatureActorLink, UserStory, UserFlow, UseCase, Requirement,
)
from src.models.engineering import (
    ArchitectureArtifact, Task, Subtask, TestDesign, TestCase,
    DependencyOutput, CodeArtifact, ArtifactRegistryEntry,
)
from src.models.execution import (
    TraceLink, ContextPackage, GenerationRun,
    ChangeRequest, ChangeSetItem, ChangeImpactMap,
    BuildArtifact, BuildRun,
)
from src.models.delivery import (
    GitExportRun, RepositoryTarget, ExportManifest, CommitBundle,
    ReleasePackage, FileEntry, LineageEntry,
)


class ValidationError(Exception):
    pass


class DomainValidator:
    """Validates domain rules and invariants from the spec."""

    # --- Section 10: Product invariant ---
    @staticmethod
    def validate_product_exists_before_children(
        product: Optional[Product],
    ) -> None:
        """Product must exist before any child entity is created (section 10)."""
        if product is None:
            raise ValidationError("Product must exist before any child entity is created.")

    # --- Section 11: Feature invariants ---
    @staticmethod
    def validate_feature_belongs_to_product(feature: Feature, product: Product) -> None:
        """Feature belongs to exactly one Product (section 11)."""
        if feature.product_id != product.product_id:
            raise ValidationError("Feature must belong to the specified Product.")

    @staticmethod
    def validate_feature_deletion(
        feature: Feature, has_downstream_refs: bool
    ) -> None:
        """Physical deletion of Feature is allowed only if unreferenced draft (section 11)."""
        if has_downstream_refs:
            raise ValidationError(
                "Cannot physically delete Feature that has downstream references."
            )
        if feature.status != BaseStatus.DRAFT:
            raise ValidationError(
                "Cannot physically delete Feature that is not in draft status."
            )

    # --- Section 12: Actor invariants ---
    @staticmethod
    def validate_actor_belongs_to_product(actor: Actor, product: Product) -> None:
        if actor.product_id != product.product_id:
            raise ValidationError("Actor must belong to the specified Product.")

    @staticmethod
    def validate_story_actor_linked_to_feature(
        story: UserStory,
        feature_actor_links: list[FeatureActorLink],
    ) -> None:
        """User Story Actor must be linked to the Story's Feature (section 12.4)."""
        if story.actor_id is None:
            raise ValidationError("User Story must reference exactly one Actor.")
        linked = any(
            link.feature_id == story.feature_id and link.actor_id == story.actor_id
            for link in feature_actor_links
        )
        if not linked:
            raise ValidationError(
                "Story's Actor must be linked to the Story's Feature via FeatureActorLink."
            )

    # --- Section 13: Story invariants ---
    @staticmethod
    def validate_story_has_actor(story: UserStory) -> None:
        """Story references exactly one Actor (section 13)."""
        if story.actor_id is None:
            raise ValidationError("Story must reference exactly one Actor.")

    @staticmethod
    def validate_story_cannot_move_downstream_without_actor_and_approval(
        story: UserStory,
    ) -> None:
        """Story cannot move downstream until Actor is assigned and Story is approved (section 13)."""
        if story.actor_id is None:
            raise ValidationError("Story cannot move downstream without an Actor.")
        if story.status != BaseStatus.APPROVED:
            raise ValidationError("Story cannot move downstream without approval.")

    # --- Section 14: Flow invariants ---
    @staticmethod
    def validate_flow_belongs_to_story(flow: UserFlow, story: UserStory) -> None:
        if flow.story_id != story.story_id:
            raise ValidationError("Flow must belong to the specified Story.")

    @staticmethod
    def validate_primary_flow_uniqueness(
        story: UserStory, flows: list[UserFlow]
    ) -> None:
        """One Story must support exactly one primary Flow in the standard path (section 14.4)."""
        primary_flows = [f for f in flows if f.flow_type == FlowType.PRIMARY and f.story_id == story.story_id]
        if len(primary_flows) > 1:
            raise ValidationError("A Story must have at most one primary Flow.")

    @staticmethod
    def validate_flow_approved_before_use_case_generation(flow: UserFlow) -> None:
        """Flow must be approved before Use Cases are generated (section 14.4)."""
        if flow.status != BaseStatus.APPROVED:
            raise ValidationError("Flow must be approved before Use Case generation.")

    @staticmethod
    def validate_flow_is_mermaid(flow: UserFlow) -> None:
        """All User Flows must be stored in Mermaid (section 14)."""
        if flow.mermaid_source is None or flow.mermaid_source.strip() == "":
            raise ValidationError("User Flow must contain Mermaid source.")

    # --- Section 15: Use Case invariants ---
    @staticmethod
    def validate_use_case_belongs_to_flow(use_case: UseCase, flow: UserFlow) -> None:
        if use_case.flow_id != flow.flow_id:
            raise ValidationError("Use Case must belong to the specified Flow.")

    @staticmethod
    def validate_use_case_approved_before_requirement(use_case: UseCase) -> None:
        """Requirement generation must not proceed from a non-approved Use Case (section 15.3)."""
        if use_case.status != BaseStatus.APPROVED:
            raise ValidationError(
                "Use Case must be approved before Requirement generation."
            )

    # --- Section 16: Requirement invariants ---
    @staticmethod
    def validate_requirement_has_upstream_source(requirement: Requirement) -> None:
        """Requirement must have at least one traceable upstream source (section 16.5)."""
        if requirement.primary_use_case_id is None and requirement.source_id is None:
            raise ValidationError(
                "Requirement must have at least one upstream traceable source."
            )

    @staticmethod
    def validate_requirement_type_set(requirement: Requirement) -> None:
        """requirement_type must explicitly classify the requirement (section 16.5)."""
        if requirement.requirement_type is None:
            raise ValidationError("Requirement must have an explicit type.")

    # --- Section 17: Architecture invariants ---
    @staticmethod
    def validate_architecture_only_from_approved(
        requirements: list[Requirement],
    ) -> None:
        """Architecture generation begins only after Requirements are approved (section 17)."""
        non_approved = [r for r in requirements if r.status != BaseStatus.APPROVED]
        if non_approved:
            raise ValidationError(
                "Architecture generation requires all source Requirements to be approved."
            )

    # --- Section 19: Test Design invariants ---
    @staticmethod
    def validate_test_design_linked_to_requirement(td: TestDesign) -> None:
        """Every approved Requirement must support at least one linked Test Design (section 19.3)."""
        if not td.requirement_id:
            raise ValidationError("TestDesign must be linked to a Requirement.")

    # --- Section 20: Test Case invariants ---
    @staticmethod
    def validate_test_case_traceable(tc: TestCase) -> None:
        """Every Test Case must be traceable to at least one Requirement or Test Design (section 9.2)."""
        if tc.requirement_id is None and tc.test_design_id is None:
            raise ValidationError(
                "Test Case must be traceable to at least one Requirement or Test Design."
            )

    # --- Section 21: Task invariants ---
    @staticmethod
    def validate_task_has_requirements(task: Task) -> None:
        """Task must be traceable to one or more Requirements (section 9.2)."""
        if not task.requirement_ids:
            raise ValidationError("Task must be linked to at least one Requirement.")

    @staticmethod
    def validate_task_has_linked_tests_for_code_gen(task: Task) -> None:
        """Code generation may proceed only when Task has linked Test Cases (section 20.4)."""
        if not task.linked_test_ids:
            raise ValidationError(
                "Task must have linked Test Cases before code generation."
            )

    @staticmethod
    def validate_task_has_context_package(task: Task) -> None:
        """Task must have a Context Package for generation (section 23)."""
        if task.context_package_ref is None:
            raise ValidationError("Task must have a Context Package reference.")

    # --- Section 22: Dependency Output invariants ---
    @staticmethod
    def validate_dependency_output_approved_for_downstream(dep: DependencyOutput) -> None:
        """Downstream Task may consume only approved Dependency Outputs (section 22.3)."""
        if dep.status != BaseStatus.APPROVED:
            raise ValidationError("Dependency Output must be approved for downstream use.")

    # --- Section 23: Context Package invariants ---
    @staticmethod
    def validate_context_package_declarations(cp: ContextPackage) -> None:
        """Every Context Package must declare target artifact type (section 23.4)."""
        if not cp.target_artifact_type:
            raise ValidationError("Context Package must declare target_artifact_type.")

    @staticmethod
    def validate_context_package_has_hash(cp: ContextPackage) -> None:
        """Every Context Package must have a reproducible context_hash (section 23.5)."""
        if not cp.context_hash:
            raise ValidationError("Context Package must have a context_hash.")

    @staticmethod
    def validate_context_package_no_full_product_context(cp: ContextPackage) -> None:
        """Full product context is prohibited unless justified (section 23.4)."""
        if cp.scope_type == "product" and not cp.broader_context_justification:
            raise ValidationError(
                "Full product context requires broader_context_justification."
            )

    # --- Section 25: Code generation invariants ---
    @staticmethod
    def validate_code_generation_prerequisites(
        task: Task,
        context_package: Optional[ContextPackage],
        upstream_approved: bool,
    ) -> None:
        """Section 25 — code generation invariants."""
        if context_package is None:
            raise ValidationError("No code generation without Context Package.")
        if not upstream_approved:
            raise ValidationError(
                "No code generation from non-approved upstream sources."
            )
        if not task.requirement_ids:
            raise ValidationError(
                "Code generation requires linked Requirements."
            )
        if not task.linked_test_ids:
            raise ValidationError(
                "Code generation requires linked Test Cases."
            )

    # --- Section 26: Artifact Registry invariants ---
    @staticmethod
    def validate_code_artifact_registered(
        code_artifact: CodeArtifact,
        registry_entries: list[ArtifactRegistryEntry],
    ) -> None:
        """Every generated file must correspond to a Code Artifact and an Artifact Registry Entry (section 26.3)."""
        matching = [
            e for e in registry_entries
            if e.code_artifact_id == code_artifact.code_artifact_id
        ]
        if not matching:
            raise ValidationError(
                "Code Artifact must have at least one Artifact Registry Entry."
            )

    # --- Section 4: Deletion rules ---
    @staticmethod
    def validate_traceable_entity_not_physically_deleted(
        entity_status: BaseStatus, has_downstream: bool
    ) -> None:
        """Traceable entities must not be physically deleted once referenced (section 4)."""
        if has_downstream:
            raise ValidationError(
                "Traceable entity cannot be physically deleted when referenced downstream."
            )

    @staticmethod
    def validate_physical_deletion_allowed(
        entity_status: BaseStatus, has_downstream: bool
    ) -> None:
        """Physical deletion allowed only for unreferenced draft entities (section 4)."""
        if has_downstream:
            raise ValidationError("Cannot delete: entity has downstream references.")
        if entity_status != BaseStatus.DRAFT:
            raise ValidationError("Cannot delete: entity is not in draft status.")


class VersioningService:
    """Versioning and approval rules per section 7."""

    @staticmethod
    def validate_version_increment_required(
        old_content: str,
        new_content: str,
        old_version: int,
        new_version: int,
    ) -> None:
        """Version must increment when content changes (section 7.1)."""
        if old_content != new_content and new_version <= old_version:
            raise ValidationError(
                "Version must increment when content changes."
            )

    @staticmethod
    def validate_approval_invalidated_on_change(
        entity: object,
        content_changed: bool,
    ) -> None:
        """If content changes, prior approval must be invalidated (section 7.2)."""
        approved_version = getattr(entity, "approved_version", None)
        current_version = getattr(entity, "version", None)
        if content_changed and approved_version is not None:
            if approved_version == current_version:
                raise ValidationError(
                    "Approval must be invalidated when content changes — "
                    "new version requires re-approval."
                )

    @staticmethod
    def approve_entity(entity, approver: str) -> None:
        """Approve entity with version binding (section 7.2)."""
        from datetime import datetime
        entity.status = BaseStatus.APPROVED
        entity.approved_at = datetime.utcnow()
        entity.approved_by = approver
        entity.approved_version = entity.version

    @staticmethod
    def invalidate_approval(entity) -> None:
        """Invalidate approval after content/structure change."""
        entity.approved_at = None
        entity.approved_by = None
        entity.approved_version = None
        if entity.status == BaseStatus.APPROVED:
            entity.status = BaseStatus.CHANGED


class BuildValidator:
    """Build Center validation per section 28."""

    @staticmethod
    def validate_build_prerequisites(
        artifact_refs: list[str],
        approved_artifact_ids: set[str],
        tasks_with_tests: set[str],
        tasks_with_approvals: set[str],
    ) -> list[str]:
        """Section 28.1 — validate build prerequisites."""
        errors = []
        unapproved = set(artifact_refs) - approved_artifact_ids
        if unapproved:
            errors.append(f"Unapproved artifacts: {unapproved}")
        missing_tests = set(artifact_refs) - tasks_with_tests
        if missing_tests:
            errors.append(f"Artifacts missing linked tests: {missing_tests}")
        missing_approvals = set(artifact_refs) - tasks_with_approvals
        if missing_approvals:
            errors.append(f"Artifacts missing source approvals: {missing_approvals}")
        return errors


class ExportValidator:
    """Git export validation per section 29."""

    @staticmethod
    def validate_export_preconditions(
        product_exists: bool,
        code_artifacts_approved: bool,
        tasks_approved_or_completed: bool,
        test_cases_exist: bool,
        build_run_exists: bool,
        export_manifest_exists: bool,
        user_approved: bool,
    ) -> list[str]:
        """Section 29.2 — export preconditions."""
        errors = []
        if not product_exists:
            errors.append("Target Product must exist.")
        if not code_artifacts_approved:
            errors.append("Code Artifacts must be approved.")
        if not tasks_approved_or_completed:
            errors.append("Tasks must be approved or completed.")
        if not test_cases_exist:
            errors.append("Linked Test Cases must exist.")
        if not build_run_exists:
            errors.append("Build Run must exist where required.")
        if not export_manifest_exists:
            errors.append("Export Manifest must be constructed.")
        if not user_approved:
            errors.append("User must explicitly approve export.")
        return errors

    @staticmethod
    def validate_export_manifest_lineage(manifest: ExportManifest) -> list[str]:
        """Section 29.6 — every file_entry must have a lineage_entry."""
        errors = []
        lineage_paths = {le.file_path for le in manifest.lineage_entries}
        for fe in manifest.file_entries:
            if fe.target_file_path not in lineage_paths:
                errors.append(
                    f"File entry '{fe.target_file_path}' has no lineage entry."
                )
        return errors

    @staticmethod
    def validate_no_export_from_non_approved(
        source_statuses: list[BaseStatus],
    ) -> None:
        """No export to Git from non-approved source artifacts (section 5.4)."""
        non_approved = [s for s in source_statuses if s != BaseStatus.APPROVED]
        if non_approved:
            raise ValidationError(
                "Cannot export from non-approved source artifacts."
            )


class SpecHealthChecker:
    """Specification health checks per section 32."""

    def __init__(
        self,
        features: list[Feature],
        stories: list[UserStory],
        flows: list[UserFlow],
        use_cases: list[UseCase],
        requirements: list[Requirement],
        test_designs: list[TestDesign],
        tasks: list[Task],
    ):
        self.features = features
        self.stories = stories
        self.flows = flows
        self.use_cases = use_cases
        self.requirements = requirements
        self.test_designs = test_designs
        self.tasks = tasks

    def features_without_approved_stories(self) -> list[str]:
        approved_story_feature_ids = {
            s.feature_id for s in self.stories if s.status == BaseStatus.APPROVED
        }
        return [
            f.feature_id for f in self.features
            if f.feature_id not in approved_story_feature_ids
        ]

    def stories_without_actors(self) -> list[str]:
        return [s.story_id for s in self.stories if s.actor_id is None]

    def stories_without_primary_flow(self) -> list[str]:
        stories_with_primary = {
            f.story_id for f in self.flows if f.flow_type == FlowType.PRIMARY
        }
        return [
            s.story_id for s in self.stories
            if s.story_id not in stories_with_primary
        ]

    def approved_flows_without_use_cases(self) -> list[str]:
        flows_with_uc = {uc.flow_id for uc in self.use_cases}
        return [
            f.flow_id for f in self.flows
            if f.status == BaseStatus.APPROVED and f.flow_id not in flows_with_uc
        ]

    def approved_use_cases_without_requirements(self) -> list[str]:
        ucs_with_req = {
            r.primary_use_case_id for r in self.requirements
            if r.primary_use_case_id is not None
        }
        return [
            uc.use_case_id for uc in self.use_cases
            if uc.status == BaseStatus.APPROVED and uc.use_case_id not in ucs_with_req
        ]

    def approved_requirements_without_test_designs(self) -> list[str]:
        reqs_with_td = {td.requirement_id for td in self.test_designs}
        return [
            r.requirement_id for r in self.requirements
            if r.status == BaseStatus.APPROVED and r.requirement_id not in reqs_with_td
        ]

    def tasks_without_linked_tests(self) -> list[str]:
        return [t.task_id for t in self.tasks if not t.linked_test_ids]

    def tasks_without_context_packages(self) -> list[str]:
        return [t.task_id for t in self.tasks if t.context_package_ref is None]
