"""Main wizard: single-message UI with pagination and cascading drill-down.

Flow:
  /start → product list (buttons) or create wizard
  Create: name → description (text/voice/file) → GPT summary → review (edit by typing) → Далее
  → features generated as TEXT LIST → review/edit by typing → Далее → saved as buttons
  → click feature → stories as TEXT LIST → review/edit → Далее → saved as buttons
  → etc.

Key rules:
  - ONE bot message, always edited in-place
  - User messages deleted instantly
  - Pagination: always 3 buttons [◀️] [page/total] [▶️]
  - Max 5 items per page
  - Text/voice editing at every review step
  - Items saved to backend only after "Далее"

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

import json
import math
import logging

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from state.product_state import ProductFSM
from callback.navigation_cb import (
    MenuCB, ProductCB, FeatureCB, RoleCB, StoryCB, FlowCB, UseCaseCB,
    WizardCB, PageCB,
)
from service.ai.openai_service import OpenAIService
from service.api.product_api import ProductAPI
from service.api.feature_api import FeatureAPI
from service.api.story_api import StoryAPI
from service.api.flow_api import FlowAPI
from service.api.use_case_api import UseCaseAPI
from service.api.actor_api import ActorAPI
from service.api.feature_actor_link_api import FeatureActorLinkAPI
from service.api.requirement_api import RequirementAPI
from service.voice import get_text_or_voice

log = logging.getLogger(__name__)
router = Router(name="wizard_main")

_ai = OpenAIService()
_product_api = ProductAPI()
_feature_api = FeatureAPI()
_story_api = StoryAPI()
_flow_api = FlowAPI()
_use_case_api = UseCaseAPI()
_actor_api = ActorAPI()
_feature_actor_link_api = FeatureActorLinkAPI()
_requirement_api = RequirementAPI()

PER_PAGE = 5


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════


def _page_row(entity: str, page: int, total_pages: int,
              parent_id: str = "") -> list[InlineKeyboardButton]:
    """Always 3 buttons: ◀️  page/total  ▶️. Disabled arrows use noop."""
    if total_pages <= 1:
        return []
    left_cb = (
        PageCB(entity=entity, page=page - 1, parent_id=parent_id).pack()
        if page > 1 else "noop"
    )
    right_cb = (
        PageCB(entity=entity, page=page + 1, parent_id=parent_id).pack()
        if page < total_pages else "noop"
    )
    return [
        InlineKeyboardButton(text="◀️" if page > 1 else "·", callback_data=left_cb),
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"),
        InlineKeyboardButton(text="▶️" if page < total_pages else "·", callback_data=right_cb),
    ]


def _nav_kb(back_text: str, back_cb: str,
            show_next: bool = False, next_cb: str = "wizard_next") -> list[list[InlineKeyboardButton]]:
    """Bottom row: ◀️ Назад [➡️ Далее]."""
    row = [InlineKeyboardButton(text=f"◀️ {back_text}", callback_data=back_cb)]
    if show_next:
        row.append(InlineKeyboardButton(text="➡️ Далее", callback_data=next_cb))
    return [row]


def _products_kb(products: list[dict], page: int = 1) -> InlineKeyboardMarkup:
    """Paginated product buttons (already saved)."""
    total = math.ceil(len(products) / PER_PAGE) or 1
    page = max(1, min(page, total))
    start = (page - 1) * PER_PAGE
    subset = products[start:start + PER_PAGE]

    rows = []
    for p in subset:
        rows.append([InlineKeyboardButton(
            text=f"📦 {p['name']}",
            callback_data=ProductCB(id=str(p["id"]), action="view").pack(),
        )])
    nav = _page_row("products", page, total)
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(
        text="➕ Создать продукт",
        callback_data=MenuCB(action="create_product").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _saved_features_kb(features: list[dict], product_id: str,
                       page: int = 1) -> InlineKeyboardMarkup:
    """Paginated feature BUTTONS (after Далее saved them)."""
    total = math.ceil(len(features) / PER_PAGE) or 1
    page = max(1, min(page, total))
    start = (page - 1) * PER_PAGE
    subset = features[start:start + PER_PAGE]

    rows = []
    for feat in subset:
        icon = "✅" if feat.get("status") == "approved" else "📝"
        rows.append([InlineKeyboardButton(
            text=f"{icon} {feat['name']}",
            callback_data=FeatureCB(id=str(feat["id"]), action="view").pack(),
        )])
    nav = _page_row("features", page, total, parent_id=product_id)
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(
        text="◀️ Назад",
        callback_data=ProductCB(id=product_id, action="view").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _review_kb(back_cb: str, next_cb: str,
               back_text: str = "Назад") -> InlineKeyboardMarkup:
    """Review screen: Назад + Далее. User edits by typing."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"◀️ {back_text}", callback_data=back_cb),
            InlineKeyboardButton(text="➡️ Далее", callback_data=next_cb),
        ],
    ])


def _saved_stories_kb(stories: list[dict], feature_id: str,
                      page: int = 1) -> InlineKeyboardMarkup:
    """Paginated story BUTTONS (after Далее saved them)."""
    total = math.ceil(len(stories) / PER_PAGE) or 1
    page = max(1, min(page, total))
    start = (page - 1) * PER_PAGE
    subset = stories[start:start + PER_PAGE]

    rows = []
    for s in subset:
        icon = "✅" if s.get("status") == "approved" else "📝"
        rows.append([InlineKeyboardButton(
            text=f"{icon} {s['title'][:40]}",
            callback_data=StoryCB(id=str(s["id"]), action="view").pack(),
        )])
    nav = _page_row("stories", page, total, parent_id=feature_id)
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(
        text="◀️ Назад к фичам",
        callback_data=FeatureCB(id=feature_id, action="back").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _saved_roles_kb(roles: list[dict], feature_id: str,
                    page: int = 1) -> InlineKeyboardMarkup:
    """Paginated role/actor BUTTONS."""
    total = math.ceil(len(roles) / PER_PAGE) or 1
    page = max(1, min(page, total))
    start = (page - 1) * PER_PAGE
    subset = roles[start:start + PER_PAGE]

    rows = []
    for r in subset:
        icon = "✅" if r.get("status") == "approved" else "👤"
        rt = r.get("role_type", "end_user")
        rows.append([InlineKeyboardButton(
            text=f"{icon} {r.get('name', 'Role')[:35]} ({rt})",
            callback_data=RoleCB(id=str(r["id"]), action="view").pack(),
        )])
    nav = _page_row("roles", page, total, parent_id=feature_id)
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(
        text="◀️ Назад к фичам",
        callback_data=FeatureCB(id=feature_id, action="back").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _saved_flows_kb(flows: list[dict], story_id: str,
                    page: int = 1) -> InlineKeyboardMarkup:
    """Paginated flow BUTTONS."""
    total = math.ceil(len(flows) / PER_PAGE) or 1
    page = max(1, min(page, total))
    start = (page - 1) * PER_PAGE
    subset = flows[start:start + PER_PAGE]

    rows = []
    for f in subset:
        icon = "✅" if f.get("status") == "approved" else "🔄"
        ft = f.get("flow_type", "primary")
        rows.append([InlineKeyboardButton(
            text=f"{icon} {f.get('title', 'Flow')[:35]} ({ft})",
            callback_data=FlowCB(id=str(f["id"]), action="view").pack(),
        )])
    nav = _page_row("flows", page, total, parent_id=story_id)
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(
        text="◀️ Назад к stories",
        callback_data=StoryCB(id=story_id, action="view").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _saved_use_cases_kb(use_cases: list[dict], story_id: str,
                        page: int = 1) -> InlineKeyboardMarkup:
    """Paginated use case BUTTONS."""
    total = math.ceil(len(use_cases) / PER_PAGE) or 1
    page = max(1, min(page, total))
    start = (page - 1) * PER_PAGE
    subset = use_cases[start:start + PER_PAGE]

    rows = []
    for u in subset:
        icon = "✅" if u.get("status") == "approved" else "📋"
        rows.append([InlineKeyboardButton(
            text=f"{icon} {u.get('title', 'UC')[:40]}",
            callback_data=UseCaseCB(id=str(u["id"]), action="view").pack(),
        )])
    nav = _page_row("use_cases", page, total, parent_id=story_id)
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(
        text="◀️ Назад к flows",
        callback_data=StoryCB(id=story_id, action="flows").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _format_features_text(features: list[dict]) -> str:
    """Format features as numbered text list with full descriptions."""
    lines = []
    for i, f in enumerate(features, 1):
        lines.append(f"{i}. <b>{f['name']}</b>")
        if f.get("description"):
            lines.append(f"   {f['description']}")
        lines.append("")  # blank line between features
    return "\n".join(lines).rstrip()


def _format_roles_text(roles: list[dict]) -> str:
    """Format roles as numbered text list."""
    lines = []
    for i, r in enumerate(roles, 1):
        rt = r.get("role_type", "end_user")
        lines.append(f"{i}. <b>{r.get('name', 'Role')}</b> ({rt})")
        if r.get("description"):
            lines.append(f"   {r['description']}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_stories_text(stories: list[dict]) -> str:
    """Format stories as numbered text list."""
    lines = []
    for i, s in enumerate(stories, 1):
        lines.append(f"{i}. <b>{s.get('title', 'Story')}</b>")
        if s.get("want"):
            lines.append(f"   Хочу: {s['want']}")
        if s.get("benefit"):
            lines.append(f"   Чтобы: {s['benefit']}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_flows_text(flows: list[dict]) -> str:
    """Format flows as numbered list with mermaid diagrams."""
    lines = []
    for i, f in enumerate(flows, 1):
        ft = f.get("flow_type", "primary")
        lines.append(f"{i}. <b>{f.get('title', 'Flow')}</b> ({ft})")
        if f.get("description"):
            lines.append(f"   {f['description']}")
        if f.get("mermaid_source"):
            lines.append(f"\n<pre>{f['mermaid_source']}</pre>")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_use_cases_text(use_cases: list[dict]) -> str:
    """Format use cases as numbered Given/When/Then list."""
    lines = []
    for i, uc in enumerate(use_cases, 1):
        lines.append(f"{i}. <b>{uc.get('title', 'Use Case')}</b>")
        if uc.get("goal"):
            lines.append(f"   Цель: {uc['goal']}")
        if uc.get("given_text"):
            lines.append(f"   Given: {uc['given_text']}")
        if uc.get("when_text"):
            lines.append(f"   When: {uc['when_text']}")
        if uc.get("then_text"):
            lines.append(f"   Then: {uc['then_text']}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_requirements_text(reqs: list[dict]) -> str:
    """Format requirements as numbered list with type and priority."""
    lines = []
    for i, r in enumerate(reqs, 1):
        rt = r.get("requirement_type", "functional")
        pr = r.get("priority", "medium")
        lines.append(f"{i}. <b>{r.get('title', 'Req')}</b> [{rt}] ({pr})")
        if r.get("text"):
            lines.append(f"   {r['text']}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _send_long(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:limit])
        text = text[limit:]
    return chunks


async def _delete_user_msg(message: Message) -> None:
    try:
        await message.delete()
    except Exception:
        pass


async def _send_or_edit(message: Message, state: FSMContext, text: str,
                        reply_markup: InlineKeyboardMarkup = None) -> None:
    """Edit tracked bot message or send new one."""
    data = await state.get_data()
    bot_msg_id = data.get("bot_msg_id")

    if bot_msg_id:
        try:
            bot = message.bot
            await bot.edit_message_text(
                text=text, chat_id=message.chat.id, message_id=bot_msg_id,
                reply_markup=reply_markup, parse_mode="HTML",
            )
            return
        except Exception:
            pass

    sent = await message.answer(text, reply_markup=reply_markup)
    await state.update_data(bot_msg_id=sent.message_id)


async def _edit_cb_msg(callback: CallbackQuery, text: str,
                       reply_markup: InlineKeyboardMarkup = None) -> None:
    try:
        await callback.message.edit_text(
            text, reply_markup=reply_markup, parse_mode="HTML",
        )
    except Exception as exc:
        log.warning("edit_cb_msg failed: %s", exc)
        # If edit fails (e.g. text unchanged), try sending new message
        try:
            await callback.message.answer(
                text, reply_markup=reply_markup, parse_mode="HTML",
            )
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# /start — Product list
# ═══════════════════════════════════════════════════════════


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _delete_user_msg(message)

    try:
        products = await _product_api.get_all()
    except Exception:
        products = []

    if products:
        sent = await message.answer(
            "📦 <b>Ваши продукты:</b>",
            reply_markup=_products_kb(products, page=1),
        )
        await state.update_data(bot_msg_id=sent.message_id)
    else:
        sent = await message.answer(
            "👋 Добро пожаловать!\n\nУ вас пока нет продуктов.\n"
            "Давайте создадим первый — введите <b>название продукта</b>:"
        )
        await state.update_data(bot_msg_id=sent.message_id)
        await state.set_state(ProductFSM.waiting_for_name)


# ═══════════════════════════════════════════════════════════
# Pagination
# ═══════════════════════════════════════════════════════════


@router.callback_query(PageCB.filter())
async def handle_page(callback: CallbackQuery, callback_data: PageCB,
                      state: FSMContext) -> None:
    entity = callback_data.entity
    raw_page = callback_data.page
    pid = callback_data.parent_id

    if entity == "products":
        try:
            products = await _product_api.get_all()
        except Exception:
            products = []
        total = math.ceil(len(products) / PER_PAGE) or 1
        page = max(1, min(raw_page, total))
        await _edit_cb_msg(callback, f"📦 <b>Ваши продукты</b> ({page}/{total}):",
                           reply_markup=_products_kb(products, page=page))

    elif entity == "features":
        try:
            features = await _feature_api.get_all(product_id=pid)
        except Exception:
            features = []
        total = math.ceil(len(features) / PER_PAGE) or 1
        page = max(1, min(raw_page, total))
        text = f"📋 <b>Фичи</b> ({page}/{total}):\n\n" + _format_features_text(features)
        await _edit_cb_msg(callback, text,
                           reply_markup=_saved_features_kb(features, pid, page=page))

    elif entity == "roles":
        try:
            links = await _feature_actor_link_api.get_all(feature_id=pid)
            roles = []
            for lnk in links:
                try:
                    actor = await _actor_api.get_by_id(lnk["actor_id"])
                    roles.append(actor)
                except Exception:
                    pass
        except Exception:
            roles = []
        total = math.ceil(len(roles) / PER_PAGE) or 1
        page = max(1, min(raw_page, total))
        text = f"👤 <b>Роли</b> ({page}/{total}):"
        await _edit_cb_msg(callback, text,
                           reply_markup=_saved_roles_kb(roles, pid, page=page))

    elif entity == "stories":
        try:
            stories = await _story_api.get_all(feature_id=pid)
        except Exception:
            stories = []
        total = math.ceil(len(stories) / PER_PAGE) or 1
        page = max(1, min(raw_page, total))
        text = f"📖 <b>User Stories</b> ({page}/{total}):"
        await _edit_cb_msg(callback, text,
                           reply_markup=_saved_stories_kb(stories, pid, page=page))

    elif entity == "flows":
        try:
            flows = await _flow_api.get_all(story_id=pid)
        except Exception:
            flows = []
        total = math.ceil(len(flows) / PER_PAGE) or 1
        page = max(1, min(raw_page, total))
        text = f"🔄 <b>User Flows</b> ({page}/{total}):"
        await _edit_cb_msg(callback, text,
                           reply_markup=_saved_flows_kb(flows, pid, page=page))

    elif entity == "use_cases":
        try:
            ucs = await _use_case_api.get_all(story_id=pid)
        except Exception:
            ucs = []
        total = math.ceil(len(ucs) / PER_PAGE) or 1
        page = max(1, min(raw_page, total))
        text = f"📋 <b>Use Cases</b> ({page}/{total}):"
        await _edit_cb_msg(callback, text,
                           reply_markup=_saved_use_cases_kb(ucs, pid, page=page))

    await callback.answer()


@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery) -> None:
    await callback.answer()


# ═══════════════════════════════════════════════════════════
# Menu callbacks
# ═══════════════════════════════════════════════════════════


@router.callback_query(MenuCB.filter())
async def handle_menu(callback: CallbackQuery, callback_data: MenuCB,
                      state: FSMContext) -> None:
    if callback_data.action == "products":
        await state.clear()
        try:
            products = await _product_api.get_all()
        except Exception:
            products = []
        await _edit_cb_msg(
            callback,
            "📦 <b>Ваши продукты:</b>" if products else "Продуктов пока нет.",
            reply_markup=_products_kb(products, page=1),
        )
        await state.update_data(bot_msg_id=callback.message.message_id)

    elif callback_data.action == "create_product":
        await _edit_cb_msg(callback, "Введите <b>название продукта</b>:")
        await state.update_data(bot_msg_id=callback.message.message_id)
        await state.set_state(ProductFSM.waiting_for_name)

    await callback.answer()


# ═══════════════════════════════════════════════════════════
# Create product wizard: name → description → summary
# ═══════════════════════════════════════════════════════════


@router.message(ProductFSM.waiting_for_name, F.text)
async def handle_product_name(message: Message, state: FSMContext) -> None:
    name = message.text
    await _delete_user_msg(message)
    await state.update_data(product_name=name)
    await state.set_state(ProductFSM.waiting_for_description)
    await _send_or_edit(
        message, state,
        f"Продукт: <b>{name}</b>\n\n"
        "Теперь опишите продукт — <b>текстом, голосовым или файлом</b>:",
    )


@router.message(ProductFSM.waiting_for_description)
async def handle_product_description(message: Message, state: FSMContext,
                                     bot: Bot) -> None:
    text = await get_text_or_voice(message, bot)
    # Also handle document with text content
    if not text and message.document:
        try:
            file = await bot.get_file(message.document.file_id)
            import tempfile, os
            tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
            await bot.download_file(file.file_path, tmp.name)
            with open(tmp.name, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()[:8000]
            os.unlink(tmp.name)
        except Exception:
            pass

    await _delete_user_msg(message)
    if not text:
        await _send_or_edit(message, state,
                            "Пожалуйста, отправьте текст, голосовое или файл.")
        return

    await state.update_data(product_description=text)
    data = await state.get_data()
    name = data["product_name"]

    await _send_or_edit(message, state, "⏳ Генерирую саммери...")

    try:
        summary = await _ai.generate_product_summary(name, text)
    except Exception as exc:
        await _send_or_edit(message, state, f"⚠️ Ошибка GPT: {exc}")
        return

    await state.update_data(product_summary=summary)
    await state.set_state(ProductFSM.reviewing_summary)

    display = f"📋 <b>Саммери продукта «{name}»:</b>\n\n{summary}"
    await _send_or_edit(
        message, state, display,
        reply_markup=_review_kb(
            back_cb=MenuCB(action="products").pack(),
            next_cb="wizard_next",
            back_text="Отмена",
        ),
    )


# ═══════════════════════════════════════════════════════════
# Summary review — edit by typing text/voice
# ═══════════════════════════════════════════════════════════


@router.message(ProductFSM.reviewing_summary)
async def handle_summary_edit(message: Message, state: FSMContext,
                              bot: Bot) -> None:
    instruction = await get_text_or_voice(message, bot)
    await _delete_user_msg(message)
    if not instruction:
        return

    data = await state.get_data()
    await _send_or_edit(message, state, "⏳ Применяю правки...")

    try:
        new_summary = await _ai.edit_text(data["product_summary"], instruction)
    except Exception as exc:
        await _send_or_edit(message, state, f"⚠️ Ошибка: {exc}")
        return

    await state.update_data(product_summary=new_summary)
    name = data["product_name"]
    await _send_or_edit(
        message, state,
        f"📋 <b>Обновлённое саммери «{name}»:</b>\n\n{new_summary}",
        reply_markup=_review_kb(
            back_cb=MenuCB(action="products").pack(),
            next_cb="wizard_next",
            back_text="Отмена",
        ),
    )


# ═══════════════════════════════════════════════════════════
# wizard_next — save product, generate features as TEXT
# ═══════════════════════════════════════════════════════════


@router.callback_query(F.data == "wizard_next")
async def handle_wizard_next(callback: CallbackQuery,
                             state: FSMContext) -> None:
    current = await state.get_state()
    log.info("wizard_next, state=%s", current)

    if current == ProductFSM.reviewing_summary.state:
        data = await state.get_data()
        await _edit_cb_msg(callback, "⏳ Сохраняю продукт и генерирую фичи...")

        # 1. Save product
        try:
            product = await _product_api.create({
                "name": data["product_name"],
                "goal": data.get("product_summary", ""),
            })
            product_id = str(product["id"])
            await state.update_data(product_id=product_id)
        except Exception as exc:
            await _edit_cb_msg(callback, f"⚠️ Ошибка создания: {exc}")
            await callback.answer()
            return

        # 2. Generate features via AI (NOT saved to backend yet)
        try:
            features_data = await _ai.generate_features_json(
                data["product_name"], data.get("product_summary", "")
            )
        except Exception as exc:
            await _edit_cb_msg(callback,
                               f"✅ Продукт создан, но ошибка генерации фичей: {exc}")
            await callback.answer()
            return

        # Store in FSM as draft list — NOT saving to backend yet
        draft_features = []
        for fd in features_data:
            draft_features.append({
                "name": fd["name"],
                "description": fd.get("description", ""),
            })

        await state.update_data(draft_features=draft_features)
        await state.set_state(ProductFSM.reviewing_features)

        text = (
            f"✅ Продукт <b>{data['product_name']}</b> создан!\n\n"
            "📋 <b>Сгенерированные фичи:</b>\n"
            "<i>Можете отредактировать текстом/голосом, затем нажмите Далее</i>\n\n"
            + _format_features_text(draft_features)
        )
        await _edit_cb_msg(
            callback, text,
            reply_markup=_review_kb(
                back_cb=ProductCB(id=product_id, action="view").pack(),
                next_cb="wizard_save_features",
                back_text="Назад",
            ),
        )

    await callback.answer()


# ═══════════════════════════════════════════════════════════
# reviewing_features — edit the TEXT list by typing
# ═══════════════════════════════════════════════════════════


@router.message(ProductFSM.reviewing_features)
async def handle_features_edit(message: Message, state: FSMContext,
                               bot: Bot) -> None:
    """User types text/voice → AI edits the feature list."""
    instruction = await get_text_or_voice(message, bot)
    await _delete_user_msg(message)
    if not instruction:
        return

    data = await state.get_data()
    draft = data.get("draft_features", [])
    await _send_or_edit(message, state, "⏳ Применяю правки к фичам...")

    # Build current list as text for AI
    current_text = "\n".join(
        f"{i}. {f['name']}: {f.get('description', '')}"
        for i, f in enumerate(draft, 1)
    )

    try:
        edited = await _ai.edit_features_list(current_text, instruction)
    except Exception as exc:
        await _send_or_edit(message, state, f"⚠️ Ошибка: {exc}")
        return

    await state.update_data(draft_features=edited)
    product_id = data.get("product_id", "")
    text = (
        "📋 <b>Обновлённые фичи:</b>\n"
        "<i>Можете продолжить редактирование или нажмите Далее</i>\n\n"
        + _format_features_text(edited)
    )
    await _send_or_edit(
        message, state, text,
        reply_markup=_review_kb(
            back_cb=ProductCB(id=product_id, action="view").pack(),
            next_cb="wizard_save_features",
            back_text="Назад",
        ),
    )


# ═══════════════════════════════════════════════════════════
# Cascade helpers
# ═══════════════════════════════════════════════════════════


async def _start_feature_roles(callback: CallbackQuery,
                               state: FSMContext,
                               feature_index: int) -> None:
    """Generate roles TEXT for feature at given index, or finish if all done."""
    data = await state.get_data()
    features = data.get("saved_features", [])
    if feature_index >= len(features):
        # All features fully processed — show features as buttons
        product_id = data.get("product_id", "")
        await state.clear()
        text = "📋 <b>Фичи:</b>\n\n" + _format_features_text(features)
        await _edit_cb_msg(callback, text,
                           reply_markup=_saved_features_kb(features, product_id, page=1))
        return

    feat = features[feature_index]
    fid = str(feat.get("id", ""))
    await state.update_data(
        feature_index=feature_index,
        current_feature_id=fid,
        current_feature_product_id=data.get("product_id", ""),
    )

    await _edit_cb_msg(callback,
                       f"🔹 <b>Фича {feature_index + 1}/{len(features)}: "
                       f"{feat['name']}</b>\n\n⏳ Генерирую роли...")
    try:
        roles_data = await _ai.generate_roles_json(
            feat["name"], feat.get("description", "")
        )
    except Exception as exc:
        await _edit_cb_msg(callback, f"⚠️ Ошибка: {exc}")
        return

    draft = [{"name": r.get("name", "Role"),
              "description": r.get("description", ""),
              "role_type": r.get("role_type", "end_user")}
             for r in roles_data]
    await state.update_data(draft_roles=draft)
    await state.set_state(ProductFSM.reviewing_roles)

    text = (
        f"🔹 <b>Фича {feature_index + 1}/{len(features)}: {feat['name']}</b>\n\n"
        "👤 <b>Роли (Actors):</b>\n"
        "<i>Редактируйте текстом/голосом, затем Далее</i>\n\n"
        + _format_roles_text(draft)
    )
    await _edit_cb_msg(
        callback, text,
        reply_markup=_review_kb(
            back_cb=FeatureCB(id=fid, action="back").pack(),
            next_cb="wizard_save_roles",
        ),
    )


async def _start_role_stories(callback: CallbackQuery,
                               state: FSMContext,
                               role_index: int) -> None:
    """Generate stories TEXT for role at given index, or next feature if all roles done."""
    data = await state.get_data()
    roles = data.get("saved_roles", [])
    if role_index >= len(roles):
        # All roles done for this feature — next feature
        fi = data.get("feature_index", 0) + 1
        await _start_feature_roles(callback, state, fi)
        return

    role = roles[role_index]
    features = data.get("saved_features", [])
    fi = data.get("feature_index", 0)
    feat = features[fi] if fi < len(features) else {"name": "?", "description": ""}
    fid = data.get("current_feature_id", "")

    await state.update_data(
        role_index=role_index,
        current_role_name=role.get("name", ""),
        current_role_id=str(role.get("id", "")),
    )

    await _edit_cb_msg(callback,
                       f"👤 <b>Роль {role_index + 1}/{len(roles)}: "
                       f"{role.get('name', '')}</b>\n\n⏳ Генерирую user stories...")
    try:
        stories_data = await _ai.generate_stories_json(
            feat["name"], feat.get("description", ""),
            role_name=role.get("name", ""),
        )
    except Exception as exc:
        await _edit_cb_msg(callback, f"⚠️ Ошибка: {exc}")
        return

    draft = [{"title": sd.get("title", "Story"),
              "want": sd.get("want", ""),
              "benefit": sd.get("benefit", "")}
             for sd in stories_data]
    await state.update_data(draft_stories=draft)
    await state.set_state(ProductFSM.reviewing_stories)

    text = (
        f"👤 <b>Роль: {role.get('name', '')}</b> | "
        f"Фича: {feat['name']}\n\n"
        "📖 <b>User Stories:</b>\n"
        "<i>Редактируйте текстом/голосом, затем Далее</i>\n\n"
        + _format_stories_text(draft)
    )
    await _edit_cb_msg(
        callback, text,
        reply_markup=_review_kb(
            back_cb=FeatureCB(id=fid, action="back").pack(),
            next_cb="wizard_save_stories",
        ),
    )


async def _start_story_flows(callback: CallbackQuery,
                              state: FSMContext,
                              story_index: int) -> None:
    """Generate flows TEXT for story at given index."""
    data = await state.get_data()
    stories = data.get("saved_stories", [])
    if story_index >= len(stories):
        # All stories done for this role — next role
        ri = data.get("role_index", 0) + 1
        await _start_role_stories(callback, state, ri)
        return

    story = stories[story_index]
    sid = str(story.get("id", ""))
    await state.update_data(
        story_index=story_index,
        current_story_id=sid,
    )

    await _edit_cb_msg(callback,
                       f"📖 <b>Story {story_index + 1}/{len(stories)}: "
                       f"{story.get('title', '')}</b>\n\n⏳ Генерирую user flows...")
    # Collect role names for mermaid diagram context
    roles = data.get("saved_roles", [])
    role_names = ", ".join(r.get("name", "") for r in roles)

    try:
        flows_data = await _ai.generate_flows_json(
            story.get("title", ""),
            story.get("want_text", story.get("want", "")),
            roles=role_names,
        )
    except Exception as exc:
        await _edit_cb_msg(callback, f"⚠️ Ошибка: {exc}")
        return

    draft = [{"title": fd.get("title", "Flow"),
              "flow_type": fd.get("flow_type", "primary"),
              "description": fd.get("description", ""),
              "mermaid_source": fd.get("mermaid_source", "")}
             for fd in flows_data]
    await state.update_data(draft_flows=draft)
    await state.set_state(ProductFSM.reviewing_flows)

    fid = data.get("current_feature_id", "")
    text = (
        f"📖 <b>Story {story_index + 1}/{len(stories)}: "
        f"{story.get('title', '')}</b>\n\n"
        "🔄 <b>User Flows:</b>\n"
        "<i>Редактируйте текстом/голосом, затем Далее</i>\n\n"
        + _format_flows_text(draft)
    )
    await _edit_cb_msg(
        callback, text,
        reply_markup=_review_kb(
            back_cb=FeatureCB(id=fid, action="back").pack(),
            next_cb="wizard_save_flows",
        ),
    )


async def _start_story_use_cases(callback: CallbackQuery,
                                  state: FSMContext) -> None:
    """Generate use cases TEXT for current story."""
    data = await state.get_data()
    story = (data.get("saved_stories", []) or [{}])[data.get("story_index", 0)]
    flows = data.get("saved_flows", [])
    flow_titles = ", ".join(f.get("title", "") for f in flows)

    await _edit_cb_msg(callback,
                       f"📖 <b>{story.get('title', 'Story')}</b>\n\n"
                       "⏳ Генерирую use cases...")
    try:
        uc_data = await _ai.generate_use_cases_json(
            story.get("title", ""), flow_titles
        )
    except Exception as exc:
        await _edit_cb_msg(callback, f"⚠️ Ошибка: {exc}")
        return

    draft = [{"title": u.get("title", "UC"),
              "goal": u.get("goal", ""),
              "given_text": u.get("given_text", ""),
              "when_text": u.get("when_text", ""),
              "then_text": u.get("then_text", "")}
             for u in uc_data]
    await state.update_data(draft_use_cases=draft)
    await state.set_state(ProductFSM.reviewing_use_cases)

    fid = data.get("current_feature_id", "")
    text = (
        f"📖 <b>{story.get('title', 'Story')}</b>\n\n"
        "📋 <b>Use Cases (Given/When/Then):</b>\n"
        "<i>Редактируйте текстом/голосом, затем Далее</i>\n\n"
        + _format_use_cases_text(draft)
    )
    await _edit_cb_msg(
        callback, text,
        reply_markup=_review_kb(
            back_cb=FeatureCB(id=fid, action="back").pack(),
            next_cb="wizard_save_use_cases",
        ),
    )


async def _start_uc_requirements(callback: CallbackQuery,
                                  state: FSMContext,
                                  uc_index: int) -> None:
    """Generate requirements TEXT for use case at given index, or next story if done."""
    data = await state.get_data()
    use_cases = data.get("saved_use_cases", [])
    if uc_index >= len(use_cases):
        # All use cases done for this story — next story's flows
        story_index = data.get("story_index", 0) + 1
        await _start_story_flows(callback, state, story_index)
        return

    uc = use_cases[uc_index]
    await state.update_data(uc_index=uc_index, current_uc_id=str(uc.get("id", "")))

    gwt = (
        f"Given: {uc.get('given_text', '')} "
        f"When: {uc.get('when_text', '')} "
        f"Then: {uc.get('then_text', '')}"
    )

    await _edit_cb_msg(callback,
                       f"📋 <b>UC {uc_index + 1}/{len(use_cases)}: "
                       f"{uc.get('title', '')}</b>\n\n⏳ Генерирую требования...")
    try:
        reqs_data = await _ai.generate_requirements_json(
            uc.get("title", ""), uc.get("goal", ""), gwt
        )
    except Exception as exc:
        await _edit_cb_msg(callback, f"⚠️ Ошибка: {exc}")
        return

    draft = [{"title": r.get("title", "Req"),
              "text": r.get("text", ""),
              "requirement_type": r.get("requirement_type", "functional"),
              "priority": r.get("priority", "medium")}
             for r in reqs_data]
    await state.update_data(draft_requirements=draft)
    await state.set_state(ProductFSM.reviewing_requirements)

    fid = data.get("current_feature_id", "")
    text = (
        f"📋 <b>UC {uc_index + 1}/{len(use_cases)}: {uc.get('title', '')}</b>\n\n"
        "📝 <b>Требования:</b>\n"
        "<i>Редактируйте текстом/голосом, затем Далее</i>\n\n"
        + _format_requirements_text(draft)
    )
    await _edit_cb_msg(
        callback, text,
        reply_markup=_review_kb(
            back_cb=FeatureCB(id=fid, action="back").pack(),
            next_cb="wizard_save_requirements",
        ),
    )


# ═══════════════════════════════════════════════════════════
# reviewing_roles — edit TEXT list by typing/voice
# ═══════════════════════════════════════════════════════════


@router.message(ProductFSM.reviewing_roles)
async def handle_roles_edit(message: Message, state: FSMContext,
                            bot: Bot) -> None:
    instruction = await get_text_or_voice(message, bot)
    await _delete_user_msg(message)
    if not instruction:
        return

    data = await state.get_data()
    draft = data.get("draft_roles", [])
    fid = data.get("current_feature_id", "")
    await _send_or_edit(message, state, "⏳ Применяю правки к ролям...")

    current_text = "\n".join(
        f"{i}. {r['name']} ({r.get('role_type', 'end_user')}): "
        f"{r.get('description', '')}"
        for i, r in enumerate(draft, 1)
    )

    try:
        edited = await _ai.edit_roles_list(current_text, instruction)
    except Exception as exc:
        await _send_or_edit(message, state, f"⚠️ Ошибка: {exc}")
        return

    await state.update_data(draft_roles=edited)
    text = (
        "👤 <b>Обновлённые роли:</b>\n"
        "<i>Можете продолжить редактирование или нажмите Далее</i>\n\n"
        + _format_roles_text(edited)
    )
    await _send_or_edit(
        message, state, text,
        reply_markup=_review_kb(
            back_cb=FeatureCB(id=fid, action="back").pack(),
            next_cb="wizard_save_roles",
        ),
    )


# ═══════════════════════════════════════════════════════════
# wizard_save_roles — save actors + links, drill into first role's stories
# ═══════════════════════════════════════════════════════════


@router.callback_query(F.data == "wizard_save_roles")
async def handle_save_roles(callback: CallbackQuery,
                            state: FSMContext) -> None:
    """Save roles to backend as actors + feature-actor links, then drill into first role."""
    data = await state.get_data()
    draft = data.get("draft_roles", [])
    pid = data.get("current_feature_product_id", data.get("product_id", ""))
    fid = data.get("current_feature_id", "")

    if not draft:
        await callback.answer("Нет ролей для сохранения", show_alert=True)
        return

    await _edit_cb_msg(callback, "⏳ Сохраняю...")

    saved = []
    for rd in draft:
        try:
            actor = await _actor_api.create({
                "product_id": pid,
                "name": rd.get("name", "Role"),
                "description": rd.get("description", ""),
                "role_type": rd.get("role_type", "end_user"),
            })
            saved.append(actor)
            # Link actor to feature
            try:
                await _feature_actor_link_api.create({
                    "product_id": pid,
                    "feature_id": fid,
                    "actor_id": str(actor["id"]),
                })
            except Exception as exc:
                log.warning("Feature-actor link failed: %s", exc)
        except Exception as exc:
            log.warning("Actor save failed: %s", exc)
            saved.append({"id": "", "name": rd.get("name", "Role"),
                          "description": rd.get("description", ""),
                          "role_type": rd.get("role_type", "end_user"),
                          "status": "draft"})

    await state.update_data(saved_roles=saved)
    await _start_role_stories(callback, state, 0)
    await callback.answer()


# ═══════════════════════════════════════════════════════════
# wizard_save_features — save to backend, drill into first feature
# ═══════════════════════════════════════════════════════════


@router.callback_query(F.data == "wizard_save_features")
async def handle_save_features(callback: CallbackQuery,
                               state: FSMContext) -> None:
    """Save features to backend silently, then drill into first feature."""
    data = await state.get_data()
    draft = data.get("draft_features", [])
    product_id = data.get("product_id", "")

    if not draft:
        await callback.answer("Нет фичей для сохранения", show_alert=True)
        return

    await _edit_cb_msg(callback, "⏳ Сохраняю...")

    saved = []
    for fd in draft:
        try:
            feat = await _feature_api.create({
                "product_id": product_id,
                "name": fd["name"],
                "description": fd.get("description", ""),
            })
            saved.append(feat)
        except Exception as exc:
            log.warning("Feature save failed: %s", exc)
            saved.append({"id": "", "name": fd["name"],
                          "description": fd.get("description", ""),
                          "status": "draft"})

    await state.update_data(saved_features=saved)
    await _start_feature_roles(callback, state, 0)
    await callback.answer()


# ═══════════════════════════════════════════════════════════
# Product view (already saved) — shows feature buttons
# ═══════════════════════════════════════════════════════════


@router.callback_query(ProductCB.filter())
async def handle_product(callback: CallbackQuery, callback_data: ProductCB,
                         state: FSMContext) -> None:
    pid = callback_data.id

    if callback_data.action == "view":
        try:
            product = await _product_api.get_by_id(pid)
            features = await _feature_api.get_all(product_id=pid)
        except Exception as exc:
            await callback.answer(f"Ошибка: {exc}", show_alert=True)
            return

        text = f"📦 <b>{product['name']}</b>\n"
        if product.get("goal"):
            text += f"\n{product['goal'][:1500]}"

        if features:
            text += "\n\n📋 <b>Фичи:</b>\n\n" + _format_features_text(features)
        else:
            text += "\n\nФичей пока нет."

        await _edit_cb_msg(callback, text,
                           reply_markup=_saved_features_kb(features, pid, page=1))

    elif callback_data.action == "gen_features":
        await _edit_cb_msg(callback, "⏳ Генерирую фичи через AI...")
        try:
            product = await _product_api.get_by_id(pid)
            features_data = await _ai.generate_features_json(
                product["name"], product.get("goal", "")
            )
            # Store as draft for review
            draft = [{"name": fd["name"], "description": fd.get("description", "")}
                     for fd in features_data]
            await state.update_data(draft_features=draft, product_id=pid)
            await state.set_state(ProductFSM.reviewing_features)

            text = (
                "📋 <b>Сгенерированные фичи:</b>\n"
                "<i>Можете отредактировать текстом/голосом, затем нажмите Далее</i>\n\n"
                + _format_features_text(draft)
            )
            await _edit_cb_msg(
                callback, text,
                reply_markup=_review_kb(
                    back_cb=ProductCB(id=pid, action="view").pack(),
                    next_cb="wizard_save_features",
                    back_text="Назад",
                ),
            )
        except Exception as exc:
            await _edit_cb_msg(callback, f"⚠️ Ошибка: {exc}")

    await callback.answer()


# ═══════════════════════════════════════════════════════════
# Feature view → auto-generate stories as TEXT for review
# ═══════════════════════════════════════════════════════════


@router.callback_query(FeatureCB.filter())
async def handle_feature(callback: CallbackQuery, callback_data: FeatureCB,
                         state: FSMContext) -> None:
    fid = callback_data.id

    if callback_data.action == "view":
        try:
            feature = await _feature_api.get_by_id(fid)
        except Exception:
            feature = {"name": "?", "description": "", "product_id": ""}

        # Check if roles already saved for this feature
        try:
            links = await _feature_actor_link_api.get_all(feature_id=fid)
            existing_roles = []
            for lnk in links:
                try:
                    actor = await _actor_api.get_by_id(lnk["actor_id"])
                    existing_roles.append(actor)
                except Exception:
                    pass
        except Exception:
            existing_roles = []

        if existing_roles:
            # Already saved — show roles as buttons
            text = (
                f"🔹 <b>{feature['name']}</b>\n\n"
                "👤 <b>Роли:</b>"
            )
            await _edit_cb_msg(callback, text,
                               reply_markup=_saved_roles_kb(existing_roles, fid, page=1))
        else:
            # Generate roles as TEXT for review
            pid = feature.get("product_id", "")
            await state.update_data(
                current_feature_id=fid,
                current_feature_product_id=pid,
            )
            await _edit_cb_msg(callback,
                               f"🔹 <b>{feature['name']}</b>\n\n⏳ Генерирую роли...")
            try:
                roles_data = await _ai.generate_roles_json(
                    feature["name"], feature.get("description", "")
                )
            except Exception as exc:
                await _edit_cb_msg(callback, f"⚠️ Ошибка: {exc}")
                await callback.answer()
                return

            draft_roles = [{"name": r.get("name", "Role"),
                            "description": r.get("description", ""),
                            "role_type": r.get("role_type", "end_user")}
                           for r in roles_data]
            await state.update_data(draft_roles=draft_roles)
            await state.set_state(ProductFSM.reviewing_roles)

            text = (
                f"🔹 <b>{feature['name']}</b>\n\n"
                "👤 <b>Роли (Actors):</b>\n"
                "<i>Редактируйте текстом/голосом, затем Далее</i>\n\n"
                + _format_roles_text(draft_roles)
            )
            await _edit_cb_msg(
                callback, text,
                reply_markup=_review_kb(
                    back_cb=FeatureCB(id=fid, action="back").pack(),
                    next_cb="wizard_save_roles",
                ),
            )

    elif callback_data.action == "back":
        try:
            feature = await _feature_api.get_by_id(fid)
            pid = feature["product_id"]
            features = await _feature_api.get_all(product_id=pid)
        except Exception:
            await callback.answer("Ошибка", show_alert=True)
            return

        await state.clear()
        text = "📋 <b>Фичи:</b>\n\n" + _format_features_text(features)
        await _edit_cb_msg(callback, text,
                           reply_markup=_saved_features_kb(features, pid, page=1))

    await callback.answer()


# ═══════════════════════════════════════════════════════════
# reviewing_stories — edit TEXT list by typing
# ═══════════════════════════════════════════════════════════


@router.message(ProductFSM.reviewing_stories)
async def handle_stories_edit(message: Message, state: FSMContext,
                              bot: Bot) -> None:
    instruction = await get_text_or_voice(message, bot)
    await _delete_user_msg(message)
    if not instruction:
        return

    data = await state.get_data()
    draft = data.get("draft_stories", [])
    fid = data.get("current_feature_id", "")
    await _send_or_edit(message, state, "⏳ Применяю правки к stories...")

    current_text = "\n".join(
        f"{i}. {s['title']}: {s.get('want', '')} → {s.get('benefit', '')}"
        for i, s in enumerate(draft, 1)
    )

    try:
        edited = await _ai.edit_stories_list(current_text, instruction)
    except Exception as exc:
        await _send_or_edit(message, state, f"⚠️ Ошибка: {exc}")
        return

    await state.update_data(draft_stories=edited)
    text = (
        "📖 <b>Обновлённые stories:</b>\n"
        "<i>Можете продолжить редактирование или нажмите Далее</i>\n\n"
        + _format_stories_text(edited)
    )
    await _send_or_edit(
        message, state, text,
        reply_markup=_review_kb(
            back_cb=FeatureCB(id=fid, action="back").pack(),
            next_cb="wizard_save_stories",
            back_text="Назад",
        ),
    )


# ═══════════════════════════════════════════════════════════
# wizard_save_stories — save to backend, show as BUTTONS
# ═══════════════════════════════════════════════════════════


@router.callback_query(F.data == "wizard_save_stories")
async def handle_save_stories(callback: CallbackQuery,
                              state: FSMContext) -> None:
    """Save stories to backend, then drill into flows for first story."""
    data = await state.get_data()
    draft = data.get("draft_stories", [])
    fid = data.get("current_feature_id", "")
    pid = data.get("current_feature_product_id", data.get("product_id", ""))

    if not draft:
        await callback.answer("Нет stories для сохранения", show_alert=True)
        return

    await _edit_cb_msg(callback, "⏳ Сохраняю...")

    saved = []
    for sd in draft:
        try:
            story = await _story_api.create({
                "product_id": pid,
                "feature_id": fid,
                "title": sd.get("title", "Story"),
                "want_text": sd.get("want", ""),
                "benefit_text": sd.get("benefit", ""),
            })
            saved.append(story)
        except Exception as exc:
            log.warning("Story save failed: %s", exc)
            saved.append({"id": "", "title": sd.get("title", "Story"),
                          "want": sd.get("want", ""),
                          "benefit": sd.get("benefit", ""),
                          "status": "draft"})

    await state.update_data(saved_stories=saved)
    await _start_story_flows(callback, state, 0)
    await callback.answer()


# ═══════════════════════════════════════════════════════════
# reviewing_flows — edit TEXT list by typing/voice
# ═══════════════════════════════════════════════════════════


@router.message(ProductFSM.reviewing_flows)
async def handle_flows_edit(message: Message, state: FSMContext,
                            bot: Bot) -> None:
    instruction = await get_text_or_voice(message, bot)
    await _delete_user_msg(message)
    if not instruction:
        return

    data = await state.get_data()
    draft = data.get("draft_flows", [])
    fid = data.get("current_feature_id", "")
    await _send_or_edit(message, state, "⏳ Применяю правки к flows...")

    current_text = "\n".join(
        f"{i}. {f['title']} ({f.get('flow_type', 'primary')}): "
        f"{f.get('description', '')}"
        for i, f in enumerate(draft, 1)
    )

    try:
        edited = await _ai.edit_flows_list(current_text, instruction)
    except Exception as exc:
        await _send_or_edit(message, state, f"⚠️ Ошибка: {exc}")
        return

    await state.update_data(draft_flows=edited)
    text = (
        "🔄 <b>Обновлённые flows:</b>\n"
        "<i>Можете продолжить редактирование или нажмите Далее</i>\n\n"
        + _format_flows_text(edited)
    )
    await _send_or_edit(
        message, state, text,
        reply_markup=_review_kb(
            back_cb=FeatureCB(id=fid, action="back").pack(),
            next_cb="wizard_save_flows",
        ),
    )


# ═══════════════════════════════════════════════════════════
# wizard_save_flows — save to backend, drill into use cases
# ═══════════════════════════════════════════════════════════


@router.callback_query(F.data == "wizard_save_flows")
async def handle_save_flows(callback: CallbackQuery,
                            state: FSMContext) -> None:
    """Save flows to backend, then drill into use cases for current story."""
    data = await state.get_data()
    draft = data.get("draft_flows", [])
    pid = data.get("current_feature_product_id", data.get("product_id", ""))
    fid = data.get("current_feature_id", "")
    sid = data.get("current_story_id", "")

    if not draft:
        await callback.answer("Нет flows для сохранения", show_alert=True)
        return

    await _edit_cb_msg(callback, "⏳ Сохраняю...")

    saved = []
    for fd in draft:
        try:
            flow_data = {
                "product_id": pid,
                "feature_id": fid,
                "story_id": sid,
                "title": fd.get("title", "Flow"),
                "flow_type": fd.get("flow_type", "primary"),
            }
            if fd.get("description"):
                flow_data["description"] = fd["description"]
            if fd.get("mermaid_source"):
                flow_data["mermaid_source"] = fd["mermaid_source"]
            flow = await _flow_api.create(flow_data)
            saved.append(flow)
        except Exception as exc:
            log.warning("Flow save failed: %s", exc)
            saved.append({"id": "", "title": fd.get("title", "Flow"),
                          "flow_type": fd.get("flow_type", "primary"),
                          "description": fd.get("description", ""),
                          "mermaid_source": fd.get("mermaid_source", ""),
                          "status": "draft"})

    await state.update_data(saved_flows=saved)
    await _start_story_use_cases(callback, state)
    await callback.answer()


# ═══════════════════════════════════════════════════════════
# reviewing_use_cases — edit TEXT list by typing/voice
# ═══════════════════════════════════════════════════════════


@router.message(ProductFSM.reviewing_use_cases)
async def handle_use_cases_edit(message: Message, state: FSMContext,
                                bot: Bot) -> None:
    instruction = await get_text_or_voice(message, bot)
    await _delete_user_msg(message)
    if not instruction:
        return

    data = await state.get_data()
    draft = data.get("draft_use_cases", [])
    fid = data.get("current_feature_id", "")
    await _send_or_edit(message, state, "⏳ Применяю правки к use cases...")

    current_text = "\n".join(
        f"{i}. {u['title']}\n"
        f"   Given: {u.get('given_text', '')}\n"
        f"   When: {u.get('when_text', '')}\n"
        f"   Then: {u.get('then_text', '')}"
        for i, u in enumerate(draft, 1)
    )

    try:
        edited = await _ai.edit_use_cases_list(current_text, instruction)
    except Exception as exc:
        await _send_or_edit(message, state, f"⚠️ Ошибка: {exc}")
        return

    await state.update_data(draft_use_cases=edited)
    text = (
        "📋 <b>Обновлённые use cases:</b>\n"
        "<i>Можете продолжить редактирование или нажмите Далее</i>\n\n"
        + _format_use_cases_text(edited)
    )
    await _send_or_edit(
        message, state, text,
        reply_markup=_review_kb(
            back_cb=FeatureCB(id=fid, action="back").pack(),
            next_cb="wizard_save_use_cases",
        ),
    )


# ═══════════════════════════════════════════════════════════
# wizard_save_use_cases — save to backend, next story/feature
# ═══════════════════════════════════════════════════════════


@router.callback_query(F.data == "wizard_save_use_cases")
async def handle_save_use_cases(callback: CallbackQuery,
                                state: FSMContext) -> None:
    """Save use cases to backend, then drill into requirements for each UC."""
    data = await state.get_data()
    draft = data.get("draft_use_cases", [])
    pid = data.get("current_feature_product_id", data.get("product_id", ""))
    fid = data.get("current_feature_id", "")
    sid = data.get("current_story_id", "")
    saved_flows = data.get("saved_flows", [])
    # Use first saved flow's id as flow_id (required by schema)
    default_flow_id = str(saved_flows[0]["id"]) if saved_flows and saved_flows[0].get("id") else ""

    if not draft:
        await callback.answer("Нет use cases для сохранения", show_alert=True)
        return

    await _edit_cb_msg(callback, "⏳ Сохраняю...")

    saved = []
    for uc in draft:
        try:
            uc_data = {
                "product_id": pid,
                "feature_id": fid,
                "story_id": sid,
                "flow_id": default_flow_id,
                "title": uc.get("title", "UC"),
            }
            if uc.get("goal"):
                uc_data["goal"] = uc["goal"]
            if uc.get("given_text"):
                uc_data["given_text"] = uc["given_text"]
            if uc.get("when_text"):
                uc_data["when_text"] = uc["when_text"]
            if uc.get("then_text"):
                uc_data["then_text"] = uc["then_text"]
            result = await _use_case_api.create(uc_data)
            saved.append(result)
        except Exception as exc:
            log.warning("UseCase save failed: %s", exc)
            saved.append({"id": "", "title": uc.get("title", "UC"),
                          "goal": uc.get("goal", ""),
                          "given_text": uc.get("given_text", ""),
                          "when_text": uc.get("when_text", ""),
                          "then_text": uc.get("then_text", ""),
                          "status": "draft"})

    await state.update_data(saved_use_cases=saved)
    # Drill into requirements for first use case
    await _start_uc_requirements(callback, state, 0)
    await callback.answer()


# ═══════════════════════════════════════════════════════════
# reviewing_requirements — edit TEXT list by typing/voice
# ═══════════════════════════════════════════════════════════


@router.message(ProductFSM.reviewing_requirements)
async def handle_requirements_edit(message: Message, state: FSMContext,
                                   bot: Bot) -> None:
    instruction = await get_text_or_voice(message, bot)
    await _delete_user_msg(message)
    if not instruction:
        return

    data = await state.get_data()
    draft = data.get("draft_requirements", [])
    fid = data.get("current_feature_id", "")
    await _send_or_edit(message, state, "⏳ Применяю правки к требованиям...")

    current_text = "\n".join(
        f"{i}. {r['title']} [{r.get('requirement_type', 'functional')}] "
        f"({r.get('priority', 'medium')}): {r.get('text', '')}"
        for i, r in enumerate(draft, 1)
    )

    try:
        edited = await _ai.edit_requirements_list(current_text, instruction)
    except Exception as exc:
        await _send_or_edit(message, state, f"⚠️ Ошибка: {exc}")
        return

    await state.update_data(draft_requirements=edited)
    text = (
        "📝 <b>Обновлённые требования:</b>\n"
        "<i>Можете продолжить редактирование или нажмите Далее</i>\n\n"
        + _format_requirements_text(edited)
    )
    await _send_or_edit(
        message, state, text,
        reply_markup=_review_kb(
            back_cb=FeatureCB(id=fid, action="back").pack(),
            next_cb="wizard_save_requirements",
        ),
    )


# ═══════════════════════════════════════════════════════════
# wizard_save_requirements — save to backend, next UC or next story
# ═══════════════════════════════════════════════════════════


@router.callback_query(F.data == "wizard_save_requirements")
async def handle_save_requirements(callback: CallbackQuery,
                                   state: FSMContext) -> None:
    """Save requirements to backend, then advance to next use case or story."""
    data = await state.get_data()
    draft = data.get("draft_requirements", [])
    pid = data.get("current_feature_product_id", data.get("product_id", ""))
    fid = data.get("current_feature_id", "")
    uc_id = data.get("current_uc_id", "")

    if not draft:
        await callback.answer("Нет требований для сохранения", show_alert=True)
        return

    await _edit_cb_msg(callback, "⏳ Сохраняю...")

    for req in draft:
        try:
            req_data = {
                "product_id": pid,
                "feature_id": fid,
                "title": req.get("title", "Req"),
                "requirement_type": req.get("requirement_type", "functional"),
            }
            if uc_id:
                req_data["primary_use_case_id"] = uc_id
            if req.get("text"):
                req_data["text"] = req["text"]
            if req.get("priority"):
                req_data["priority"] = req["priority"]
            await _requirement_api.create(req_data)
        except Exception as exc:
            log.warning("Requirement save failed: %s", exc)

    # Advance: next use case's requirements, or next story
    uc_index = data.get("uc_index", 0) + 1
    await _start_uc_requirements(callback, state, uc_index)
    await callback.answer()


# ═══════════════════════════════════════════════════════════
# Role view
# ═══════════════════════════════════════════════════════════


@router.callback_query(RoleCB.filter())
async def handle_role(callback: CallbackQuery, callback_data: RoleCB,
                      state: FSMContext) -> None:
    rid = callback_data.id

    if callback_data.action == "view":
        try:
            actor = await _actor_api.get_by_id(rid)
        except Exception as exc:
            await callback.answer(f"Ошибка: {exc}", show_alert=True)
            return

        # Find feature link to get feature_id for back navigation
        try:
            links = await _feature_actor_link_api.get_all(actor_id=rid)
            feature_id = links[0]["feature_id"] if links else ""
        except Exception:
            feature_id = ""

        # Check if stories exist for this feature (from this role's perspective)
        try:
            stories = await _story_api.get_all(feature_id=feature_id)
        except Exception:
            stories = []

        if stories:
            text = (
                f"👤 <b>{actor.get('name', 'Role')}</b> "
                f"({actor.get('role_type', 'end_user')})\n\n"
                "📖 <b>User Stories:</b>"
            )
            await _edit_cb_msg(callback, text,
                               reply_markup=_saved_stories_kb(stories, feature_id, page=1))
        else:
            text = (
                f"👤 <b>{actor.get('name', 'Role')}</b> "
                f"({actor.get('role_type', 'end_user')})\n\n"
            )
            if actor.get("description"):
                text += f"{actor['description']}\n"
            text += f"\nСтатус: {actor.get('status', 'draft')}"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="◀️ Назад к ролям",
                    callback_data=FeatureCB(id=feature_id, action="view").pack(),
                )],
            ])
            await _edit_cb_msg(callback, text, reply_markup=kb)

    await callback.answer()


# ═══════════════════════════════════════════════════════════
# Story view
# ═══════════════════════════════════════════════════════════


@router.callback_query(StoryCB.filter())
async def handle_story(callback: CallbackQuery, callback_data: StoryCB,
                       state: FSMContext) -> None:
    sid = callback_data.id

    if callback_data.action == "view":
        try:
            story = await _story_api.get_by_id(sid)
        except Exception as exc:
            await callback.answer(f"Ошибка: {exc}", show_alert=True)
            return

        # Check if flows already saved
        try:
            existing_flows = await _flow_api.get_all(story_id=sid)
        except Exception:
            existing_flows = []

        if existing_flows:
            text = (
                f"📖 <b>{story['title']}</b>\n\n"
                "🔄 <b>User Flows:</b>"
            )
            await _edit_cb_msg(callback, text,
                               reply_markup=_saved_flows_kb(existing_flows, sid, page=1))
        else:
            text = f"📖 <b>{story['title']}</b>\n\n"
            if story.get("want_text"):
                text += f"Я хочу: {story['want_text']}\n"
            if story.get("benefit_text"):
                text += f"Чтобы: {story['benefit_text']}\n"
            text += f"\nСтатус: {story.get('status', 'draft')}"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="◀️ Назад к stories",
                    callback_data=FeatureCB(
                        id=story.get("feature_id", ""), action="view"
                    ).pack(),
                )],
            ])
            await _edit_cb_msg(callback, text, reply_markup=kb)

    elif callback_data.action == "flows":
        # Show flows list for this story
        try:
            flows = await _flow_api.get_all(story_id=sid)
        except Exception:
            flows = []
        text = "🔄 <b>User Flows:</b>"
        await _edit_cb_msg(callback, text,
                           reply_markup=_saved_flows_kb(flows, sid, page=1))

    await callback.answer()


# ═══════════════════════════════════════════════════════════
# Flow view
# ═══════════════════════════════════════════════════════════


@router.callback_query(FlowCB.filter())
async def handle_flow(callback: CallbackQuery, callback_data: FlowCB,
                      state: FSMContext) -> None:
    fid = callback_data.id

    if callback_data.action == "view":
        try:
            flow = await _flow_api.get_by_id(fid)
        except Exception as exc:
            await callback.answer(f"Ошибка: {exc}", show_alert=True)
            return

        sid = flow.get("story_id", "")

        # Check if use cases exist for this story
        try:
            existing_ucs = await _use_case_api.get_all(story_id=sid)
        except Exception:
            existing_ucs = []

        if existing_ucs:
            text = (
                f"🔄 <b>{flow.get('title', 'Flow')}</b> "
                f"({flow.get('flow_type', 'primary')})\n\n"
                "📋 <b>Use Cases:</b>"
            )
            await _edit_cb_msg(callback, text,
                               reply_markup=_saved_use_cases_kb(existing_ucs, sid, page=1))
        else:
            text = (
                f"🔄 <b>{flow.get('title', 'Flow')}</b> "
                f"({flow.get('flow_type', 'primary')})\n\n"
            )
            if flow.get("description"):
                text += f"{flow['description']}\n"
            text += f"\nСтатус: {flow.get('status', 'draft')}"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="◀️ Назад к flows",
                    callback_data=StoryCB(id=sid, action="flows").pack(),
                )],
            ])
            await _edit_cb_msg(callback, text, reply_markup=kb)

    await callback.answer()


# ═══════════════════════════════════════════════════════════
# Use Case view
# ═══════════════════════════════════════════════════════════


@router.callback_query(UseCaseCB.filter())
async def handle_use_case(callback: CallbackQuery, callback_data: UseCaseCB,
                          state: FSMContext) -> None:
    uid = callback_data.id

    if callback_data.action == "view":
        try:
            uc = await _use_case_api.get_by_id(uid)
        except Exception as exc:
            await callback.answer(f"Ошибка: {exc}", show_alert=True)
            return

        sid = uc.get("story_id", "")
        text = f"📋 <b>{uc.get('title', 'UC')}</b>\n\n"
        if uc.get("goal"):
            text += f"<b>Цель:</b> {uc['goal']}\n\n"
        if uc.get("given_text"):
            text += f"<b>Given:</b> {uc['given_text']}\n"
        if uc.get("when_text"):
            text += f"<b>When:</b> {uc['when_text']}\n"
        if uc.get("then_text"):
            text += f"<b>Then:</b> {uc['then_text']}\n"
        text += f"\nСтатус: {uc.get('status', 'draft')}"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="◀️ Назад к use cases",
                callback_data=StoryCB(id=sid, action="flows").pack(),
            )],
        ])
        await _edit_cb_msg(callback, text, reply_markup=kb)

    await callback.answer()
