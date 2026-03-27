"""Main wizard: single-message UI with pagination and cascading drill-down.

/start shows paginated product list as buttons (max 5 per page).
All navigation edits ONE bot message. User messages are deleted instantly.
Creation wizard: name -> description (text/voice) -> GPT summary -> Next
-> features generated as buttons -> click feature -> stories -> ...

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


# ─── Helpers ────────────────────────────────────────────────


def _page_row(entity: str, page: int, total_pages: int, parent_id: str = "") -> list[InlineKeyboardButton]:
    """Build ◀️ {page}/{total} ▶️ navigation row."""
    row = []
    if total_pages <= 1:
        return row
    if page > 1:
        row.append(InlineKeyboardButton(
            text="◀️",
            callback_data=PageCB(entity=entity, page=page - 1, parent_id=parent_id).pack(),
        ))
    row.append(InlineKeyboardButton(
        text=f"{page}/{total_pages}",
        callback_data="noop",
    ))
    if page < total_pages:
        row.append(InlineKeyboardButton(
            text="▶️",
            callback_data=PageCB(entity=entity, page=page + 1, parent_id=parent_id).pack(),
        ))
    return row


def _products_kb(products: list[dict], page: int = 1) -> InlineKeyboardMarkup:
    """Paginated product list + Create button."""
    total = math.ceil(len(products) / PER_PAGE) or 1
    page = max(1, min(page, total))
    start = (page - 1) * PER_PAGE
    subset = products[start:start + PER_PAGE]

    buttons = []
    for p in subset:
        buttons.append([InlineKeyboardButton(
            text=f"📦 {p['name']}",
            callback_data=ProductCB(id=str(p["id"]), action="view").pack(),
        )])
    nav = _page_row("products", page, total)
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(
        text="➕ Создать продукт",
        callback_data=MenuCB(action="create_product").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _features_kb(features: list[dict], product_id: str, page: int = 1,
                  show_next: bool = False) -> InlineKeyboardMarkup:
    """Paginated feature list with optional Далее button."""
    total = math.ceil(len(features) / PER_PAGE) or 1
    page = max(1, min(page, total))
    start = (page - 1) * PER_PAGE
    subset = features[start:start + PER_PAGE]

    buttons = []
    for feat in subset:
        icon = "✅" if feat.get("status") == "approved" else "📝"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {feat['name']}",
            callback_data=FeatureCB(id=str(feat["id"]), action="view").pack(),
        )])
    nav = _page_row("features", page, total, parent_id=product_id)
    if nav:
        buttons.append(nav)
    bottom = []
    bottom.append(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data=ProductCB(id=product_id, action="view").pack(),
    ))
    if show_next and features:
        bottom.append(InlineKeyboardButton(
            text="➡️ Далее",
            callback_data="wizard_dive_features",
        ))
    buttons.append(bottom)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _stories_kb(stories: list[dict], feature_id: str, page: int = 1) -> InlineKeyboardMarkup:
    """Paginated story list."""
    total = math.ceil(len(stories) / PER_PAGE) or 1
    page = max(1, min(page, total))
    start = (page - 1) * PER_PAGE
    subset = stories[start:start + PER_PAGE]

    buttons = []
    for s in subset:
        icon = "✅" if s.get("status") == "approved" else "📝"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {s['title'][:40]}",
            callback_data=StoryCB(id=str(s["id"]), action="view").pack(),
        )])
    nav = _page_row("stories", page, total, parent_id=feature_id)
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад к фичам",
        callback_data=FeatureCB(id=feature_id, action="back").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _summary_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Далее", callback_data="wizard_next")],
    ])


def _send_long(text: str, limit: int = 4000) -> list[str]:
    """Split text into Telegram-safe chunks."""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:limit])
        text = text[limit:]
    return chunks


async def _delete_user_msg(message: Message) -> None:
    """Silently delete the user's message."""
    try:
        await message.delete()
    except Exception:
        pass


async def _send_or_edit(message: Message, state: FSMContext, text: str,
                        reply_markup: InlineKeyboardMarkup = None) -> None:
    """Edit the tracked bot message or send a new one. Always update bot_msg_id."""
    data = await state.get_data()
    bot_msg_id = data.get("bot_msg_id")
    chat_id = message.chat.id

    if bot_msg_id:
        try:
            from aiogram import Bot as _Bot
            bot = message.bot  # type: ignore[attr-defined]
            await bot.edit_message_text(
                text=text, chat_id=chat_id, message_id=bot_msg_id,
                reply_markup=reply_markup, parse_mode="HTML",
            )
            return
        except Exception:
            pass

    sent = await message.answer(text, reply_markup=reply_markup)
    await state.update_data(bot_msg_id=sent.message_id)


async def _edit_bot_msg(callback: CallbackQuery, text: str,
                        reply_markup: InlineKeyboardMarkup = None) -> None:
    """Edit the message that holds the inline keyboard (callback source)."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        pass


# ─── /start — Product list ──────────────────────────────────


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


# ─── Pagination ─────────────────────────────────────────────


@router.callback_query(PageCB.filter())
async def handle_page(callback: CallbackQuery, callback_data: PageCB, state: FSMContext) -> None:
    entity = callback_data.entity
    page = callback_data.page
    parent_id = callback_data.parent_id

    if entity == "products":
        try:
            products = await _product_api.get_all()
        except Exception:
            products = []
        await _edit_bot_msg(
            callback,
            "📦 <b>Ваши продукты:</b>",
            reply_markup=_products_kb(products, page=page),
        )

    elif entity == "features":
        try:
            features = await _feature_api.get_all(product_id=parent_id)
        except Exception:
            features = []
        text = "📋 <b>Фичи:</b>\n"
        for i, feat in enumerate(features, 1):
            text += f"\n{i}. <b>{feat['name']}</b>"
        await _edit_bot_msg(
            callback, text,
            reply_markup=_features_kb(features, parent_id, page=page),
        )

    elif entity == "stories":
        try:
            stories = await _story_api.get_all(feature_id=parent_id)
        except Exception:
            stories = []
        await _edit_bot_msg(
            callback,
            "📖 <b>User Stories:</b>",
            reply_markup=_stories_kb(stories, parent_id, page=page),
        )

    await callback.answer()


# ─── Noop for page counter button ───────────────────────────


@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery) -> None:
    await callback.answer()


# ─── Menu callbacks ─────────────────────────────────────────


@router.callback_query(MenuCB.filter())
async def handle_menu(callback: CallbackQuery, callback_data: MenuCB, state: FSMContext) -> None:
    if callback_data.action == "products":
        await state.clear()
        try:
            products = await _product_api.get_all()
        except Exception:
            products = []
        await _edit_bot_msg(
            callback,
            "📦 <b>Ваши продукты:</b>" if products else "Продуктов пока нет.",
            reply_markup=_products_kb(products, page=1),
        )
        await state.update_data(bot_msg_id=callback.message.message_id)

    elif callback_data.action == "create_product":
        await _edit_bot_msg(callback, "Введите <b>название продукта</b>:")
        await state.update_data(bot_msg_id=callback.message.message_id)
        await state.set_state(ProductFSM.waiting_for_name)

    await callback.answer()


# ─── Create product wizard ──────────────────────────────────


@router.message(ProductFSM.waiting_for_name, F.text)
async def handle_product_name(message: Message, state: FSMContext) -> None:
    name = message.text
    await _delete_user_msg(message)
    await state.update_data(product_name=name)
    await state.set_state(ProductFSM.waiting_for_description)
    await _send_or_edit(
        message, state,
        f"Продукт: <b>{name}</b>\n\n"
        "Теперь опишите продукт — <b>текстом или голосовым сообщением</b>:",
    )


@router.message(ProductFSM.waiting_for_description)
async def handle_product_description(message: Message, state: FSMContext, bot: Bot) -> None:
    text = await get_text_or_voice(message, bot)
    await _delete_user_msg(message)
    if not text:
        await _send_or_edit(message, state, "Пожалуйста, отправьте текст или голосовое сообщение.")
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
    chunks = _send_long(display)
    # For multi-chunk we send last chunk with keyboard
    for i, chunk in enumerate(chunks):
        kb = _summary_kb() if i == len(chunks) - 1 else None
        await _send_or_edit(message, state, chunk, reply_markup=kb)


# ─── Summary review — edit by typing, Next via button ───────


@router.message(ProductFSM.reviewing_summary)
async def handle_summary_edit(message: Message, state: FSMContext, bot: Bot) -> None:
    """User types text/voice in reviewing_summary → apply as edit instruction."""
    instruction = await get_text_or_voice(message, bot)
    await _delete_user_msg(message)
    if not instruction:
        await _send_or_edit(message, state, "Отправьте текст или голосовое.")
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
        reply_markup=_summary_kb(),
    )


# ─── "Далее" button — plain F.data match, no CallbackData filter issues ─


@router.callback_query(F.data == "wizard_next")
async def handle_wizard_next(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle the ➡️ Далее button press."""
    current = await state.get_state()
    log.info("wizard_next pressed, FSM state=%s", current)

    if current == ProductFSM.reviewing_summary.state:
        data = await state.get_data()
        await _edit_bot_msg(callback, "⏳ Сохраняю продукт и генерирую фичи...")

        # 1. Save product
        try:
            product = await _product_api.create({
                "name": data["product_name"],
                "goal": data.get("product_summary", ""),
            })
            product_id = str(product["id"])
            await state.update_data(product_id=product_id)
        except Exception as exc:
            await _edit_bot_msg(callback, f"⚠️ Ошибка создания: {exc}")
            await callback.answer()
            return

        # 2. Generate features via AI
        try:
            features_data = await _ai.generate_features_json(
                data["product_name"], data.get("product_summary", "")
            )
        except Exception as exc:
            await _edit_bot_msg(
                callback,
                f"✅ Продукт создан, но ошибка генерации фичей: {exc}",
            )
            await callback.answer()
            return

        # 3. Save features to backend (best-effort) and keep local list
        saved_features = []
        for fd in features_data:
            feat_record = {
                "id": "",
                "name": fd["name"],
                "description": fd.get("description", ""),
                "status": "draft",
            }
            try:
                feat = await _feature_api.create({
                    "product_id": product_id,
                    "name": fd["name"],
                    "description": fd.get("description", ""),
                })
                feat_record["id"] = str(feat.get("id", ""))
            except Exception as exc:
                log.warning("Feature save failed: %s", exc)
            saved_features.append(feat_record)

        await state.update_data(features=saved_features, product_id=product_id)
        await state.set_state(ProductFSM.reviewing_features)

        text = f"✅ Продукт <b>{data['product_name']}</b> создан!\n\n"
        text += "📋 <b>Сгенерированные фичи:</b>\n"
        for i, f in enumerate(saved_features, 1):
            text += f"\n{i}. <b>{f['name']}</b>"
            if f.get("description"):
                text += f"\n   {f['description'][:80]}"

        await _edit_bot_msg(
            callback, text,
            reply_markup=_features_kb(saved_features, product_id, page=1, show_next=True),
        )

    await callback.answer()


@router.callback_query(F.data == "wizard_dive_features")
async def handle_dive_features(callback: CallbackQuery, state: FSMContext) -> None:
    """Далее on features list — open first feature and auto-generate its stories."""
    data = await state.get_data()
    features = data.get("features", [])

    if not features:
        await callback.answer("Нет фичей для проработки", show_alert=True)
        return

    # Open first feature
    first = features[0]
    fid = first.get("id", "")
    if fid:
        # Simulate clicking the first feature
        try:
            feature = await _feature_api.get_by_id(fid)
            stories = await _story_api.get_all(feature_id=fid)
        except Exception:
            feature = first
            stories = []

        if not stories:
            await _edit_bot_msg(callback, f"🔹 <b>{first['name']}</b>\n\n⏳ Генерирую user stories...")
            try:
                stories_data = await _ai.generate_stories_json(
                    first["name"], first.get("description", "")
                )
                for sd in stories_data:
                    try:
                        await _story_api.create({
                            "product_id": data.get("product_id", ""),
                            "feature_id": fid,
                            "title": sd.get("title", "Story"),
                            "want_text": sd.get("want", ""),
                            "benefit_text": sd.get("benefit", ""),
                        })
                    except Exception:
                        pass
                stories = await _story_api.get_all(feature_id=fid)
            except Exception as exc:
                await _edit_bot_msg(callback, f"⚠️ Ошибка генерации stories: {exc}")
                await callback.answer()
                return

        text = f"🔹 <b>{first['name']}</b>\n"
        if first.get("description"):
            text += f"{first['description'][:500]}\n"
        text += "\n📖 <b>User Stories:</b>"

        await _edit_bot_msg(
            callback, text,
            reply_markup=_stories_kb(stories, fid, page=1),
        )
    else:
        # No backend ID — show feature info from FSM data
        text = f"🔹 <b>{first['name']}</b>\n"
        if first.get("description"):
            text += f"{first['description'][:500]}\n"
        text += "\n⚠️ Фича не сохранена в бэкенд. Проверьте подключение."

        product_id = data.get("product_id", "")
        await _edit_bot_msg(
            callback, text,
            reply_markup=_features_kb(features, product_id, page=1, show_next=True),
        )

    await callback.answer()


# ─── Product view ────────────────────────────────────────────


@router.callback_query(ProductCB.filter())
async def handle_product(callback: CallbackQuery, callback_data: ProductCB, state: FSMContext) -> None:
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
            text += f"\n{product['goal'][:1000]}"

        if features:
            text += "\n\n📋 <b>Фичи:</b>\n"
            for i, feat in enumerate(features, 1):
                text += f"\n{i}. <b>{feat['name']}</b>"
        else:
            text += "\n\nФичей пока нет."

        await _edit_bot_msg(
            callback, text,
            reply_markup=_features_kb(features, pid, page=1),
        )

    elif callback_data.action == "gen_features":
        await _edit_bot_msg(callback, "⏳ Генерирую фичи через AI...")
        try:
            product = await _product_api.get_by_id(pid)
            features_data = await _ai.generate_features_json(
                product["name"], product.get("goal", "")
            )
            for fd in features_data:
                try:
                    await _feature_api.create({
                        "product_id": pid,
                        "name": fd["name"],
                        "description": fd.get("description", ""),
                    })
                except Exception:
                    pass
            features = await _feature_api.get_all(product_id=pid)
        except Exception as exc:
            await _edit_bot_msg(callback, f"⚠️ Ошибка: {exc}")
            await callback.answer()
            return

        text = "📋 <b>Фичи:</b>\n"
        for i, feat in enumerate(features, 1):
            text += f"\n{i}. <b>{feat['name']}</b>"
        await _edit_bot_msg(
            callback, text,
            reply_markup=_features_kb(features, pid, page=1),
        )

    await callback.answer()


# ─── Feature view → Stories ──────────────────────────────────


@router.callback_query(FeatureCB.filter())
async def handle_feature(callback: CallbackQuery, callback_data: FeatureCB, state: FSMContext) -> None:
    fid = callback_data.id

    if callback_data.action == "view":
        try:
            feature = await _feature_api.get_by_id(fid)
            stories = await _story_api.get_all(feature_id=fid)
        except Exception:
            stories = []
            feature = {"name": "?", "description": "", "product_id": ""}

        text = f"🔹 <b>{feature['name']}</b>\n"
        if feature.get("description"):
            text += f"{feature['description'][:500]}\n"

        if not stories:
            # Auto-generate stories on first view
            await _edit_bot_msg(callback, f"🔹 <b>{feature['name']}</b>\n\n⏳ Генерирую user stories...")
            try:
                stories_data = await _ai.generate_stories_json(
                    feature["name"], feature.get("description", "")
                )
                for sd in stories_data:
                    try:
                        await _story_api.create({
                            "product_id": feature["product_id"],
                            "feature_id": fid,
                            "title": sd.get("title", "Story"),
                            "want_text": sd.get("want", ""),
                            "benefit_text": sd.get("benefit", ""),
                        })
                    except Exception:
                        pass
                stories = await _story_api.get_all(feature_id=fid)
            except Exception as exc:
                await _edit_bot_msg(callback, f"⚠️ Ошибка: {exc}")
                await callback.answer()
                return

        text += "\n📖 <b>User Stories:</b>"
        await _edit_bot_msg(
            callback, text,
            reply_markup=_stories_kb(stories, fid, page=1),
        )

    elif callback_data.action == "gen_stories":
        await _edit_bot_msg(callback, "⏳ Генерирую user stories через AI...")
        try:
            feature = await _feature_api.get_by_id(fid)
            stories_data = await _ai.generate_stories_json(
                feature["name"], feature.get("description", "")
            )
            for sd in stories_data:
                try:
                    await _story_api.create({
                        "product_id": feature["product_id"],
                        "feature_id": fid,
                        "title": sd.get("title", "Story"),
                        "want_text": sd.get("want", ""),
                        "benefit_text": sd.get("benefit", ""),
                    })
                except Exception:
                    pass
            stories = await _story_api.get_all(feature_id=fid)
        except Exception as exc:
            await _edit_bot_msg(callback, f"⚠️ Ошибка: {exc}")
            await callback.answer()
            return

        await _edit_bot_msg(
            callback,
            f"🔹 <b>{feature['name']}</b>\n\n📖 <b>User Stories:</b>",
            reply_markup=_stories_kb(stories, fid, page=1),
        )

    elif callback_data.action == "back":
        try:
            feature = await _feature_api.get_by_id(fid)
            pid = feature["product_id"]
            features = await _feature_api.get_all(product_id=pid)
        except Exception:
            await callback.answer("Ошибка", show_alert=True)
            return

        text = "📋 <b>Фичи:</b>\n"
        for i, feat in enumerate(features, 1):
            text += f"\n{i}. <b>{feat['name']}</b>"
        await _edit_bot_msg(
            callback, text,
            reply_markup=_features_kb(features, pid, page=1),
        )

    await callback.answer()


# ─── Story view ──────────────────────────────────────────────


@router.callback_query(StoryCB.filter())
async def handle_story(callback: CallbackQuery, callback_data: StoryCB, state: FSMContext) -> None:
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
                callback_data=FeatureCB(id=story.get("feature_id", ""), action="view").pack(),
            )],
        ])
        await _edit_bot_msg(callback, text, reply_markup=kb)

    await callback.answer()
