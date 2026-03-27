"""Tests for the wizard flow: /start, pagination, create, Next, drill-down.

## Traceability
Feature: F001 — Product Management (Wizard Flow)
"""
from __future__ import annotations

import math
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from aiogram.types import Message, CallbackQuery, Chat, User

from state.product_state import ProductFSM
from callback.navigation_cb import MenuCB, WizardCB, ProductCB, FeatureCB, PageCB


# ─── Helpers ────────────────────────────────────────────────


def _make_message(text: str = "", voice: bool = False) -> MagicMock:
    msg = MagicMock(spec=Message)
    msg.text = text
    msg.voice = MagicMock() if voice else None
    msg.audio = None
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
    msg.delete.assert_awaited_once()  # user msg deleted


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
    # 5 products + page row + create button = 7 rows
    assert len(kb.inline_keyboard) == 7
    msg.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_api_failure_starts_wizard():
    from handler.v1.user.wizard.main_widget import cmd_start

    msg = _make_message("/start")
    state = _make_state()

    with patch("handler.v1.user.wizard.main_widget._product_api") as api:
        api.get_all = AsyncMock(side_effect=Exception("Connection refused"))
        await cmd_start(msg, state)

    state.set_state.assert_awaited_once_with(ProductFSM.waiting_for_name)


# ═══════════════════════════════════════════════════════════
# Pagination keyboards
# ═══════════════════════════════════════════════════════════


def test_products_kb_max_5_items():
    from handler.v1.user.wizard.main_widget import _products_kb

    products = [{"id": str(i), "name": f"P{i}"} for i in range(12)]
    kb = _products_kb(products, page=1)
    # 5 items + nav row + create = 7
    product_buttons = [
        btn.text for row in kb.inline_keyboard for btn in row
        if btn.text.startswith("📦")
    ]
    assert len(product_buttons) == 5


def test_products_kb_page_2():
    from handler.v1.user.wizard.main_widget import _products_kb

    products = [{"id": str(i), "name": f"P{i}"} for i in range(12)]
    kb = _products_kb(products, page=2)
    product_buttons = [
        btn.text for row in kb.inline_keyboard for btn in row
        if btn.text.startswith("📦")
    ]
    assert len(product_buttons) == 5  # items 5-9


def test_products_kb_last_page():
    from handler.v1.user.wizard.main_widget import _products_kb

    products = [{"id": str(i), "name": f"P{i}"} for i in range(12)]
    kb = _products_kb(products, page=3)
    product_buttons = [
        btn.text for row in kb.inline_keyboard for btn in row
        if btn.text.startswith("📦")
    ]
    assert len(product_buttons) == 2  # items 10-11


def test_products_kb_no_nav_for_few_items():
    from handler.v1.user.wizard.main_widget import _products_kb

    products = [{"id": "1", "name": "P1"}, {"id": "2", "name": "P2"}]
    kb = _products_kb(products, page=1)
    all_texts = [btn.text for row in kb.inline_keyboard for btn in row]
    # No ◀️ or ▶️ since everything fits on one page
    assert "◀️" not in all_texts
    assert "▶️" not in all_texts


def test_products_kb_has_nav_arrows():
    from handler.v1.user.wizard.main_widget import _products_kb

    products = [{"id": str(i), "name": f"P{i}"} for i in range(8)]
    kb_page1 = _products_kb(products, page=1)
    texts_p1 = [btn.text for row in kb_page1.inline_keyboard for btn in row]
    assert "▶️" in texts_p1
    assert "◀️" not in texts_p1  # no back on page 1

    kb_page2 = _products_kb(products, page=2)
    texts_p2 = [btn.text for row in kb_page2.inline_keyboard for btn in row]
    assert "◀️" in texts_p2
    assert "▶️" not in texts_p2  # page 2 is last (8 items / 5 = 2 pages)


def test_features_kb_pagination():
    from handler.v1.user.wizard.main_widget import _features_kb

    features = [{"id": str(i), "name": f"F{i}", "status": "draft"} for i in range(11)]
    kb = _features_kb(features, "prod-1", page=1)
    feat_btns = [btn.text for row in kb.inline_keyboard for btn in row if btn.text.startswith("📝")]
    assert len(feat_btns) == 5


def test_stories_kb_pagination():
    from handler.v1.user.wizard.main_widget import _stories_kb

    stories = [{"id": str(i), "title": f"Story {i}", "status": "draft"} for i in range(8)]
    kb = _stories_kb(stories, "feat-1", page=1)
    story_btns = [btn.text for row in kb.inline_keyboard for btn in row if btn.text.startswith("📝")]
    assert len(story_btns) == 5


def test_page_row_counter():
    from handler.v1.user.wizard.main_widget import _page_row

    row = _page_row("products", page=2, total_pages=5)
    texts = [btn.text for btn in row]
    assert "◀️" in texts
    assert "2/5" in texts
    assert "▶️" in texts


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
async def test_description_text_generates_summary():
    from handler.v1.user.wizard.main_widget import handle_product_description

    msg = _make_message("A task management tool")
    state = _make_state(data={"product_name": "TaskMgr", "bot_msg_id": 10})
    msg.bot.edit_message_text = AsyncMock()
    bot = MagicMock()

    with patch("handler.v1.user.wizard.main_widget._ai") as ai, \
         patch("handler.v1.user.wizard.main_widget.get_text_or_voice", new=AsyncMock(return_value="A task management tool")):
        ai.generate_product_summary = AsyncMock(return_value="Client: teams\nProblem: chaos")
        await handle_product_description(msg, state, bot)

    state.update_data.assert_any_await(product_summary="Client: teams\nProblem: chaos")
    state.set_state.assert_awaited_once_with(ProductFSM.reviewing_summary)
    msg.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_description_empty_rejects():
    from handler.v1.user.wizard.main_widget import handle_product_description

    msg = _make_message("")
    state = _make_state(data={"product_name": "X", "bot_msg_id": 10})
    msg.bot.edit_message_text = AsyncMock()
    bot = MagicMock()

    with patch("handler.v1.user.wizard.main_widget.get_text_or_voice", new=AsyncMock(return_value="")):
        await handle_product_description(msg, state, bot)

    state.set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_description_gpt_error():
    from handler.v1.user.wizard.main_widget import handle_product_description

    msg = _make_message("desc")
    state = _make_state(data={"product_name": "X", "bot_msg_id": 10})
    msg.bot.edit_message_text = AsyncMock()
    bot = MagicMock()

    with patch("handler.v1.user.wizard.main_widget._ai") as ai, \
         patch("handler.v1.user.wizard.main_widget.get_text_or_voice", new=AsyncMock(return_value="desc")):
        ai.generate_product_summary = AsyncMock(side_effect=Exception("GPT timeout"))
        await handle_product_description(msg, state, bot)

    # Should not crash, error shown to user
    state.set_state.assert_not_awaited()


# ═══════════════════════════════════════════════════════════
# Summary review — edit via text
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_reviewing_summary_text_edits():
    from handler.v1.user.wizard.main_widget import handle_summary_edit

    msg = _make_message("Remove second point")
    state = _make_state(data={
        "product_name": "MyProd",
        "product_summary": "Old summary",
        "bot_msg_id": 10,
    })
    msg.bot.edit_message_text = AsyncMock()
    bot = MagicMock()

    with patch("handler.v1.user.wizard.main_widget._ai") as ai, \
         patch("handler.v1.user.wizard.main_widget.get_text_or_voice", new=AsyncMock(return_value="Remove second point")):
        ai.edit_text = AsyncMock(return_value="Updated summary")
        await handle_summary_edit(msg, state, bot)

    state.update_data.assert_any_await(product_summary="Updated summary")
    msg.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_reviewing_summary_empty_rejects():
    from handler.v1.user.wizard.main_widget import handle_summary_edit

    msg = _make_message("")
    state = _make_state(data={"product_name": "X", "product_summary": "S", "bot_msg_id": 10})
    msg.bot.edit_message_text = AsyncMock()
    bot = MagicMock()

    with patch("handler.v1.user.wizard.main_widget.get_text_or_voice", new=AsyncMock(return_value="")):
        await handle_summary_edit(msg, state, bot)

    msg.delete.assert_awaited_once()


# ═══════════════════════════════════════════════════════════
# "Далее" button (wizard_next)
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_next_saves_product_and_generates_features():
    from handler.v1.user.wizard.main_widget import handle_wizard_next

    cb = _make_callback("wizard_next")
    state = _make_state(
        data={"product_name": "MyProd", "product_summary": "Summary"},
        current_state=ProductFSM.reviewing_summary.state,
    )

    with patch("handler.v1.user.wizard.main_widget._product_api") as p_api, \
         patch("handler.v1.user.wizard.main_widget._feature_api") as f_api, \
         patch("handler.v1.user.wizard.main_widget._ai") as ai:
        p_api.create = AsyncMock(return_value={"id": "prod-1", "name": "MyProd"})
        ai.generate_features_json = AsyncMock(return_value=[
            {"name": "Auth", "description": "Authentication"},
            {"name": "Dashboard", "description": "Main view"},
        ])
        f_api.create = AsyncMock(side_effect=[
            {"id": "f1", "name": "Auth", "description": "Authentication"},
            {"id": "f2", "name": "Dashboard", "description": "Main view"},
        ])
        await handle_wizard_next(cb, state)

    p_api.create.assert_awaited_once()
    state.set_state.assert_awaited_with(ProductFSM.reviewing_features)
    # Features shown as buttons
    kb = cb.message.edit_text.call_args_list[-1][1].get("reply_markup")
    assert kb is not None


@pytest.mark.asyncio
async def test_next_wrong_state_does_nothing():
    from handler.v1.user.wizard.main_widget import handle_wizard_next

    cb = _make_callback("wizard_next")
    state = _make_state(current_state=None)

    await handle_wizard_next(cb, state)

    cb.answer.assert_awaited()
    state.set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_next_api_error_shows_message():
    from handler.v1.user.wizard.main_widget import handle_wizard_next

    cb = _make_callback("wizard_next")
    state = _make_state(
        data={"product_name": "X", "product_summary": "S"},
        current_state=ProductFSM.reviewing_summary.state,
    )

    with patch("handler.v1.user.wizard.main_widget._product_api") as p_api:
        p_api.create = AsyncMock(side_effect=Exception("DB error"))
        await handle_wizard_next(cb, state)

    error_text = cb.message.edit_text.call_args[0][0]
    assert "DB error" in error_text


# ═══════════════════════════════════════════════════════════
# Menu callbacks
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_menu_products_shows_list():
    from handler.v1.user.wizard.main_widget import handle_menu

    cb = _make_callback(MenuCB(action="products").pack())
    cb_data = MenuCB(action="products")
    state = _make_state()

    with patch("handler.v1.user.wizard.main_widget._product_api") as api:
        api.get_all = AsyncMock(return_value=[{"id": "1", "name": "P1"}])
        await handle_menu(cb, cb_data, state)

    state.clear.assert_awaited()
    cb.message.edit_text.assert_awaited()


@pytest.mark.asyncio
async def test_menu_create_starts_wizard():
    from handler.v1.user.wizard.main_widget import handle_menu

    cb = _make_callback(MenuCB(action="create_product").pack())
    cb_data = MenuCB(action="create_product")
    state = _make_state()

    await handle_menu(cb, cb_data, state)

    state.set_state.assert_awaited_once_with(ProductFSM.waiting_for_name)


# ═══════════════════════════════════════════════════════════
# Product view
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_product_view_shows_features():
    from handler.v1.user.wizard.main_widget import handle_product

    cb = _make_callback(ProductCB(id="1", action="view").pack())
    cb_data = ProductCB(id="1", action="view")
    state = _make_state()

    with patch("handler.v1.user.wizard.main_widget._product_api") as p_api, \
         patch("handler.v1.user.wizard.main_widget._feature_api") as f_api:
        p_api.get_by_id = AsyncMock(return_value={
            "id": "1", "name": "Prod", "status": "draft", "goal": "Goal",
        })
        f_api.get_all = AsyncMock(return_value=[
            {"id": "f1", "name": "F1", "status": "draft"},
        ])
        await handle_product(cb, cb_data, state)

    cb.message.edit_text.assert_awaited()
    text = cb.message.edit_text.call_args[0][0]
    assert "Prod" in text


# ═══════════════════════════════════════════════════════════
# Feature view — auto-generates stories
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_feature_view_auto_generates_stories():
    from handler.v1.user.wizard.main_widget import handle_feature

    cb = _make_callback(FeatureCB(id="f1", action="view").pack())
    cb_data = FeatureCB(id="f1", action="view")
    state = _make_state()

    with patch("handler.v1.user.wizard.main_widget._feature_api") as f_api, \
         patch("handler.v1.user.wizard.main_widget._story_api") as s_api, \
         patch("handler.v1.user.wizard.main_widget._ai") as ai:
        f_api.get_by_id = AsyncMock(return_value={
            "id": "f1", "name": "Auth", "description": "Login", "product_id": "p1",
        })
        s_api.get_all = AsyncMock(side_effect=[
            [],  # first call: no stories
            [{"id": "s1", "title": "Login flow", "status": "draft"}],  # after gen
        ])
        ai.generate_stories_json = AsyncMock(return_value=[
            {"title": "Login flow", "want": "log in", "benefit": "access"},
        ])
        s_api.create = AsyncMock(return_value={"id": "s1"})
        await handle_feature(cb, cb_data, state)

    ai.generate_stories_json.assert_awaited_once()
    cb.message.edit_text.assert_awaited()


# ═══════════════════════════════════════════════════════════
# Pagination callback
# ═══════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_page_callback_products():
    from handler.v1.user.wizard.main_widget import handle_page

    cb = _make_callback(PageCB(entity="products", page=2).pack())
    cb_data = PageCB(entity="products", page=2)
    state = _make_state()

    products = [{"id": str(i), "name": f"P{i}"} for i in range(8)]
    with patch("handler.v1.user.wizard.main_widget._product_api") as api:
        api.get_all = AsyncMock(return_value=products)
        await handle_page(cb, cb_data, state)

    cb.message.edit_text.assert_awaited()


@pytest.mark.asyncio
async def test_page_callback_features():
    from handler.v1.user.wizard.main_widget import handle_page

    cb = _make_callback(PageCB(entity="features", page=1, parent_id="p1").pack())
    cb_data = PageCB(entity="features", page=1, parent_id="p1")
    state = _make_state()

    with patch("handler.v1.user.wizard.main_widget._feature_api") as api:
        api.get_all = AsyncMock(return_value=[
            {"id": "f1", "name": "F1", "status": "draft"},
        ])
        await handle_page(cb, cb_data, state)

    cb.message.edit_text.assert_awaited()


# ═══════════════════════════════════════════════════════════
# Keyboard helpers
# ═══════════════════════════════════════════════════════════


def test_summary_kb_only_next():
    from handler.v1.user.wizard.main_widget import _summary_kb

    kb = _summary_kb()
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert texts == ["➡️ Далее"]


def test_summary_kb_uses_plain_callback_data():
    """Далее uses F.data == 'wizard_next', not WizardCB."""
    from handler.v1.user.wizard.main_widget import _summary_kb

    kb = _summary_kb()
    data = kb.inline_keyboard[0][0].callback_data
    assert data == "wizard_next"


def test_send_long_splits():
    from handler.v1.user.wizard.main_widget import _send_long

    chunks = _send_long("A" * 5000, limit=4000)
    assert len(chunks) == 2
    assert len(chunks[0]) == 4000


def test_send_long_short():
    from handler.v1.user.wizard.main_widget import _send_long

    assert _send_long("Hi") == ["Hi"]


# ═══════════════════════════════════════════════════════════
# OpenAI prompt checks
# ═══════════════════════════════════════════════════════════


def test_system_prompt_no_markdown():
    from service.ai.openai_service import SYSTEM_PROMPT

    assert "markdown" in SYSTEM_PROMPT.lower() or "asterisk" in SYSTEM_PROMPT.lower()


def test_summary_prompt_client_problem_solution():
    import inspect
    from service.ai.openai_service import OpenAIService

    source = inspect.getsource(OpenAIService.generate_product_summary)
    source_lower = source.lower()
    assert "client" in source_lower
    assert "problem" in source_lower
    assert "solution" in source_lower
    assert "metric" in source_lower


# ═══════════════════════════════════════════════════════════
# Callback data round-trips
# ═══════════════════════════════════════════════════════════


def test_wizard_cb_roundtrip():
    cb = WizardCB(action="next", ctx="test")
    assert WizardCB.unpack(cb.pack()).action == "next"


def test_product_cb_roundtrip():
    cb = ProductCB(id="123", action="view")
    u = ProductCB.unpack(cb.pack())
    assert u.id == "123" and u.action == "view"


def test_page_cb_roundtrip():
    cb = PageCB(entity="features", page=3, parent_id="p1")
    u = PageCB.unpack(cb.pack())
    assert u.entity == "features" and u.page == 3 and u.parent_id == "p1"


def test_menu_cb_roundtrip():
    cb = MenuCB(action="products")
    assert MenuCB.unpack(cb.pack()).action == "products"


# ═══════════════════════════════════════════════════════════
# FSM states
# ═══════════════════════════════════════════════════════════


def test_fsm_has_required_states():
    states = [s.state for s in ProductFSM.__all_states__]
    for name in ("waiting_for_name", "waiting_for_description",
                 "reviewing_summary", "reviewing_features"):
        assert any(name in s for s in states), f"Missing state: {name}"
