"""Tests for the main wizard flow: /start → name → description → summary → next.

## Traceability
Feature: F001 — Product Management (Wizard Flow)
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Message, CallbackQuery, Chat, User

from state.product_state import ProductFSM
from callback.navigation_cb import MenuCB, WizardCB, ProductCB


# ─── Helpers ────────────────────────────────────────────────


def _make_message(text: str = "", voice: bool = False) -> MagicMock:
    msg = MagicMock(spec=Message)
    msg.text = text
    msg.voice = MagicMock() if voice else None
    msg.audio = None
    msg.answer = AsyncMock(return_value=MagicMock(edit_text=AsyncMock()))
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
    return cb


def _make_state(data: dict = None, current_state: str = None) -> AsyncMock:
    state = AsyncMock()
    state.get_data = AsyncMock(return_value=data or {})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    state.get_state = AsyncMock(return_value=current_state)
    return state


# ─── /start ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_no_products_starts_wizard():
    """When user has no products, /start should prompt for product name."""
    from handler.v1.user.wizard.main_widget import cmd_start

    msg = _make_message("/start")
    state = _make_state()

    with patch("handler.v1.user.wizard.main_widget._product_api") as api:
        api.get_all = AsyncMock(return_value=[])
        await cmd_start(msg, state)

    state.set_state.assert_awaited_once_with(ProductFSM.waiting_for_name)
    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "название продукта" in text.lower() or "название" in text.lower()


@pytest.mark.asyncio
async def test_start_with_products_shows_list():
    """When user has products, /start should show product buttons."""
    from handler.v1.user.wizard.main_widget import cmd_start

    products = [{"id": "1", "name": "Prod A"}, {"id": "2", "name": "Prod B"}]
    msg = _make_message("/start")
    state = _make_state()

    with patch("handler.v1.user.wizard.main_widget._product_api") as api:
        api.get_all = AsyncMock(return_value=products)
        await cmd_start(msg, state)

    msg.answer.assert_awaited_once()
    call_kwargs = msg.answer.call_args
    assert call_kwargs[1].get("reply_markup") is not None


@pytest.mark.asyncio
async def test_start_api_failure_starts_wizard():
    """When API is unreachable, /start treats it as empty list."""
    from handler.v1.user.wizard.main_widget import cmd_start

    msg = _make_message("/start")
    state = _make_state()

    with patch("handler.v1.user.wizard.main_widget._product_api") as api:
        api.get_all = AsyncMock(side_effect=Exception("Connection refused"))
        await cmd_start(msg, state)

    state.set_state.assert_awaited_once_with(ProductFSM.waiting_for_name)


# ─── Name step ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_product_name_saves_and_asks_description():
    """After entering name, bot stores it and asks for description."""
    from handler.v1.user.wizard.main_widget import handle_product_name

    msg = _make_message("My Product")
    state = _make_state()

    await handle_product_name(msg, state)

    state.update_data.assert_awaited_once_with(product_name="My Product")
    state.set_state.assert_awaited_once_with(ProductFSM.waiting_for_description)
    text = msg.answer.call_args[0][0]
    assert "My Product" in text


# ─── Description step ───────────────────────────────────────


@pytest.mark.asyncio
async def test_description_text_generates_summary():
    """Text description triggers GPT summary generation."""
    from handler.v1.user.wizard.main_widget import handle_product_description

    msg = _make_message("A tool for managing tasks")
    wait_msg = MagicMock()
    wait_msg.edit_text = AsyncMock()
    msg.answer = AsyncMock(return_value=wait_msg)
    state = _make_state(data={"product_name": "TaskMgr"})
    bot = MagicMock()

    with patch("handler.v1.user.wizard.main_widget._ai") as ai, \
         patch("handler.v1.user.wizard.main_widget.get_text_or_voice", new=AsyncMock(return_value="A tool for managing tasks")):
        ai.generate_product_summary = AsyncMock(return_value="Client: teams\nProblem: chaos\nSolution: organize")
        await handle_product_description(msg, state, bot)

    state.update_data.assert_any_await(product_summary="Client: teams\nProblem: chaos\nSolution: organize")
    state.set_state.assert_awaited_once_with(ProductFSM.reviewing_summary)
    wait_msg.edit_text.assert_awaited()


@pytest.mark.asyncio
async def test_description_voice_transcribes_and_generates_summary():
    """Voice description is transcribed then used for GPT summary."""
    from handler.v1.user.wizard.main_widget import handle_product_description

    msg = _make_message(voice=True)
    msg.text = None
    wait_msg = MagicMock()
    wait_msg.edit_text = AsyncMock()
    msg.answer = AsyncMock(return_value=wait_msg)
    state = _make_state(data={"product_name": "VoiceProd"})
    bot = MagicMock()

    with patch("handler.v1.user.wizard.main_widget._ai") as ai, \
         patch("handler.v1.user.wizard.main_widget.get_text_or_voice", new=AsyncMock(return_value="transcribed text")):
        ai.generate_product_summary = AsyncMock(return_value="Summary text here")
        await handle_product_description(msg, state, bot)

    state.update_data.assert_any_await(product_description="transcribed text")
    state.set_state.assert_awaited_once_with(ProductFSM.reviewing_summary)


@pytest.mark.asyncio
async def test_description_empty_rejects():
    """Empty input should ask user to retry."""
    from handler.v1.user.wizard.main_widget import handle_product_description

    msg = _make_message("")
    msg.voice = None
    msg.audio = None
    state = _make_state(data={"product_name": "Test"})
    bot = MagicMock()

    with patch("handler.v1.user.wizard.main_widget.get_text_or_voice", new=AsyncMock(return_value="")):
        await handle_product_description(msg, state, bot)

    msg.answer.assert_awaited_once()
    state.set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_description_gpt_error_shows_warning():
    """GPT failure should show error message."""
    from handler.v1.user.wizard.main_widget import handle_product_description

    msg = _make_message("desc")
    wait_msg = MagicMock()
    wait_msg.edit_text = AsyncMock()
    msg.answer = AsyncMock(return_value=wait_msg)
    state = _make_state(data={"product_name": "Test"})
    bot = MagicMock()

    with patch("handler.v1.user.wizard.main_widget._ai") as ai, \
         patch("handler.v1.user.wizard.main_widget.get_text_or_voice", new=AsyncMock(return_value="desc")):
        ai.generate_product_summary = AsyncMock(side_effect=Exception("GPT timeout"))
        await handle_product_description(msg, state, bot)

    error_text = wait_msg.edit_text.call_args[0][0]
    assert "GPT timeout" in error_text


# ─── Summary review — edit via text/voice ────────────────────


@pytest.mark.asyncio
async def test_reviewing_summary_text_edits_summary():
    """Sending text in reviewing_summary state applies edit."""
    from handler.v1.user.wizard.main_widget import handle_summary_edit_input

    msg = _make_message("Remove the second point")
    wait_msg = MagicMock()
    wait_msg.edit_text = AsyncMock()
    msg.answer = AsyncMock(return_value=wait_msg)
    state = _make_state(data={
        "product_name": "MyProd",
        "product_summary": "Old summary text",
    })
    bot = MagicMock()

    with patch("handler.v1.user.wizard.main_widget._ai") as ai, \
         patch("handler.v1.user.wizard.main_widget.get_text_or_voice", new=AsyncMock(return_value="Remove the second point")):
        ai.edit_text = AsyncMock(return_value="Updated summary text")
        await handle_summary_edit_input(msg, state, bot)

    state.update_data.assert_awaited_with(product_summary="Updated summary text")
    text = wait_msg.edit_text.call_args[0][0]
    assert "Updated summary text" in text


@pytest.mark.asyncio
async def test_reviewing_summary_empty_rejects():
    """Empty input while reviewing should prompt retry."""
    from handler.v1.user.wizard.main_widget import handle_summary_edit_input

    msg = _make_message("")
    state = _make_state(data={"product_name": "X", "product_summary": "S"})
    bot = MagicMock()

    with patch("handler.v1.user.wizard.main_widget.get_text_or_voice", new=AsyncMock(return_value="")):
        await handle_summary_edit_input(msg, state, bot)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "текст" in text.lower() or "голосовое" in text.lower()


# ─── Next button (WizardCB action=next) ─────────────────────


@pytest.mark.asyncio
async def test_next_button_saves_product_and_generates_features():
    """Pressing Next saves product to backend and generates features."""
    from handler.v1.user.wizard.main_widget import handle_wizard_cb

    cb = _make_callback(WizardCB(action="next").pack())
    cb_data = WizardCB(action="next")
    state = _make_state(
        data={
            "product_name": "MyProd",
            "product_summary": "Summary",
        },
        current_state=ProductFSM.reviewing_summary.state,
    )

    with patch("handler.v1.user.wizard.main_widget._product_api") as p_api, \
         patch("handler.v1.user.wizard.main_widget._feature_api") as f_api, \
         patch("handler.v1.user.wizard.main_widget._ai") as ai:
        p_api.create = AsyncMock(return_value={"id": "prod-1", "name": "MyProd"})
        ai.generate_features_json = AsyncMock(return_value=[
            {"name": "Auth", "description": "User authentication"},
            {"name": "Dashboard", "description": "Main dashboard"},
        ])
        f_api.create = AsyncMock(side_effect=[
            {"id": "f1", "name": "Auth", "description": "User authentication"},
            {"id": "f2", "name": "Dashboard", "description": "Main dashboard"},
        ])
        await handle_wizard_cb(cb, cb_data, state)

    p_api.create.assert_awaited_once()
    state.set_state.assert_awaited_with(ProductFSM.reviewing_features)
    cb.answer.assert_awaited()


@pytest.mark.asyncio
async def test_next_button_wrong_action_ignored():
    """WizardCB with action != 'next' should be ignored."""
    from handler.v1.user.wizard.main_widget import handle_wizard_cb

    cb = _make_callback(WizardCB(action="edit").pack())
    cb_data = WizardCB(action="edit")
    state = _make_state(current_state=ProductFSM.reviewing_summary.state)

    await handle_wizard_cb(cb, cb_data, state)

    cb.answer.assert_awaited()
    state.set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_next_button_api_error_shows_message():
    """If product creation fails, show error."""
    from handler.v1.user.wizard.main_widget import handle_wizard_cb

    cb = _make_callback(WizardCB(action="next").pack())
    cb_data = WizardCB(action="next")
    state = _make_state(
        data={"product_name": "X", "product_summary": "S"},
        current_state=ProductFSM.reviewing_summary.state,
    )

    with patch("handler.v1.user.wizard.main_widget._product_api") as p_api:
        p_api.create = AsyncMock(side_effect=Exception("DB error"))
        await handle_wizard_cb(cb, cb_data, state)

    error_text = cb.message.edit_text.call_args[0][0]
    assert "DB error" in error_text


# ─── Menu callbacks ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_menu_products_shows_list():
    """Menu 'products' action shows product list."""
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
async def test_menu_create_product_starts_wizard():
    """Menu 'create_product' action enters name step."""
    from handler.v1.user.wizard.main_widget import handle_menu

    cb = _make_callback(MenuCB(action="create_product").pack())
    cb_data = MenuCB(action="create_product")
    state = _make_state()

    await handle_menu(cb, cb_data, state)

    state.set_state.assert_awaited_once_with(ProductFSM.waiting_for_name)
    cb.message.edit_text.assert_awaited()


# ─── Product view callbacks ─────────────────────────────────


@pytest.mark.asyncio
async def test_product_view_shows_detail():
    """ProductCB action='view' shows product details."""
    from handler.v1.user.wizard.main_widget import handle_product

    cb = _make_callback(ProductCB(id="1", action="view").pack())
    cb_data = ProductCB(id="1", action="view")
    state = _make_state()

    with patch("handler.v1.user.wizard.main_widget._product_api") as api:
        api.get_by_id = AsyncMock(return_value={
            "id": "1", "name": "TestProd", "status": "draft", "version": 1, "goal": "A goal",
        })
        await handle_product(cb, cb_data, state)

    cb.message.edit_text.assert_awaited()
    text = cb.message.edit_text.call_args[0][0]
    assert "TestProd" in text


@pytest.mark.asyncio
async def test_product_next_shows_features():
    """ProductCB action='next' shows feature list."""
    from handler.v1.user.wizard.main_widget import handle_product

    cb = _make_callback(ProductCB(id="1", action="next").pack())
    cb_data = ProductCB(id="1", action="next")
    state = _make_state()

    with patch("handler.v1.user.wizard.main_widget._feature_api") as api:
        api.get_all = AsyncMock(return_value=[
            {"id": "f1", "name": "Feature A", "status": "draft"},
        ])
        await handle_product(cb, cb_data, state)

    cb.message.edit_text.assert_awaited()


# ─── Keyboard helpers ───────────────────────────────────────


def test_summary_kb_has_only_next_button():
    """Summary keyboard should have only the Next button, no Edit."""
    from handler.v1.user.wizard.main_widget import _summary_kb

    kb = _summary_kb()
    buttons = []
    for row in kb.inline_keyboard:
        for btn in row:
            buttons.append(btn.text)

    assert "➡️ Далее" in buttons
    assert "✏️ Редактировать" not in buttons
    assert len(buttons) == 1


def test_products_kb_has_create_button():
    """Product keyboard should have Create button."""
    from handler.v1.user.wizard.main_widget import _products_kb

    kb = _products_kb([{"id": "1", "name": "P1"}])
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert "📦 P1" in texts
    assert "➕ Создать продукт" in texts


def test_send_long_splits_text():
    """_send_long should split text exceeding limit."""
    from handler.v1.user.wizard.main_widget import _send_long

    chunks = _send_long("A" * 5000, limit=4000)
    assert len(chunks) == 2
    assert len(chunks[0]) == 4000
    assert len(chunks[1]) == 1000


def test_send_long_short_text():
    """_send_long should return single chunk for short text."""
    from handler.v1.user.wizard.main_widget import _send_long

    chunks = _send_long("Hello", limit=4000)
    assert chunks == ["Hello"]


# ─── OpenAI service ─────────────────────────────────────────


def test_system_prompt_no_markdown():
    """SYSTEM_PROMPT should instruct GPT not to use markdown."""
    from service.ai.openai_service import SYSTEM_PROMPT

    assert "**" in SYSTEM_PROMPT or "asterisk" in SYSTEM_PROMPT.lower() or "markdown" in SYSTEM_PROMPT.lower()


def test_summary_prompt_has_client_problem_solution():
    """generate_product_summary prompt should use client-problem-solution format."""
    import inspect
    from service.ai.openai_service import OpenAIService

    source = inspect.getsource(OpenAIService.generate_product_summary)
    assert "Client" in source or "client" in source
    assert "Problem" in source or "problem" in source
    assert "Solution" in source or "solution" in source
    assert "metric" in source.lower()
    # Should NOT require constraints
    assert "constraint" not in source.lower() or "no constraint" in source.lower()


# ─── Callback data ──────────────────────────────────────────


def test_wizard_cb_pack_unpack():
    """WizardCB should round-trip pack/unpack correctly."""
    cb = WizardCB(action="next", ctx="test")
    packed = cb.pack()
    unpacked = WizardCB.unpack(packed)
    assert unpacked.action == "next"
    assert unpacked.ctx == "test"


def test_product_cb_pack_unpack():
    """ProductCB should round-trip correctly."""
    cb = ProductCB(id="123", action="view")
    packed = cb.pack()
    unpacked = ProductCB.unpack(packed)
    assert unpacked.id == "123"
    assert unpacked.action == "view"


def test_menu_cb_pack_unpack():
    """MenuCB should round-trip correctly."""
    cb = MenuCB(action="products")
    packed = cb.pack()
    unpacked = MenuCB.unpack(packed)
    assert unpacked.action == "products"


# ─── FSM states ─────────────────────────────────────────────


def test_product_fsm_has_required_states():
    """ProductFSM should define all wizard states."""
    states = [s.state for s in ProductFSM.__all_states__]
    assert any("waiting_for_name" in s for s in states)
    assert any("waiting_for_description" in s for s in states)
    assert any("reviewing_summary" in s for s in states)
    assert any("reviewing_features" in s for s in states)
