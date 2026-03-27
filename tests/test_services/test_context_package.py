"""Context Package tests — section 23."""
import pytest
from src.enums.types import GenerationMode
from src.models.execution import ContextPackage
from src.services.validation import DomainValidator, ValidationError


class TestContextPackageDeclarations:
    """Section 23.4 — Mandatory declarations."""

    @pytest.mark.context_package
    def test_context_package_must_declare_target_type(self, context_package):
        DomainValidator.validate_context_package_declarations(context_package)

    @pytest.mark.context_package
    def test_context_package_without_target_type_rejected(self, product):
        cp = ContextPackage(
            context_package_id="cp-bad",
            product_id=product.product_id,
            target_artifact_type="",
            context_hash="hash",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="target_artifact_type"):
            DomainValidator.validate_context_package_declarations(cp)


class TestContextPackageHash:
    """Section 23.5 — Determinism rule."""

    @pytest.mark.context_package
    def test_context_package_must_have_hash(self, context_package):
        DomainValidator.validate_context_package_has_hash(context_package)

    @pytest.mark.context_package
    def test_context_package_without_hash_rejected(self, product):
        cp = ContextPackage(
            context_package_id="cp-no-hash",
            product_id=product.product_id,
            target_artifact_type="code",
            context_hash=None,
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="context_hash"):
            DomainValidator.validate_context_package_has_hash(cp)

    @pytest.mark.context_package
    def test_equivalent_packages_same_hash(self):
        """Two equivalent Context Packages must produce the same context_hash (section 23.5)."""
        cp1 = ContextPackage(
            context_package_id="cp-a",
            product_id="p-1",
            target_artifact_type="code",
            included_entity_refs=["req-1", "tc-1"],
            context_hash="deterministic-hash-abc",
            created_by="u",
            updated_by="u",
        )
        cp2 = ContextPackage(
            context_package_id="cp-b",
            product_id="p-1",
            target_artifact_type="code",
            included_entity_refs=["req-1", "tc-1"],
            context_hash="deterministic-hash-abc",
            created_by="u",
            updated_by="u",
        )
        assert cp1.context_hash == cp2.context_hash


class TestContextPackageScope:
    """Section 23.4 — Scope and justification rules."""

    @pytest.mark.context_package
    def test_product_scope_requires_justification(self, product):
        """Full product context requires broader_context_justification."""
        cp = ContextPackage(
            context_package_id="cp-product",
            product_id=product.product_id,
            scope_type="product",
            target_artifact_type="code",
            context_hash="hash",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="broader_context_justification"):
            DomainValidator.validate_context_package_no_full_product_context(cp)

    @pytest.mark.context_package
    def test_product_scope_with_justification_allowed(self, product):
        cp = ContextPackage(
            context_package_id="cp-justified",
            product_id=product.product_id,
            scope_type="product",
            target_artifact_type="code",
            broader_context_justification="Cross-cutting security policy requires full product view",
            context_hash="hash",
            created_by="u",
            updated_by="u",
        )
        DomainValidator.validate_context_package_no_full_product_context(cp)

    @pytest.mark.context_package
    def test_task_scope_no_justification_needed(self, context_package):
        DomainValidator.validate_context_package_no_full_product_context(context_package)


class TestContextPackageStandardContent:
    """Section 23.3 — Standard included content by Task scope."""

    @pytest.mark.context_package
    def test_task_context_may_include_standard_refs(self):
        cp = ContextPackage(
            context_package_id="cp-full",
            product_id="p-1",
            feature_id="f-1",
            scope_type="task",
            scope_entity_id="task-1",
            target_artifact_type="code",
            target_artifact_id="ca-1",
            included_entity_refs=[
                "req-1",     # linked Requirements
                "td-1",      # linked Test Designs
                "tc-1",      # linked Test Cases
                "arch-1",    # linked Architecture fragments
            ],
            dependency_output_refs=["dep-1"],
            linked_code_artifact_refs=["ca-existing-1"],
            context_hash="hash",
            created_by="u",
            updated_by="u",
        )
        assert len(cp.included_entity_refs) == 4
        assert len(cp.dependency_output_refs) == 1
        assert len(cp.linked_code_artifact_refs) == 1

    @pytest.mark.context_package
    def test_context_package_supports_all_generation_modes(self):
        for mode in GenerationMode:
            cp = ContextPackage(
                context_package_id=f"cp-{mode.value}",
                product_id="p-1",
                target_artifact_type="code",
                generation_mode=mode,
                context_hash="hash",
                created_by="u",
                updated_by="u",
            )
            assert cp.generation_mode == mode
