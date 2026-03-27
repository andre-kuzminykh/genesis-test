"""Specification health check tests — section 32."""
import pytest
from src.enums.statuses import BaseStatus
from src.enums.types import FlowType, RequirementType
from src.models.business import Feature, UserStory, UserFlow, UseCase, Requirement
from src.models.engineering import Task, TestDesign
from src.services.validation import SpecHealthChecker


def _feature(fid, status=BaseStatus.DRAFT):
    return Feature(feature_id=fid, product_id="p-1", name=fid, status=status, created_by="u", updated_by="u")


def _story(sid, fid, actor_id=None, status=BaseStatus.DRAFT):
    return UserStory(story_id=sid, product_id="p-1", feature_id=fid, actor_id=actor_id, title=sid, status=status, created_by="u", updated_by="u")


def _flow(fid, sid, flow_type=FlowType.PRIMARY, status=BaseStatus.DRAFT):
    return UserFlow(flow_id=fid, product_id="p-1", feature_id="f-1", story_id=sid, title=fid, flow_type=flow_type, mermaid_source="graph TD\n A-->B", status=status, created_by="u", updated_by="u")


def _uc(ucid, fid, status=BaseStatus.DRAFT):
    return UseCase(use_case_id=ucid, product_id="p-1", feature_id="f-1", story_id="s-1", flow_id=fid, title=ucid, status=status, created_by="u", updated_by="u")


def _req(rid, ucid=None, status=BaseStatus.DRAFT):
    return Requirement(requirement_id=rid, product_id="p-1", feature_id="f-1", primary_use_case_id=ucid, title=rid, requirement_type=RequirementType.FUNCTIONAL, status=status, created_by="u", updated_by="u")


def _td(tdid, rid):
    return TestDesign(test_design_id=tdid, product_id="p-1", requirement_id=rid, title=tdid, created_by="u", updated_by="u")


def _task(tid, req_ids=None, test_ids=None, cp_ref=None):
    return Task(task_id=tid, product_id="p-1", feature_id="f-1", requirement_ids=req_ids or [], linked_test_ids=test_ids or [], title=tid, context_package_ref=cp_ref, created_by="u", updated_by="u")


class TestFeaturesWithoutApprovedStories:
    """Section 32 — Features without approved Stories."""

    @pytest.mark.health
    def test_feature_without_approved_stories(self):
        checker = SpecHealthChecker(
            features=[_feature("f-1")],
            stories=[_story("s-1", "f-1", status=BaseStatus.DRAFT)],
            flows=[], use_cases=[], requirements=[], test_designs=[], tasks=[],
        )
        result = checker.features_without_approved_stories()
        assert "f-1" in result

    @pytest.mark.health
    def test_feature_with_approved_story(self):
        checker = SpecHealthChecker(
            features=[_feature("f-1")],
            stories=[_story("s-1", "f-1", status=BaseStatus.APPROVED)],
            flows=[], use_cases=[], requirements=[], test_designs=[], tasks=[],
        )
        result = checker.features_without_approved_stories()
        assert "f-1" not in result


class TestStoriesWithoutActors:
    """Section 32 — Stories without Actors."""

    @pytest.mark.health
    def test_story_without_actor(self):
        checker = SpecHealthChecker(
            features=[], stories=[_story("s-1", "f-1", actor_id=None)],
            flows=[], use_cases=[], requirements=[], test_designs=[], tasks=[],
        )
        result = checker.stories_without_actors()
        assert "s-1" in result

    @pytest.mark.health
    def test_story_with_actor(self):
        checker = SpecHealthChecker(
            features=[], stories=[_story("s-1", "f-1", actor_id="a-1")],
            flows=[], use_cases=[], requirements=[], test_designs=[], tasks=[],
        )
        result = checker.stories_without_actors()
        assert result == []


class TestStoriesWithoutPrimaryFlow:
    """Section 32 — Stories without a primary Flow."""

    @pytest.mark.health
    def test_story_without_primary_flow(self):
        checker = SpecHealthChecker(
            features=[], stories=[_story("s-1", "f-1")],
            flows=[], use_cases=[], requirements=[], test_designs=[], tasks=[],
        )
        result = checker.stories_without_primary_flow()
        assert "s-1" in result

    @pytest.mark.health
    def test_story_with_primary_flow(self):
        checker = SpecHealthChecker(
            features=[], stories=[_story("s-1", "f-1")],
            flows=[_flow("fl-1", "s-1", FlowType.PRIMARY)],
            use_cases=[], requirements=[], test_designs=[], tasks=[],
        )
        result = checker.stories_without_primary_flow()
        assert result == []

    @pytest.mark.health
    def test_story_with_only_alternative_flow_still_flagged(self):
        checker = SpecHealthChecker(
            features=[], stories=[_story("s-1", "f-1")],
            flows=[_flow("fl-1", "s-1", FlowType.ALTERNATIVE)],
            use_cases=[], requirements=[], test_designs=[], tasks=[],
        )
        result = checker.stories_without_primary_flow()
        assert "s-1" in result


class TestApprovedFlowsWithoutUseCases:
    """Section 32 — Approved Flows without Use Cases."""

    @pytest.mark.health
    def test_approved_flow_without_use_case(self):
        checker = SpecHealthChecker(
            features=[], stories=[],
            flows=[_flow("fl-1", "s-1", status=BaseStatus.APPROVED)],
            use_cases=[], requirements=[], test_designs=[], tasks=[],
        )
        result = checker.approved_flows_without_use_cases()
        assert "fl-1" in result

    @pytest.mark.health
    def test_draft_flow_without_use_case_not_flagged(self):
        checker = SpecHealthChecker(
            features=[], stories=[],
            flows=[_flow("fl-1", "s-1", status=BaseStatus.DRAFT)],
            use_cases=[], requirements=[], test_designs=[], tasks=[],
        )
        result = checker.approved_flows_without_use_cases()
        assert result == []


class TestApprovedUseCasesWithoutRequirements:
    """Section 32 — Approved Use Cases without Requirements."""

    @pytest.mark.health
    def test_approved_uc_without_requirement(self):
        checker = SpecHealthChecker(
            features=[], stories=[], flows=[],
            use_cases=[_uc("uc-1", "fl-1", status=BaseStatus.APPROVED)],
            requirements=[], test_designs=[], tasks=[],
        )
        result = checker.approved_use_cases_without_requirements()
        assert "uc-1" in result

    @pytest.mark.health
    def test_approved_uc_with_requirement(self):
        checker = SpecHealthChecker(
            features=[], stories=[], flows=[],
            use_cases=[_uc("uc-1", "fl-1", status=BaseStatus.APPROVED)],
            requirements=[_req("r-1", ucid="uc-1")],
            test_designs=[], tasks=[],
        )
        result = checker.approved_use_cases_without_requirements()
        assert result == []


class TestApprovedRequirementsWithoutTestDesigns:
    """Section 32 — Approved Requirements without Test Designs."""

    @pytest.mark.health
    def test_approved_req_without_test_design(self):
        checker = SpecHealthChecker(
            features=[], stories=[], flows=[], use_cases=[],
            requirements=[_req("r-1", status=BaseStatus.APPROVED)],
            test_designs=[], tasks=[],
        )
        result = checker.approved_requirements_without_test_designs()
        assert "r-1" in result

    @pytest.mark.health
    def test_approved_req_with_test_design(self):
        checker = SpecHealthChecker(
            features=[], stories=[], flows=[], use_cases=[],
            requirements=[_req("r-1", status=BaseStatus.APPROVED)],
            test_designs=[_td("td-1", "r-1")],
            tasks=[],
        )
        result = checker.approved_requirements_without_test_designs()
        assert result == []


class TestTasksWithoutLinkedTests:
    """Section 32 — Tasks without linked Test Cases."""

    @pytest.mark.health
    def test_task_without_tests(self):
        checker = SpecHealthChecker(
            features=[], stories=[], flows=[], use_cases=[],
            requirements=[], test_designs=[],
            tasks=[_task("t-1", req_ids=["r-1"])],
        )
        result = checker.tasks_without_linked_tests()
        assert "t-1" in result

    @pytest.mark.health
    def test_task_with_tests(self):
        checker = SpecHealthChecker(
            features=[], stories=[], flows=[], use_cases=[],
            requirements=[], test_designs=[],
            tasks=[_task("t-1", req_ids=["r-1"], test_ids=["tc-1"])],
        )
        result = checker.tasks_without_linked_tests()
        assert result == []


class TestTasksWithoutContextPackages:
    """Section 32 — Tasks without Context Packages."""

    @pytest.mark.health
    def test_task_without_cp(self):
        checker = SpecHealthChecker(
            features=[], stories=[], flows=[], use_cases=[],
            requirements=[], test_designs=[],
            tasks=[_task("t-1")],
        )
        result = checker.tasks_without_context_packages()
        assert "t-1" in result

    @pytest.mark.health
    def test_task_with_cp(self):
        checker = SpecHealthChecker(
            features=[], stories=[], flows=[], use_cases=[],
            requirements=[], test_designs=[],
            tasks=[_task("t-1", cp_ref="cp-1")],
        )
        result = checker.tasks_without_context_packages()
        assert result == []
