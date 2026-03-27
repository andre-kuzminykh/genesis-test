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
    MenuCB, ProductCB, FeatureCB, StoryCB, WizardCB, PageCB,
)
from service.ai.openai_service import OpenAIService
from service.api.product_api import ProductAPI
from service.api.feature_api import FeatureAPI
from service.api.story_api import StoryAPI
from service.api.flow_api import FlowAPI
from service.voice import get_text_or_voice

log = logging.getLogger(__name__)
router = Router(name="wizard_main")

_ai = OpenAIService()
_product_api = ProductAPI()
_feature_api = FeatureAPI()
_story_api = StoryAPI()
_flow_api = FlowAPI()

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


def _format_features_text(features: list[dict]) -> str:
    """Format features as numbered text list with full descriptions."""
    lines = []
    for i, f in enumerate(features, 1):
        lines.append(f"{i}. <b>{f['name']}</b>")
        if f.get("description"):
            lines.append(f"   {f['description']}")
        lines.append("")  # blank line between features
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
        await callback.message.edit_text(text, reply_markup=reply_markup)
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
    page = callback_data.page
    pid = callback_data.parent_id

    if entity == "products":
        try:
            products = await _product_api.get_all()
        except Exception:
            products = []
        await _edit_cb_msg(callback, "📦 <b>Ваши продукты:</b>",
                           reply_markup=_products_kb(products, page=page))

    elif entity == "features":
        try:
            features = await _feature_api.get_all(product_id=pid)
        except Exception:
            features = []
        text = "📋 <b>Фичи:</b>\n\n" + _format_features_text(features)
        await _edit_cb_msg(callback, text,
                           reply_markup=_saved_features_kb(features, pid, page=page))

    elif entity == "stories":
        try:
            stories = await _story_api.get_all(feature_id=pid)
        except Exception:
            stories = []
        await _edit_cb_msg(callback, "📖 <b>User Stories:</b>",
                           reply_markup=_saved_stories_kb(stories, pid, page=page))

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
# wizard_save_features — save to backend, show as BUTTONS
# ═══════════════════════════════════════════════════════════


@router.callback_query(F.data == "wizard_save_features")
async def handle_save_features(callback: CallbackQuery,
                               state: FSMContext) -> None:
    data = await state.get_data()
    draft = data.get("draft_features", [])
    product_id = data.get("product_id", "")

    if not draft:
        await callback.answer("Нет фичей для сохранения", show_alert=True)
        return

    await _edit_cb_msg(callback, "⏳ Сохраняю фичи...")

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
    await state.clear()

    text = "✅ <b>Фичи сохранены!</b>\n\nВыберите фичу для детальной проработки:"
    await _edit_cb_msg(
        callback, text,
        reply_markup=_saved_features_kb(saved, product_id, page=1),
    )
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

        # Check if stories already saved
        try:
            existing = await _story_api.get_all(feature_id=fid)
        except Exception:
            existing = []

        if existing:
            # Already saved — show as buttons
            text = (
                f"🔹 <b>{feature['name']}</b>\n"
                f"{feature.get('description', '')[:500]}\n\n"
                "📖 <b>User Stories:</b>"
            )
            await _edit_cb_msg(callback, text,
                               reply_markup=_saved_stories_kb(existing, fid, page=1))
        else:
            # Generate stories as TEXT for review
            await _edit_cb_msg(callback,
                               f"🔹 <b>{feature['name']}</b>\n\n⏳ Генерирую user stories...")
            try:
                stories_data = await _ai.generate_stories_json(
                    feature["name"], feature.get("description", "")
                )
            except Exception as exc:
                await _edit_cb_msg(callback, f"⚠️ Ошибка: {exc}")
                await callback.answer()
                return

            draft_stories = []
            for sd in stories_data:
                draft_stories.append({
                    "title": sd.get("title", "Story"),
                    "want": sd.get("want", ""),
                    "benefit": sd.get("benefit", ""),
                })

            await state.update_data(
                draft_stories=draft_stories,
                current_feature_id=fid,
                current_feature_product_id=feature.get("product_id", ""),
            )
            await state.set_state(ProductFSM.reviewing_stories)

            text = (
                f"🔹 <b>{feature['name']}</b>\n\n"
                "📖 <b>User Stories:</b>\n"
                "<i>Можете отредактировать текстом/голосом, затем нажмите Далее</i>\n\n"
                + _format_stories_text(draft_stories)
            )
            await _edit_cb_msg(
                callback, text,
                reply_markup=_review_kb(
                    back_cb=FeatureCB(id=fid, action="back").pack(),
                    next_cb="wizard_save_stories",
                    back_text="Назад",
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
    data = await state.get_data()
    draft = data.get("draft_stories", [])
    fid = data.get("current_feature_id", "")
    pid = data.get("current_feature_product_id", "")

    if not draft:
        await callback.answer("Нет stories для сохранения", show_alert=True)
        return

    await _edit_cb_msg(callback, "⏳ Сохраняю stories...")

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
            saved.append({"id": "", "title": sd.get("title", ""),
                          "status": "draft"})

    await state.clear()

    text = "✅ <b>Stories сохранены!</b>\n\nВыберите story для просмотра:"
    await _edit_cb_msg(
        callback, text,
        reply_markup=_saved_stories_kb(saved, fid, page=1),
    )
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

    await callback.answer()
