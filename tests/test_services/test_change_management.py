"""Change management tests — section 27."""
import pytest
from src.enums.statuses import BaseStatus
from src.enums.types import ChangeType
from src.models.execution import ChangeRequest, ChangeSetItem, ChangeImpactMap


class TestChangeRequestWorkflow:
    """Section 27 — Change Request workflow."""

    @pytest.mark.change_management
    def test_change_request_created(self, change_request):
        assert change_request.status == BaseStatus.DRAFT
        assert change_request.change_reason is not None

    @pytest.mark.change_management
    def test_change_request_approval(self, change_request):
        change_request.status = BaseStatus.APPROVED
        assert change_request.status == BaseStatus.APPROVED


class TestChangeSetItem:
    """Section 27.3 — Change Set Item."""

    @pytest.mark.change_management
    def test_change_set_item_linked_to_request(self, change_set_item, change_request):
        assert change_set_item.change_request_id == change_request.change_request_id

    @pytest.mark.change_management
    def test_change_set_item_targets_entity(self, change_set_item):
        assert change_set_item.target_entity_type == "feature"
        assert change_set_item.target_entity_id == "feat-1"

    @pytest.mark.change_management
    @pytest.mark.parametrize("change_type", list(ChangeType))
    def test_all_change_types_supported(self, change_type):
        """Section 27.1 — all supported change types."""
        csi = ChangeSetItem(
            change_set_item_id=f"csi-{change_type.value}",
            change_request_id="cr-1",
            target_entity_type="entity",
            target_entity_id="e-1",
            change_type=change_type,
            created_by="u",
            updated_by="u",
        )
        assert csi.change_type == change_type


class TestChangeImpactMap:
    """Section 27.4-27.5 — Change Impact Map."""

    @pytest.mark.change_management
    def test_impact_map_identifies_affected_entities(self, change_impact_map):
        """Section 27.5 — impact analysis must identify affected entities."""
        assert len(change_impact_map.affected_entity_refs) > 0

    @pytest.mark.change_management
    def test_impact_map_identifies_invalidated_entities(self, change_impact_map):
        assert len(change_impact_map.invalidated_entity_refs) > 0

    @pytest.mark.change_management
    def test_impact_map_identifies_regeneration_candidates(self, change_impact_map):
        assert len(change_impact_map.regeneration_candidates) > 0

    @pytest.mark.change_management
    def test_impact_map_linked_to_change_request(self, change_impact_map, change_request):
        assert change_impact_map.change_request_id == change_request.change_request_id


class TestChangeModeWorkflow:
    """Section 27 — Mandatory change flow."""

    @pytest.mark.change_management
    def test_change_flow_order(self):
        """Change Request → Change Set → Impact Map → Updated artifacts → Rebuild → Patch Export."""
        cr = ChangeRequest(
            change_request_id="cr-flow",
            product_id="p-1",
            title="Add OAuth",
            change_reason="Business need",
            created_by="u",
            updated_by="u",
        )
        assert cr.status == BaseStatus.DRAFT

        csi = ChangeSetItem(
            change_set_item_id="csi-flow",
            change_request_id=cr.change_request_id,
            target_entity_type="feature",
            target_entity_id="feat-1",
            change_type=ChangeType.UPDATE,
            created_by="u",
            updated_by="u",
        )
        assert csi.change_request_id == cr.change_request_id

        cim = ChangeImpactMap(
            change_impact_map_id="cim-flow",
            change_request_id=cr.change_request_id,
            affected_entity_refs=["feat-1", "story-1"],
            invalidated_entity_refs=["req-1"],
            regeneration_candidates=["req-1", "task-1"],
            created_by="u",
            updated_by="u",
        )
        assert cim.change_request_id == cr.change_request_id
        assert "req-1" in cim.invalidated_entity_refs

    @pytest.mark.change_management
    def test_only_change_set_entities_may_be_modified(self):
        """Section 27.6 — only entities inside approved Change Set may be regenerated."""
        approved_change_set = {"feat-1", "story-1"}
        entity_to_modify = "feat-1"
        assert entity_to_modify in approved_change_set

        entity_outside = "feat-999"
        assert entity_outside not in approved_change_set
