"""Shared test fixtures for the Telegram Product Engineer Bot test suite."""
import pytest
from datetime import datetime

from src.enums.statuses import BaseStatus
from src.enums.types import (
    FlowType, RequirementType, ArchitectureArtifactType,
    TestCategory, GenerationMode, ChangeType, TraceLinkType,
)
from src.models.business import (
    Product, Feature, Actor, FeatureActorLink, UserStory, UserFlow, UseCase, Requirement,
)
from src.models.engineering import (
    ArchitectureArtifact, Task, Subtask, TestDesign, TestCase,
    DependencyOutput, CodeArtifact, ArtifactRegistryEntry, TestSuite,
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

SYSTEM_USER = "system"
TEST_USER = "tester"


# ── Product ──────────────────────────────────────────────────────────────────

@pytest.fixture
def product() -> Product:
    return Product(
        product_id="prod-1",
        name="Test Product",
        short_description="A test product",
        goal="Validate spec compliance",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def approved_product(product: Product) -> Product:
    product.status = BaseStatus.APPROVED
    product.approved_at = datetime.utcnow()
    product.approved_by = TEST_USER
    product.approved_version = product.version
    return product


# ── Feature ──────────────────────────────────────────────────────────────────

@pytest.fixture
def feature(product: Product) -> Feature:
    return Feature(
        feature_id="feat-1",
        product_id=product.product_id,
        name="Auth Feature",
        description="User authentication",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def approved_feature(feature: Feature) -> Feature:
    feature.status = BaseStatus.APPROVED
    feature.approved_at = datetime.utcnow()
    feature.approved_by = TEST_USER
    feature.approved_version = feature.version
    return feature


# ── Actor ────────────────────────────────────────────────────────────────────

@pytest.fixture
def actor(product: Product) -> Actor:
    return Actor(
        actor_id="actor-1",
        product_id=product.product_id,
        name="End User",
        role_type="primary",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def feature_actor_link(product: Product, feature: Feature, actor: Actor) -> FeatureActorLink:
    return FeatureActorLink(
        feature_actor_link_id="fal-1",
        product_id=product.product_id,
        feature_id=feature.feature_id,
        actor_id=actor.actor_id,
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


# ── User Story ───────────────────────────────────────────────────────────────

@pytest.fixture
def story(product: Product, feature: Feature, actor: Actor) -> UserStory:
    return UserStory(
        story_id="story-1",
        product_id=product.product_id,
        feature_id=feature.feature_id,
        actor_id=actor.actor_id,
        title="Login story",
        want_text="log in with email",
        benefit_text="access my account",
        full_text="As End User, I want to log in with email, so that I can access my account.",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def approved_story(story: UserStory) -> UserStory:
    story.status = BaseStatus.APPROVED
    story.approved_at = datetime.utcnow()
    story.approved_by = TEST_USER
    story.approved_version = story.version
    return story


# ── User Flow ────────────────────────────────────────────────────────────────

@pytest.fixture
def flow(product: Product, feature: Feature, story: UserStory) -> UserFlow:
    return UserFlow(
        flow_id="flow-1",
        product_id=product.product_id,
        feature_id=feature.feature_id,
        story_id=story.story_id,
        title="Primary login flow",
        flow_type=FlowType.PRIMARY,
        mermaid_source="graph TD\n  A[Start] --> B[Login]\n  B --> C[Dashboard]",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def approved_flow(flow: UserFlow) -> UserFlow:
    flow.status = BaseStatus.APPROVED
    flow.approved_at = datetime.utcnow()
    flow.approved_by = TEST_USER
    flow.approved_version = flow.version
    return flow


# ── Use Case ─────────────────────────────────────────────────────────────────

@pytest.fixture
def use_case(product: Product, feature: Feature, story: UserStory, flow: UserFlow) -> UseCase:
    return UseCase(
        use_case_id="uc-1",
        product_id=product.product_id,
        feature_id=feature.feature_id,
        story_id=story.story_id,
        flow_id=flow.flow_id,
        title="Successful login",
        goal="Authenticate user with valid credentials",
        preconditions="User has registered account",
        given_text="User is on login page",
        when_text="User enters valid credentials and clicks login",
        then_text="User is redirected to dashboard",
        main_success_scenario="1. User enters email\n2. User enters password\n3. System validates\n4. Redirect to dashboard",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def approved_use_case(use_case: UseCase) -> UseCase:
    use_case.status = BaseStatus.APPROVED
    use_case.approved_at = datetime.utcnow()
    use_case.approved_by = TEST_USER
    use_case.approved_version = use_case.version
    return use_case


# ── Requirement ──────────────────────────────────────────────────────────────

@pytest.fixture
def requirement(product: Product, feature: Feature, use_case: UseCase) -> Requirement:
    return Requirement(
        requirement_id="req-1",
        product_id=product.product_id,
        feature_id=feature.feature_id,
        primary_use_case_id=use_case.use_case_id,
        title="Email login must validate format",
        text="The system shall validate email format before authentication attempt.",
        requirement_type=RequirementType.FUNCTIONAL,
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def approved_requirement(requirement: Requirement) -> Requirement:
    requirement.status = BaseStatus.APPROVED
    requirement.approved_at = datetime.utcnow()
    requirement.approved_by = TEST_USER
    requirement.approved_version = requirement.version
    return requirement


# ── Architecture ─────────────────────────────────────────────────────────────

@pytest.fixture
def architecture(product: Product, feature: Feature) -> ArchitectureArtifact:
    return ArchitectureArtifact(
        architecture_id="arch-1",
        product_id=product.product_id,
        feature_id=feature.feature_id,
        artifact_type=ArchitectureArtifactType.SERVICE,
        title="Auth service architecture",
        mermaid_source="graph LR\n  Client --> AuthService --> DB",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def approved_architecture(architecture: ArchitectureArtifact) -> ArchitectureArtifact:
    architecture.status = BaseStatus.APPROVED
    architecture.approved_at = datetime.utcnow()
    architecture.approved_by = TEST_USER
    architecture.approved_version = architecture.version
    return architecture


# ── Test Design ──────────────────────────────────────────────────────────────

@pytest.fixture
def test_design(product: Product, requirement: Requirement) -> TestDesign:
    return TestDesign(
        test_design_id="td-1",
        product_id=product.product_id,
        requirement_id=requirement.requirement_id,
        title="Verify email validation",
        test_intent="Ensure invalid email formats are rejected",
        test_type="functional",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


# ── Test Case ────────────────────────────────────────────────────────────────

@pytest.fixture
def test_case(product: Product, requirement: Requirement, test_design: TestDesign) -> TestCase:
    return TestCase(
        test_id="tc-1",
        product_id=product.product_id,
        requirement_id=requirement.requirement_id,
        test_design_id=test_design.test_design_id,
        title="Test invalid email rejected",
        category=TestCategory.UNIT,
        steps="1. Enter invalid email\n2. Submit form",
        expected_result="Validation error displayed",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


# ── Task ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def task(product: Product, feature: Feature, requirement: Requirement, test_case: TestCase) -> Task:
    return Task(
        task_id="task-1",
        product_id=product.product_id,
        feature_id=feature.feature_id,
        requirement_ids=[requirement.requirement_id],
        linked_test_ids=[test_case.test_id],
        title="Implement email validation",
        description="Add email format validation to login form",
        context_package_ref="cp-1",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def subtask(task: Task) -> Subtask:
    return Subtask(
        subtask_id="sub-1",
        task_id=task.task_id,
        title="Add regex validation",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


# ── Dependency Output ────────────────────────────────────────────────────────

@pytest.fixture
def dependency_output(task: Task) -> DependencyOutput:
    return DependencyOutput(
        dependency_output_id="dep-1",
        task_id=task.task_id,
        output_type="interface_contract",
        title="Auth service interface",
        status=BaseStatus.APPROVED,
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


# ── Code Artifact ────────────────────────────────────────────────────────────

@pytest.fixture
def code_artifact(task: Task) -> CodeArtifact:
    return CodeArtifact(
        code_artifact_id="ca-1",
        task_id=task.task_id,
        artifact_type="service",
        logical_name="auth_service.py",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def registry_entry(code_artifact: CodeArtifact) -> ArtifactRegistryEntry:
    return ArtifactRegistryEntry(
        artifact_registry_entry_id="are-1",
        code_artifact_id=code_artifact.code_artifact_id,
        file_path="src/services/auth_service.py",
        content_hash="abc123",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


# ── Context Package ──────────────────────────────────────────────────────────

@pytest.fixture
def context_package(product: Product, feature: Feature, task: Task) -> ContextPackage:
    return ContextPackage(
        context_package_id="cp-1",
        product_id=product.product_id,
        feature_id=feature.feature_id,
        scope_type="task",
        scope_entity_id=task.task_id,
        target_artifact_type="code",
        target_artifact_id="ca-1",
        included_entity_refs=["req-1", "tc-1", "arch-1"],
        context_hash="hash-abc123",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


# ── Generation Run ───────────────────────────────────────────────────────────

@pytest.fixture
def generation_run(context_package: ContextPackage) -> GenerationRun:
    return GenerationRun(
        generation_run_id="gr-1",
        target_entity_type="code_artifact",
        target_entity_id="ca-1",
        context_package_id=context_package.context_package_id,
        generation_mode=GenerationMode.DETERMINISTIC,
        initiated_by=TEST_USER,
    )


# ── Trace Link ───────────────────────────────────────────────────────────────

@pytest.fixture
def trace_link() -> TraceLink:
    return TraceLink(
        trace_link_id="tl-1",
        source_entity_type="requirement",
        source_entity_id="req-1",
        target_entity_type="task",
        target_entity_id="task-1",
        link_type=TraceLinkType.IMPLEMENTS,
        created_by=SYSTEM_USER,
    )


# ── Change Request ───────────────────────────────────────────────────────────

@pytest.fixture
def change_request(product: Product) -> ChangeRequest:
    return ChangeRequest(
        change_request_id="cr-1",
        product_id=product.product_id,
        title="Add OAuth login",
        description="Add OAuth2 support for Google login",
        change_reason="Business requirement",
        requested_by=TEST_USER,
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def change_set_item(change_request: ChangeRequest) -> ChangeSetItem:
    return ChangeSetItem(
        change_set_item_id="csi-1",
        change_request_id=change_request.change_request_id,
        target_entity_type="feature",
        target_entity_id="feat-1",
        change_type=ChangeType.UPDATE,
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def change_impact_map(change_request: ChangeRequest) -> ChangeImpactMap:
    return ChangeImpactMap(
        change_impact_map_id="cim-1",
        change_request_id=change_request.change_request_id,
        affected_entity_refs=["feat-1", "story-1", "flow-1"],
        invalidated_entity_refs=["req-1", "task-1"],
        regeneration_candidates=["req-1", "task-1", "tc-1"],
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


# ── Build ────────────────────────────────────────────────────────────────────

@pytest.fixture
def build_artifact(product: Product) -> BuildArtifact:
    return BuildArtifact(
        build_artifact_id="ba-1",
        product_id=product.product_id,
        artifact_refs=["ca-1"],
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def build_run(product: Product, build_artifact: BuildArtifact) -> BuildRun:
    return BuildRun(
        build_run_id="br-1",
        product_id=product.product_id,
        build_artifact_id=build_artifact.build_artifact_id,
        initiated_by=TEST_USER,
    )


# ── Delivery ─────────────────────────────────────────────────────────────────

@pytest.fixture
def repository_target(product: Product) -> RepositoryTarget:
    return RepositoryTarget(
        repository_target_id="rt-1",
        product_id=product.product_id,
        provider="github",
        repository_name="test-product",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def export_manifest(product: Product) -> ExportManifest:
    return ExportManifest(
        export_manifest_id="em-1",
        product_id=product.product_id,
        build_run_id="br-1",
        included_artifact_ids=["ca-1"],
        file_entries=[
            FileEntry(
                target_file_path="src/services/auth_service.py",
                source_artifact_id="ca-1",
                artifact_type="service",
            )
        ],
        lineage_entries=[
            LineageEntry(
                file_path="src/services/auth_service.py",
                task_id="task-1",
                requirement_ids=["req-1"],
                test_ids=["tc-1"],
                architecture_ids=["arch-1"],
                code_artifact_id="ca-1",
                generation_run_id="gr-1",
            )
        ],
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def git_export_run(product: Product) -> GitExportRun:
    return GitExportRun(
        git_export_run_id="ger-1",
        product_id=product.product_id,
        build_run_id="br-1",
        repository_target_id="rt-1",
        export_manifest_id="em-1",
        branch_name="feature/auth",
        commit_message="Add auth service",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def commit_bundle(repository_target: RepositoryTarget, export_manifest: ExportManifest) -> CommitBundle:
    return CommitBundle(
        commit_bundle_id="cb-1",
        repository_target_id=repository_target.repository_target_id,
        branch_name="feature/auth",
        commit_message="Add auth service",
        export_manifest_id=export_manifest.export_manifest_id,
        changed_files=["src/services/auth_service.py"],
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )


@pytest.fixture
def release_package(product: Product) -> ReleasePackage:
    return ReleasePackage(
        release_package_id="rp-1",
        product_id=product.product_id,
        build_run_id="br-1",
        git_export_run_id="ger-1",
        handoff_notes="Initial release of auth service",
        created_by=SYSTEM_USER,
        updated_by=SYSTEM_USER,
    )
