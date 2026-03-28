"""Tests for wizard flow: /start, review text lists, pagination, save as buttons.

Flow: name → desc → summary review → Далее → features TEXT → edit → Далее → buttons
Same for stories: TEXT review → edit → Далее → buttons

## Traceability
Feature: F001 — Product Management (Wizard Flow)
"""
from __future__ import annotations

import math
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Message, CallbackQuery, Chat, User

from state.product_state import ProductFSM
from callback.navigation_cb import MenuCB, WizardCB, ProductCB, FeatureCB, PageCB


# ─── Helpers ────────────────────────────────────────────────


def _make_message(text: str = "", voice: bool = False) -> MagicMock:
    msg = MagicMock(spec=Message)
    msg.text = text
    msg.voice = MagicMock() if voice else None
    msg.audio = None
    msg.document = None
    msg.delete = AsyncMock()
    msg.bot = MagicMock()
    sent = MagicMock()
    sent.message_id = 42
    sent.edit_text = AsyncMock()
    msg.answer = AsyncMock(return_value=sent)
    msg.chat = MagicMock(spec=Chat, id=1)
    msg.from_user = MagicMock(spec=User, id=1, first_name="Test")
    return msg


def _make_callback(data: str) -> MagicMock:
    cb = MagicMock(spec=CallbackQuery)
    cb.data = data
    cb.answer = AsyncMock()
    cb.message = MagicMock()
    cb.message.edit_text = AsyncMock()
    cb.message.answer = AsyncMock()
    cb.message.message_id = 10
    return cb


def _make_state(data: dict = None, current_state: str = None) -> AsyncMock:
    state = AsyncMock()
    state.get_data = AsyncMock(return_value=data or {})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    state.get_state = AsyncMock(return_value=current_state)
    return state


# ═══════════════════════════════════════════════════════════
# /start
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_start_no_products_starts_wizard():
    from handler.v1.user.wizard.main_widget import cmd_start
    msg = _make_message("/start")
    state = _make_state()
    with patch("handler.v1.user.wizard.main_widget._product_api") as api:
        api.get_all = AsyncMock(return_value=[])
        await cmd_start(msg, state)
    state.set_state.assert_awaited_once_with(ProductFSM.waiting_for_name)
    msg.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_with_products_shows_paginated_list():
    from handler.v1.user.wizard.main_widget import cmd_start
    products = [{"id": str(i), "name": f"Prod {i}"} for i in range(7)]
    msg = _make_message("/start")
    state = _make_state()
    with patch("handler.v1.user.wizard.main_widget._product_api") as api:
        api.get_all = AsyncMock(return_value=products)
        await cmd_start(msg, state)
    kb = msg.answer.call_args[1]["reply_markup"]
    product_btns = [b.text for r in kb.inline_keyboard for b in r if b.text.startswith("📦")]
    assert len(product_btns) == 5  # max 5 per page


@pytest.mark.asyncio
async def test_start_api_failure_starts_wizard():
    from handler.v1.user.wizard.main_widget import cmd_start
    msg = _make_message("/start")
    state = _make_state()
    with patch("handler.v1.user.wizard.main_widget._product_api") as api:
        api.get_all = AsyncMock(side_effect=Exception("fail"))
        await cmd_start(msg, state)
    state.set_state.assert_awaited_once_with(ProductFSM.waiting_for_name)


# ═══════════════════════════════════════════════════════════
# Pagination
# ═══════════════════════════════════════════════════════════


def test_page_row_always_3_buttons():
    from handler.v1.user.wizard.main_widget import _page_row
    # Page 1 of 3: · 1/3 ▶️
    row = _page_row("x", 1, 3)
    assert len(row) == 3
    assert row[0].text == "·"  # no left
    assert row[1].text == "1/3"
    assert row[2].text == "▶️"

    # Page 2 of 3: ◀️ 2/3 ▶️
    row = _page_row("x", 2, 3)
    assert row[0].text == "◀️"
    assert row[1].text == "2/3"
    assert row[2].text == "▶️"

    # Page 3 of 3: ◀️ 3/3 ·
    row = _page_row("x", 3, 3)
    assert row[0].text == "◀️"
    assert row[1].text == "3/3"
    assert row[2].text == "·"


def test_page_row_single_page_empty():
    from handler.v1.user.wizard.main_widget import _page_row
    assert _page_row("x", 1, 1) == []


def test_products_kb_max_5():
    from handler.v1.user.wizard.main_widget import _products_kb
    products = [{"id": str(i), "name": f"P{i}"} for i in range(12)]
    kb = _products_kb(products, page=1)
    product_btns = [b.text for r in kb.inline_keyboard for b in r if b.text.startswith("📦")]
    assert len(product_btns) == 5


def test_products_kb_page_2():
    from handler.v1.user.wizard.main_widget import _products_kb
    products = [{"id": str(i), "name": f"P{i}"} for i in range(12)]
    kb = _products_kb(products, page=2)
    product_btns = [b.text for r in kb.inline_keyboard for b in r if b.text.startswith("📦")]
    assert len(product_btns) == 5


def test_products_kb_last_page():
    from handler.v1.user.wizard.main_widget import _products_kb
    products = [{"id": str(i), "name": f"P{i}"} for i in range(12)]
    kb = _products_kb(products, page=3)
    product_btns = [b.text for r in kb.inline_keyboard for b in r if b.text.startswith("📦")]
    assert len(product_btns) == 2


# ═══════════════════════════════════════════════════════════
# Name step
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_product_name_saves_and_deletes_msg():
    from handler.v1.user.wizard.main_widget import handle_product_name
    msg = _make_message("My Product")
    state = _make_state(data={"bot_msg_id": 10})
    msg.bot.edit_message_text = AsyncMock()
    await handle_product_name(msg, state)
    state.update_data.assert_any_await(product_name="My Product")
    state.set_state.assert_awaited_once_with(ProductFSM.waiting_for_description)
    msg.delete.assert_awaited_once()


# ═══════════════════════════════════════════════════════════
# Description step
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_description_generates_summary():
    from handler.v1.user.wizard.main_widget import handle_product_description
    msg = _make_message("A task tool")
    state = _make_state(data={"product_name": "TaskMgr", "bot_msg_id": 10})
    msg.bot.edit_message_text = AsyncMock()
    bot = MagicMock()
    with patch("handler.v1.user.wizard.main_widget._ai") as ai, \
         patch("handler.v1.user.wizard.main_widget.get_text_or_voice",
               new=AsyncMock(return_value="A task tool")):
        ai.generate_product_summary = AsyncMock(return_value="Summary text")
        await handle_product_description(msg, state, bot)
    state.update_data.assert_any_await(product_summary="Summary text")
    state.set_state.assert_awaited_once_with(ProductFSM.reviewing_summary)
    msg.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_description_empty_rejects():
    from handler.v1.user.wizard.main_widget import handle_product_description
    msg = _make_message("")
    state = _make_state(data={"product_name": "X", "bot_msg_id": 10})
    msg.bot.edit_message_text = AsyncMock()
    bot = MagicMock()
    with patch("handler.v1.user.wizard.main_widget.get_text_or_voice",
               new=AsyncMock(return_value="")):
        await handle_product_description(msg, state, bot)
    state.set_state.assert_not_awaited()


# ═══════════════════════════════════════════════════════════
# Summary review — edit by typing
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_summary_edit_by_text():
    from handler.v1.user.wizard.main_widget import handle_summary_edit
    msg = _make_message("Remove second point")
    state = _make_state(data={
        "product_name": "MyProd", "product_summary": "Old", "bot_msg_id": 10,
    })
    msg.bot.edit_message_text = AsyncMock()
    bot = MagicMock()
    with patch("handler.v1.user.wizard.main_widget._ai") as ai, \
         patch("handler.v1.user.wizard.main_widget.get_text_or_voice",
               new=AsyncMock(return_value="Remove second point")):
        ai.edit_text = AsyncMock(return_value="Updated")
        await handle_summary_edit(msg, state, bot)
    state.update_data.assert_any_await(product_summary="Updated")
    msg.delete.assert_awaited_once()


# ═══════════════════════════════════════════════════════════
# wizard_next — features as TEXT (NOT saved yet)
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_wizard_next_generates_features_as_text():
    from handler.v1.user.wizard.main_widget import handle_wizard_next
    cb = _make_callback("wizard_next")
    state = _make_state(
        data={"product_name": "MyProd", "product_summary": "Summary"},
        current_state=ProductFSM.reviewing_summary.state,
    )
    with patch("handler.v1.user.wizard.main_widget._product_api") as p_api, \
         patch("handler.v1.user.wizard.main_widget._ai") as ai:
        p_api.create = AsyncMock(return_value={"id": "p1", "name": "MyProd"})
        ai.generate_features_json = AsyncMock(return_value=[
            {"name": "Auth", "description": "User authentication"},
            {"name": "Dashboard", "description": "Main view"},
        ])
        await handle_wizard_next(cb, state)

    # Features NOT saved to backend — stored as draft in FSM
    state.update_data.assert_any_await(draft_features=[
        {"name": "Auth", "description": "User authentication"},
        {"name": "Dashboard", "description": "Main view"},
    ])
    state.set_state.assert_awaited_with(ProductFSM.reviewing_features)

    # Text contains numbered features with descriptions
    text = cb.message.edit_text.call_args_list[-1][0][0]
    assert "1." in text and "Auth" in text
    assert "2." in text and "Dashboard" in text
    assert "User authentication" in text  # full description, not truncated


@pytest.mark.asyncio
async def test_wizard_next_wrong_state():
    from handler.v1.user.wizard.main_widget import handle_wizard_next
    cb = _make_callback("wizard_next")
    state = _make_state(current_state=None)
    await handle_wizard_next(cb, state)
    state.set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_wizard_next_api_error():
    from handler.v1.user.wizard.main_widget import handle_wizard_next
    cb = _make_callback("wizard_next")
    state = _make_state(
        data={"product_name": "X", "product_summary": "S"},
        current_state=ProductFSM.reviewing_summary.state,
    )
    with patch("handler.v1.user.wizard.main_widget._product_api") as p_api:
        p_api.create = AsyncMock(side_effect=Exception("DB error"))
        await handle_wizard_next(cb, state)
    assert "DB error" in cb.message.edit_text.call_args[0][0]


# ═══════════════════════════════════════════════════════════
# reviewing_features — edit TEXT by typing
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_features_edit_by_text():
    from handler.v1.user.wizard.main_widget import handle_features_edit
    msg = _make_message("Add a notifications feature")
    state = _make_state(data={
        "product_id": "p1",
        "draft_features": [
            {"name": "Auth", "description": "Login"},
        ],
        "bot_msg_id": 10,
    })
    msg.bot.edit_message_text = AsyncMock()
    bot = MagicMock()
    with patch("handler.v1.user.wizard.main_widget._ai") as ai, \
         patch("handler.v1.user.wizard.main_widget.get_text_or_voice",
               new=AsyncMock(return_value="Add a notifications feature")):
        ai.edit_features_list = AsyncMock(return_value=[
            {"name": "Auth", "description": "Login"},
            {"name": "Notifications", "description": "Push notifications"},
        ])
        await handle_features_edit(msg, state, bot)
    msg.delete.assert_awaited_once()
    state.update_data.assert_any_await(draft_features=[
        {"name": "Auth", "description": "Login"},
        {"name": "Notifications", "description": "Push notifications"},
    ])


# ═══════════════════════════════════════════════════════════
# wizard_save_features — save and show as BUTTONS
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_save_features_drills_into_roles():
    from handler.v1.user.wizard.main_widget import handle_save_features
    cb = _make_callback("wizard_save_features")
    saved_features = [
        {"id": "f1", "name": "Auth", "description": "Login", "status": "draft"},
        {"id": "f2", "name": "Dashboard", "description": "View", "status": "draft"},
    ]
    data = {
        "product_id": "p1",
        "draft_features": [
            {"name": "Auth", "description": "Login"},
            {"name": "Dashboard", "description": "View"},
        ],
    }
    data_after = {**data, "saved_features": saved_features}
    state = _make_state(data=data)
    state.get_data = AsyncMock(side_effect=[data, data_after])

    with patch("handler.v1.user.wizard.main_widget._feature_api") as f_api, \
         patch("handler.v1.user.wizard.main_widget._ai") as ai:
        f_api.create = AsyncMock(side_effect=saved_features)
        ai.generate_roles_json = AsyncMock(return_value=[
            {"name": "End User", "description": "Regular user", "role_type": "end_user"},
        ])
        await handle_save_features(cb, state)

    assert f_api.create.await_count == 2
    ai.generate_roles_json.assert_awaited_once()
    state.set_state.assert_awaited_with(ProductFSM.reviewing_roles)


@pytest.mark.asyncio
async def test_save_features_empty_alert():
    from handler.v1.user.wizard.main_widget import handle_save_features
    cb = _make_callback("wizard_save_features")
    state = _make_state(data={"draft_features": [], "product_id": "p1"})
    await handle_save_features(cb, state)
    cb.answer.assert_awaited_with("Нет фичей для сохранения", show_alert=True)


# ═══════════════════════════════════════════════════════════
# Feature view → roles as TEXT for review
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_feature_view_generates_roles_as_text():
    from handler.v1.user.wizard.main_widget import handle_feature
    cb = _make_callback(FeatureCB(id="f1", action="view").pack())
    cb_data = FeatureCB(id="f1", action="view")
    state = _make_state()

    with patch("handler.v1.user.wizard.main_widget._feature_api") as f_api, \
         patch("handler.v1.user.wizard.main_widget._feature_actor_link_api") as link_api, \
         patch("handler.v1.user.wizard.main_widget._ai") as ai:
        f_api.get_by_id = AsyncMock(return_value={
            "id": "f1", "name": "Auth", "description": "Login", "product_id": "p1",
        })
        link_api.get_all = AsyncMock(return_value=[])  # no saved roles
        ai.generate_roles_json = AsyncMock(return_value=[
            {"name": "End User", "description": "Regular user", "role_type": "end_user"},
        ])
        await handle_feature(cb, cb_data, state)

    # Roles generated as text draft
    state.set_state.assert_awaited_with(ProductFSM.reviewing_roles)
    text = cb.message.edit_text.call_args_list[-1][0][0]
    assert "End User" in text
    assert "Далее" in str(cb.message.edit_text.call_args_list[-1])


@pytest.mark.asyncio
async def test_feature_view_with_saved_roles_shows_buttons():
    from handler.v1.user.wizard.main_widget import handle_feature
    cb = _make_callback(FeatureCB(id="f1", action="view").pack())
    cb_data = FeatureCB(id="f1", action="view")
    state = _make_state()

    with patch("handler.v1.user.wizard.main_widget._feature_api") as f_api, \
         patch("handler.v1.user.wizard.main_widget._feature_actor_link_api") as link_api, \
         patch("handler.v1.user.wizard.main_widget._actor_api") as actor_api:
        f_api.get_by_id = AsyncMock(return_value={
            "id": "f1", "name": "Auth", "description": "Login", "product_id": "p1",
        })
        link_api.get_all = AsyncMock(return_value=[
            {"actor_id": "a1", "feature_id": "f1"},
        ])
        actor_api.get_by_id = AsyncMock(return_value={
            "id": "a1", "name": "End User", "role_type": "end_user", "status": "draft",
        })
        await handle_feature(cb, cb_data, state)

    # Shows roles as buttons
    kb = cb.message.edit_text.call_args[1].get("reply_markup")
    texts = [b.text for r in kb.inline_keyboard for b in r]
    assert any("End User" in t for t in texts)


# ═══════════════════════════════════════════════════════════
# reviewing_stories — edit TEXT by typing
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_stories_edit_by_text():
    from handler.v1.user.wizard.main_widget import handle_stories_edit
    msg = _make_message("Add a logout story")
    state = _make_state(data={
        "current_feature_id": "f1",
        "draft_stories": [{"title": "Login", "want": "log in", "benefit": "access"}],
        "bot_msg_id": 10,
    })
    msg.bot.edit_message_text = AsyncMock()
    bot = MagicMock()
    with patch("handler.v1.user.wizard.main_widget._ai") as ai, \
         patch("handler.v1.user.wizard.main_widget.get_text_or_voice",
               new=AsyncMock(return_value="Add a logout story")):
        ai.edit_stories_list = AsyncMock(return_value=[
            {"title": "Login", "want": "log in", "benefit": "access"},
            {"title": "Logout", "want": "log out", "benefit": "security"},
        ])
        await handle_stories_edit(msg, state, bot)
    msg.delete.assert_awaited_once()


# ═══════════════════════════════════════════════════════════
# wizard_save_stories — save and show as BUTTONS
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_save_stories_drills_into_flows():
    from handler.v1.user.wizard.main_widget import handle_save_stories
    cb = _make_callback("wizard_save_stories")
    saved_story = {"id": "s1", "title": "Login", "want": "log in", "status": "draft"}
    data = {
        "current_feature_id": "f1",
        "current_feature_product_id": "p1",
        "product_id": "p1",
        "draft_stories": [
            {"title": "Login", "want": "log in", "benefit": "access"},
        ],
    }
    data_after = {**data, "saved_stories": [saved_story]}
    state = _make_state(data=data)
    state.get_data = AsyncMock(side_effect=[data, data_after])

    with patch("handler.v1.user.wizard.main_widget._story_api") as s_api, \
         patch("handler.v1.user.wizard.main_widget._ai") as ai:
        s_api.create = AsyncMock(return_value=saved_story)
        ai.generate_flows_json = AsyncMock(return_value=[
            {"title": "Login flow", "flow_type": "primary", "description": "Steps"},
        ])
        await handle_save_stories(cb, state)

    s_api.create.assert_awaited_once()
    ai.generate_flows_json.assert_awaited_once()
    state.set_state.assert_awaited_with(ProductFSM.reviewing_flows)


# ═══════════════════════════════════════════════════════════
# Menu callbacks
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_menu_products():
    from handler.v1.user.wizard.main_widget import handle_menu
    cb = _make_callback(MenuCB(action="products").pack())
    state = _make_state()
    with patch("handler.v1.user.wizard.main_widget._product_api") as api:
        api.get_all = AsyncMock(return_value=[{"id": "1", "name": "P1"}])
        await handle_menu(cb, MenuCB(action="products"), state)
    state.clear.assert_awaited()


@pytest.mark.asyncio
async def test_menu_create():
    from handler.v1.user.wizard.main_widget import handle_menu
    cb = _make_callback(MenuCB(action="create_product").pack())
    state = _make_state()
    await handle_menu(cb, MenuCB(action="create_product"), state)
    state.set_state.assert_awaited_once_with(ProductFSM.waiting_for_name)


# ═══════════════════════════════════════════════════════════
# Formatting helpers
# ═══════════════════════════════════════════════════════════


def test_format_features_text():
    from handler.v1.user.wizard.main_widget import _format_features_text
    features = [
        {"name": "Auth", "description": "User login system"},
        {"name": "Dashboard", "description": "Main dashboard view"},
    ]
    text = _format_features_text(features)
    assert "1. " in text and "Auth" in text
    assert "2. " in text and "Dashboard" in text
    assert "User login system" in text  # full description
    assert "\n\n" in text or text.count("\n") >= 4  # spacing between features


def test_format_stories_text():
    from handler.v1.user.wizard.main_widget import _format_stories_text
    stories = [
        {"title": "Login", "want": "log in", "benefit": "access"},
        {"title": "Logout", "want": "log out", "benefit": "security"},
    ]
    text = _format_stories_text(stories)
    assert "1." in text and "Login" in text
    assert "2." in text and "Logout" in text


def test_review_kb_has_back_and_next():
    from handler.v1.user.wizard.main_widget import _review_kb
    kb = _review_kb(back_cb="back", next_cb="next", back_text="Назад")
    texts = [b.text for r in kb.inline_keyboard for b in r]
    assert "◀️ Назад" in texts
    assert "➡️ Далее" in texts


def test_send_long_splits():
    from handler.v1.user.wizard.main_widget import _send_long
    assert len(_send_long("A" * 5000, 4000)) == 2


def test_send_long_short():
    from handler.v1.user.wizard.main_widget import _send_long
    assert _send_long("Hi") == ["Hi"]


# ═══════════════════════════════════════════════════════════
# OpenAI prompts
# ═══════════════════════════════════════════════════════════


def test_system_prompt_no_markdown():
    from service.ai.openai_service import SYSTEM_PROMPT
    assert "markdown" in SYSTEM_PROMPT.lower() or "asterisk" in SYSTEM_PROMPT.lower()


def test_summary_prompt_client_problem_solution():
    import inspect
    from service.ai.openai_service import OpenAIService
    source = inspect.getsource(OpenAIService.generate_product_summary).lower()
    assert "client" in source
    assert "problem" in source
    assert "solution" in source
    assert "metric" in source


def test_edit_features_list_method_exists():
    from service.ai.openai_service import OpenAIService
    assert hasattr(OpenAIService, "edit_features_list")


def test_edit_stories_list_method_exists():
    from service.ai.openai_service import OpenAIService
    assert hasattr(OpenAIService, "edit_stories_list")


# ═══════════════════════════════════════════════════════════
# Callback data roundtrips
# ═══════════════════════════════════════════════════════════


def test_page_cb_roundtrip():
    cb = PageCB(entity="features", page=3, parent_id="p1")
    u = PageCB.unpack(cb.pack())
    assert u.entity == "features" and u.page == 3


def test_product_cb_roundtrip():
    cb = ProductCB(id="123", action="view")
    assert ProductCB.unpack(cb.pack()).id == "123"


def test_menu_cb_roundtrip():
    assert MenuCB.unpack(MenuCB(action="products").pack()).action == "products"


# ═══════════════════════════════════════════════════════════
# FSM states
# ═══════════════════════════════════════════════════════════


def test_fsm_has_required_states():
    states = [s.state for s in ProductFSM.__all_states__]
    for name in ("waiting_for_name", "waiting_for_description",
                 "reviewing_summary", "reviewing_features", "reviewing_stories"):
        assert any(name in s for s in states), f"Missing state: {name}"
