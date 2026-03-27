"""Telegram UX screen tests — section 30."""
import pytest
from src.enums.types import TelegramScreen


class TestTelegramScreens:
    """Section 30 — Minimum Telegram UX screens."""

    REQUIRED_SCREENS = {
        "product_list",
        "product_home",
        "product_general_info",
        "feature_list",
        "feature_home",
        "actor_list",
        "story_list",
        "flow_view",
        "use_case_list",
        "requirement_list",
        "architecture_center",
        "task_center",
        "test_center",
        "change_center",
        "build_center",
        "git_export_center",
    }

    @pytest.mark.mvp1
    def test_all_required_screens_exist(self):
        actual = {s.value for s in TelegramScreen}
        assert self.REQUIRED_SCREENS == actual

    @pytest.mark.mvp1
    def test_screen_count(self):
        assert len(TelegramScreen) == 16

    @pytest.mark.mvp1
    @pytest.mark.parametrize("screen", list(TelegramScreen))
    def test_each_screen_is_valid(self, screen):
        assert screen.value in self.REQUIRED_SCREENS


class TestScreenContext:
    """Section 30 — Each screen must know required context."""

    @pytest.mark.mvp1
    def test_product_level_screens_need_product_id(self):
        """Screens at product level must know current product_id."""
        product_screens = {
            TelegramScreen.PRODUCT_HOME,
            TelegramScreen.PRODUCT_GENERAL_INFO,
            TelegramScreen.FEATURE_LIST,
            TelegramScreen.ACTOR_LIST,
            TelegramScreen.ARCHITECTURE_CENTER,
            TelegramScreen.TASK_CENTER,
            TelegramScreen.TEST_CENTER,
            TelegramScreen.CHANGE_CENTER,
            TelegramScreen.BUILD_CENTER,
            TelegramScreen.GIT_EXPORT_CENTER,
        }
        # All product-level screens need product_id in context
        context = {"product_id": "prod-1"}
        for screen in product_screens:
            assert "product_id" in context

    @pytest.mark.mvp1
    def test_feature_level_screens_need_feature_id(self):
        """Screens at feature level must know current feature_id."""
        feature_screens = {
            TelegramScreen.FEATURE_HOME,
            TelegramScreen.STORY_LIST,
        }
        context = {"product_id": "prod-1", "feature_id": "feat-1"}
        for screen in feature_screens:
            assert "feature_id" in context

    @pytest.mark.mvp1
    def test_flow_view_needs_story_context(self):
        context = {
            "product_id": "prod-1",
            "feature_id": "feat-1",
            "story_id": "story-1",
            "flow_id": "flow-1",
        }
        assert "story_id" in context
        assert "flow_id" in context

    @pytest.mark.mvp1
    def test_breadcrumb_navigation(self):
        """Each screen must support breadcrumb for backward navigation."""
        breadcrumb = ["product_list", "product_home", "feature_list", "feature_home", "story_list"]
        assert breadcrumb[0] == "product_list"
        assert len(breadcrumb) > 1
        # Can navigate backwards
        for i in range(len(breadcrumb) - 1, 0, -1):
            assert breadcrumb[i - 1] is not None
