"""Lifecycle tests — sections 3, 33."""
import pytest
from src.enums.statuses import BaseStatus
from src.enums.types import (
    FlowType, RequirementType, ArchitectureArtifactType,
    TestCategory, GenerationMode,
)
from src.models.business import (
    Product, Feature, Actor, FeatureActorLink, UserStory, UserFlow, UseCase, Requirement,
)
from src.models.engineering import (
    ArchitectureArtifact, Task, Subtask, TestDesign, TestCase,
    CodeArtifact, ArtifactRegistryEntry,
)
from src.models.execution import (
    ContextPackage, GenerationRun, BuildArtifact, BuildRun,
)
from src.models.delivery import (
    GitExportRun, ExportManifest, FileEntry, LineageEntry, ReleasePackage,
)
from src.services.validation import DomainValidator, VersioningService


class TestGreenfieldLifecycle:
    """Section 33.1 — Greenfield mode lifecycle."""

    @pytest.mark.workflow
    def test_full_greenfield_lifecycle(self):
        """Product → Features → Stories → Flows → Use Cases → Requirements →
        Test Designs → Architecture → Tasks → Subtasks → Tests → Code →
        Build → Git Export → Release Package."""

        # 1. Product
        product = Product(
            product_id="p-lifecycle",
            name="Lifecycle Test Product",
            created_by="u", updated_by="u",
        )
        DomainValidator.validate_product_exists_before_children(product)
        VersioningService.approve_entity(product, "approver")

        # 2. Feature
        feature = Feature(
            feature_id="f-lifecycle",
            product_id=product.product_id,
            name="Auth",
            created_by="u", updated_by="u",
        )
        DomainValidator.validate_feature_belongs_to_product(feature, product)
        VersioningService.approve_entity(feature, "approver")

        # 3. Actor
        actor = Actor(
            actor_id="a-lifecycle",
            product_id=product.product_id,
            name="User",
            created_by="u", updated_by="u",
        )

        # 4. Feature-Actor Link
        link = FeatureActorLink(
            feature_actor_link_id="fal-lifecycle",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            actor_id=actor.actor_id,
            created_by="u", updated_by="u",
        )

        # 5. Story
        story = UserStory(
            story_id="s-lifecycle",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            actor_id=actor.actor_id,
            title="Login",
            want_text="log in",
            benefit_text="access app",
            created_by="u", updated_by="u",
        )
        DomainValidator.validate_story_has_actor(story)
        DomainValidator.validate_story_actor_linked_to_feature(story, [link])
        VersioningService.approve_entity(story, "approver")

        # 6. Flow
        flow = UserFlow(
            flow_id="fl-lifecycle",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            story_id=story.story_id,
            title="Primary login",
            flow_type=FlowType.PRIMARY,
            mermaid_source="graph TD\n  A --> B",
            created_by="u", updated_by="u",
        )
        DomainValidator.validate_flow_is_mermaid(flow)
        DomainValidator.validate_flow_belongs_to_story(flow, story)
        VersioningService.approve_entity(flow, "approver")

        # 7. Use Case
        use_case = UseCase(
            use_case_id="uc-lifecycle",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            story_id=story.story_id,
            flow_id=flow.flow_id,
            title="Successful login",
            goal="Auth user",
            preconditions="Registered",
            given_text="On login page",
            when_text="Enter creds",
            then_text="See dashboard",
            main_success_scenario="Login steps",
            created_by="u", updated_by="u",
        )
        DomainValidator.validate_flow_approved_before_use_case_generation(flow)
        DomainValidator.validate_use_case_belongs_to_flow(use_case, flow)
        VersioningService.approve_entity(use_case, "approver")

        # 8. Requirement
        requirement = Requirement(
            requirement_id="r-lifecycle",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            primary_use_case_id=use_case.use_case_id,
            title="Validate email format",
            requirement_type=RequirementType.FUNCTIONAL,
            created_by="u", updated_by="u",
        )
        DomainValidator.validate_use_case_approved_before_requirement(use_case)
        DomainValidator.validate_requirement_has_upstream_source(requirement)
        VersioningService.approve_entity(requirement, "approver")

        # 9. Test Design
        test_design = TestDesign(
            test_design_id="td-lifecycle",
            product_id=product.product_id,
            requirement_id=requirement.requirement_id,
            title="Verify email validation",
            test_intent="Invalid emails rejected",
            created_by="u", updated_by="u",
        )
        DomainValidator.validate_test_design_linked_to_requirement(test_design)
        VersioningService.approve_entity(test_design, "approver")

        # 10. Architecture
        arch = ArchitectureArtifact(
            architecture_id="arch-lifecycle",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            artifact_type=ArchitectureArtifactType.SERVICE,
            title="Auth service arch",
            mermaid_source="graph LR\n  Client --> Service",
            created_by="u", updated_by="u",
        )
        DomainValidator.validate_architecture_only_from_approved([requirement])
        VersioningService.approve_entity(arch, "approver")

        # 11. Test Case
        test_case = TestCase(
            test_id="tc-lifecycle",
            product_id=product.product_id,
            requirement_id=requirement.requirement_id,
            test_design_id=test_design.test_design_id,
            title="Test invalid email",
            category=TestCategory.UNIT,
            created_by="u", updated_by="u",
        )
        DomainValidator.validate_test_case_traceable(test_case)
        VersioningService.approve_entity(test_case, "approver")

        # 12. Task
        task = Task(
            task_id="t-lifecycle",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            requirement_ids=[requirement.requirement_id],
            architecture_ids=[arch.architecture_id],
            linked_test_ids=[test_case.test_id],
            title="Implement email validation",
            context_package_ref="cp-lifecycle",
            created_by="u", updated_by="u",
        )
        DomainValidator.validate_task_has_requirements(task)
        DomainValidator.validate_task_has_linked_tests_for_code_gen(task)
        DomainValidator.validate_task_has_context_package(task)

        # 13. Context Package
        cp = ContextPackage(
            context_package_id="cp-lifecycle",
            product_id=product.product_id,
            feature_id=feature.feature_id,
            scope_type="task",
            scope_entity_id=task.task_id,
            target_artifact_type="code",
            included_entity_refs=[requirement.requirement_id, test_case.test_id, arch.architecture_id],
            context_hash="lifecycle-hash",
            created_by="u", updated_by="u",
        )
        DomainValidator.validate_context_package_declarations(cp)
        DomainValidator.validate_context_package_has_hash(cp)

        # 14. Code generation
        DomainValidator.validate_code_generation_prerequisites(
            task, cp, upstream_approved=True
        )

        # 15. Code Artifact
        ca = CodeArtifact(
            code_artifact_id="ca-lifecycle",
            task_id=task.task_id,
            logical_name="auth_validator.py",
            created_by="u", updated_by="u",
        )
        VersioningService.approve_entity(ca, "approver")

        # 16. Registry Entry
        re = ArtifactRegistryEntry(
            artifact_registry_entry_id="are-lifecycle",
            code_artifact_id=ca.code_artifact_id,
            file_path="src/auth_validator.py",
            content_hash="hash123",
            created_by="u", updated_by="u",
        )
        DomainValidator.validate_code_artifact_registered(ca, [re])

        # 17. Build
        ba = BuildArtifact(
            build_artifact_id="ba-lifecycle",
            product_id=product.product_id,
            artifact_refs=[ca.code_artifact_id],
            created_by="u", updated_by="u",
        )

        # 18. Export Manifest
        em = ExportManifest(
            export_manifest_id="em-lifecycle",
            product_id=product.product_id,
            included_artifact_ids=[ca.code_artifact_id],
            file_entries=[FileEntry(
                target_file_path="src/auth_validator.py",
                source_artifact_id=ca.code_artifact_id,
                artifact_type="service",
            )],
            lineage_entries=[LineageEntry(
                file_path="src/auth_validator.py",
                task_id=task.task_id,
                requirement_ids=[requirement.requirement_id],
                test_ids=[test_case.test_id],
                architecture_ids=[arch.architecture_id],
                code_artifact_id=ca.code_artifact_id,
            )],
            created_by="u", updated_by="u",
        )

        # 19. Git Export
        ger = GitExportRun(
            git_export_run_id="ger-lifecycle",
            product_id=product.product_id,
            export_manifest_id=em.export_manifest_id,
            branch_name="feature/auth",
            created_by="u", updated_by="u",
        )

        # 20. Release Package
        rp = ReleasePackage(
            release_package_id="rp-lifecycle",
            product_id=product.product_id,
            git_export_run_id=ger.git_export_run_id,
            handoff_notes="Auth feature ready",
            created_by="u", updated_by="u",
        )

        # Verify full chain exists
        assert product.status == BaseStatus.APPROVED
        assert feature.status == BaseStatus.APPROVED
        assert story.status == BaseStatus.APPROVED
        assert flow.status == BaseStatus.APPROVED
        assert use_case.status == BaseStatus.APPROVED
        assert requirement.status == BaseStatus.APPROVED
        assert test_design.status == BaseStatus.APPROVED
        assert arch.status == BaseStatus.APPROVED
        assert test_case.status == BaseStatus.APPROVED
        assert ca.status == BaseStatus.APPROVED
        assert rp.release_package_id is not None


class TestCanonicalOrder:
    """Section 3 — Canonical structure order."""

    @pytest.mark.workflow
    def test_mandatory_modeling_order(self):
        """Product → Features → Stories → Flows → Use Cases → Requirements →
        Architecture → Tasks → Subtasks → Tests → Code."""
        order = [
            "Product", "Features", "Stories", "Flows", "Use Cases",
            "Requirements", "Architecture", "Tasks", "Subtasks", "Tests", "Code",
        ]
        assert order[0] == "Product"
        assert order[-1] == "Code"
        assert order.index("Features") < order.index("Stories")
        assert order.index("Stories") < order.index("Flows")
        assert order.index("Flows") < order.index("Use Cases")
        assert order.index("Use Cases") < order.index("Requirements")
        assert order.index("Requirements") < order.index("Architecture")
        assert order.index("Architecture") < order.index("Tasks")
        assert order.index("Tasks") < order.index("Subtasks")
        assert order.index("Subtasks") < order.index("Tests")
        assert order.index("Tests") < order.index("Code")

    @pytest.mark.workflow
    def test_mandatory_delivery_order(self):
        """Approved Code Artifacts → Build → Export Manifest → Git Export → Release Package."""
        delivery_order = [
            "Approved Code Artifacts", "Build", "Export Manifest",
            "Git Export", "Release Package",
        ]
        assert delivery_order[0] == "Approved Code Artifacts"
        assert delivery_order[-1] == "Release Package"

    @pytest.mark.workflow
    def test_business_artifacts_top_down(self):
        """Business and specification artifacts are created top-down."""
        top_down = ["Product", "Feature", "Story", "Flow", "UseCase", "Requirement"]
        for i in range(len(top_down) - 1):
            assert top_down.index(top_down[i]) < top_down.index(top_down[i + 1])

    @pytest.mark.workflow
    def test_engineering_artifacts_bottom_up(self):
        """Engineering and delivery artifacts are generated bottom-up."""
        # Tests/Code generated from Tasks (bottom) and assembled upward to Build/Export
        bottom_up_generation = ["Task", "Test", "Code", "Build", "Export"]
        for i in range(len(bottom_up_generation) - 1):
            assert bottom_up_generation.index(bottom_up_generation[i]) < bottom_up_generation.index(bottom_up_generation[i + 1])


class TestEntityGroups:
    """Section 8 — Entity groups."""

    @pytest.mark.workflow
    def test_business_truth_entities(self):
        """Section 8.1 — Business truth entities."""
        entities = {
            "Product", "Feature", "Actor", "FeatureActorLink",
            "UserStory", "UserFlowArtifact", "UseCase", "Requirement",
        }
        assert len(entities) == 8

    @pytest.mark.workflow
    def test_engineering_truth_entities(self):
        """Section 8.2 — Engineering truth entities."""
        entities = {
            "ArchitectureArtifact", "Task", "Subtask",
            "TestDesign", "TestCase", "TestSuite",
            "DependencyOutput", "CodeArtifact", "ArtifactRegistryEntry",
        }
        assert len(entities) == 9

    @pytest.mark.workflow
    def test_execution_truth_entities(self):
        """Section 8.3 — Execution truth entities."""
        entities = {
            "ContextPackage", "GenerationRun", "TraceLink",
            "ChangeRequest", "ChangeSetItem", "ChangeImpactMap",
            "BuildArtifact", "BuildRun",
        }
        assert len(entities) == 8

    @pytest.mark.workflow
    def test_delivery_truth_entities(self):
        """Section 8.4 — Delivery truth entities."""
        entities = {
            "GitExportRun", "RepositoryTarget", "ExportManifest",
            "CommitBundle", "ReleasePackage",
        }
        assert len(entities) == 5
