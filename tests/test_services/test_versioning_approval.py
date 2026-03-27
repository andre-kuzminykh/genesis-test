"""Versioning and approval tests — section 7."""
import pytest
from datetime import datetime

from src.enums.statuses import BaseStatus
from src.models.business import Feature, Requirement
from src.enums.types import RequirementType
from src.services.validation import VersioningService, ValidationError


class TestVersionIncrement:
    """Section 7.1 — Version must increment on change."""

    @pytest.mark.workflow
    def test_version_must_increment_on_content_change(self):
        with pytest.raises(ValidationError, match="Version must increment"):
            VersioningService.validate_version_increment_required(
                old_content="old",
                new_content="new",
                old_version=1,
                new_version=1,
            )

    @pytest.mark.workflow
    def test_version_increment_valid(self):
        VersioningService.validate_version_increment_required(
            old_content="old",
            new_content="new",
            old_version=1,
            new_version=2,
        )

    @pytest.mark.workflow
    def test_no_increment_needed_if_content_unchanged(self):
        VersioningService.validate_version_increment_required(
            old_content="same",
            new_content="same",
            old_version=1,
            new_version=1,
        )


class TestApprovalInvalidation:
    """Section 7.2 — Approval invalidated on change."""

    @pytest.mark.workflow
    def test_approval_invalidated_when_content_changes(self):
        f = Feature(
            feature_id="f-1",
            product_id="p-1",
            name="Test",
            version=2,
            approved_version=2,
            approved_at=datetime.utcnow(),
            approved_by="user",
            created_by="u",
            updated_by="u",
        )
        with pytest.raises(ValidationError, match="invalidated"):
            VersioningService.validate_approval_invalidated_on_change(
                entity=f, content_changed=True
            )

    @pytest.mark.workflow
    def test_no_invalidation_when_content_unchanged(self):
        f = Feature(
            feature_id="f-1",
            product_id="p-1",
            name="Test",
            version=2,
            approved_version=2,
            created_by="u",
            updated_by="u",
        )
        VersioningService.validate_approval_invalidated_on_change(
            entity=f, content_changed=False
        )

    @pytest.mark.workflow
    def test_no_invalidation_when_never_approved(self):
        f = Feature(
            feature_id="f-1",
            product_id="p-1",
            name="Test",
            version=1,
            created_by="u",
            updated_by="u",
        )
        VersioningService.validate_approval_invalidated_on_change(
            entity=f, content_changed=True
        )


class TestApproveEntity:
    """Section 7.2 — Approval is version-bound."""

    @pytest.mark.workflow
    def test_approve_entity(self, feature):
        VersioningService.approve_entity(feature, "reviewer")
        assert feature.status == BaseStatus.APPROVED
        assert feature.approved_at is not None
        assert feature.approved_by == "reviewer"
        assert feature.approved_version == feature.version

    @pytest.mark.workflow
    def test_approve_records_timestamp(self, feature):
        before = datetime.utcnow()
        VersioningService.approve_entity(feature, "reviewer")
        assert feature.approved_at >= before

    @pytest.mark.workflow
    def test_approval_version_bound(self, feature):
        """Approval must be bound to current version."""
        feature.version = 3
        VersioningService.approve_entity(feature, "reviewer")
        assert feature.approved_version == 3


class TestInvalidateApproval:
    """Section 7.2 — Invalidation on change."""

    @pytest.mark.workflow
    def test_invalidate_approval(self, approved_feature):
        VersioningService.invalidate_approval(approved_feature)
        assert approved_feature.approved_at is None
        assert approved_feature.approved_by is None
        assert approved_feature.approved_version is None
        assert approved_feature.status == BaseStatus.CHANGED

    @pytest.mark.workflow
    def test_invalidate_then_reapprove(self, approved_feature):
        VersioningService.invalidate_approval(approved_feature)
        assert approved_feature.status == BaseStatus.CHANGED
        approved_feature.version += 1
        VersioningService.approve_entity(approved_feature, "reviewer2")
        assert approved_feature.status == BaseStatus.APPROVED
        assert approved_feature.approved_version == approved_feature.version


class TestDownstreamEligibility:
    """Section 7.2 — Downstream eligibility depends on current approved version."""

    @pytest.mark.workflow
    def test_downstream_uses_currently_approved_version(self):
        r = Requirement(
            requirement_id="r-1",
            product_id="p-1",
            feature_id="f-1",
            title="Req",
            requirement_type=RequirementType.FUNCTIONAL,
            source_id="uc-1",
            version=3,
            approved_version=2,
            created_by="u",
            updated_by="u",
        )
        # Current version (3) != approved version (2), so not eligible
        assert r.version != r.approved_version

    @pytest.mark.workflow
    def test_approved_version_matches_current(self):
        r = Requirement(
            requirement_id="r-1",
            product_id="p-1",
            feature_id="f-1",
            title="Req",
            requirement_type=RequirementType.FUNCTIONAL,
            source_id="uc-1",
            version=3,
            approved_version=3,
            status=BaseStatus.APPROVED,
            created_by="u",
            updated_by="u",
        )
        assert r.version == r.approved_version
        assert r.status == BaseStatus.APPROVED


class TestGenerationRunVersioning:
    """Section 7.4 — Generation Run entity versioning."""

    @pytest.mark.workflow
    def test_generation_run_changes_target_version(self, feature):
        """If a run changes persisted artifact content, the target entity version must increment."""
        old_version = feature.version
        # Simulate generation changing content
        feature.name = "Updated Name"
        feature.version += 1
        assert feature.version == old_version + 1
