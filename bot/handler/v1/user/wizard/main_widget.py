"""Main wizard: product list, create product, cascading decomposition.

/start shows product list as buttons. If empty — starts creation wizard.
Creation: name → description (text/voice) → GPT summary → [Edit/Next]
→ features generated → [approve/edit each] → stories per feature → …

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

import json

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from state.product_state import ProductFSM
from callback.navigation_cb import MenuCB, ProductCB, FeatureCB, StoryCB, WizardCB
from service.ai.openai_service import OpenAIService
from service.api.product_api import ProductAPI
from service.api.feature_api import FeatureAPI
from service.api.story_api import StoryAPI
from service.api.flow_api import FlowAPI
from service.voice import get_text_or_voice

router = Router(name="wizard_main")

_ai = OpenAIService()
_product_api = ProductAPI()
_feature_api = FeatureAPI()
_story_api = StoryAPI()
_flow_api = FlowAPI()


# ─── Helpers ────────────────────────────────────────────────

def _products_kb(products: list[dict]) -> InlineKeyboardMarkup:
    """Build inline keyboard with product buttons + Create button."""
    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(
            text=f"📦 {p['name']}",
            callback_data=ProductCB(id=p["id"], action="view").pack(),
        )])
    buttons.append([InlineKeyboardButton(
        text="➕ Создать продукт",
        callback_data=MenuCB(action="create_product").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _product_detail_kb(product_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📋 Фичи",
            callback_data=ProductCB(id=product_id, action="next").pack(),
        )],
        [InlineKeyboardButton(
            text="✏️ Редактировать",
            callback_data=ProductCB(id=product_id, action="edit").pack(),
        )],
        [InlineKeyboardButton(
            text="◀️ Назад к продуктам",
            callback_data=MenuCB(action="products").pack(),
        )],
    ])


def _features_kb(features: list[dict], product_id: str) -> InlineKeyboardMarkup:
    buttons = []
    for f in features:
        status_icon = "✅" if f.get("status") == "approved" else "📝"
        buttons.append([InlineKeyboardButton(
            text=f"{status_icon} {f['name']}",
            callback_data=FeatureCB(id=f["id"], action="view").pack(),
        )])
    buttons.append([
        InlineKeyboardButton(
            text="🤖 Сгенерировать фичи",
            callback_data=ProductCB(id=product_id, action="gen_features").pack(),
        ),
    ])
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад к продукту",
        callback_data=ProductCB(id=product_id, action="view").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _stories_kb(stories: list[dict], feature_id: str) -> InlineKeyboardMarkup:
    buttons = []
    for s in stories:
        status_icon = "✅" if s.get("status") == "approved" else "📝"
        buttons.append([InlineKeyboardButton(
            text=f"{status_icon} {s['title'][:40]}",
            callback_data=StoryCB(id=s["id"], action="view").pack(),
        )])
    buttons.append([
        InlineKeyboardButton(
            text="🤖 Сгенерировать истории",
            callback_data=FeatureCB(id=feature_id, action="gen_stories").pack(),
        ),
    ])
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад к фичам",
        callback_data=FeatureCB(id=feature_id, action="back").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _summary_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=WizardCB(action="edit").pack()),
            InlineKeyboardButton(text="➡️ Далее", callback_data=WizardCB(action="next").pack()),
        ],
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


# ─── /start — Product list ──────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        products = await _product_api.get_all()
    except Exception:
        products = []

    if products:
        await message.answer(
            "📦 <b>Ваши продукты:</b>",
            reply_markup=_products_kb(products),
        )
    else:
        await message.answer(
            "👋 Добро пожаловать!\n\nУ вас пока нет продуктов.\n"
            "Давайте создадим первый — введите <b>название продукта</b>:"
        )
        await state.set_state(ProductFSM.waiting_for_name)


# ─── Menu callbacks ─────────────────────────────────────────

@router.callback_query(MenuCB.filter())
async def handle_menu(callback: CallbackQuery, callback_data: MenuCB, state: FSMContext) -> None:
    if callback_data.action == "products":
        await state.clear()
        try:
            products = await _product_api.get_all()
        except Exception:
            products = []
        await callback.message.edit_text(
            "📦 <b>Ваши продукты:</b>" if products else "Продуктов пока нет.",
            reply_markup=_products_kb(products),
        )

    elif callback_data.action == "create_product":
        await callback.message.edit_text("Введите <b>название продукта</b>:")
        await state.set_state(ProductFSM.waiting_for_name)

    await callback.answer()


# ─── Create product wizard ──────────────────────────────────

@router.message(ProductFSM.waiting_for_name, F.text)
async def handle_product_name(message: Message, state: FSMContext) -> None:
    await state.update_data(product_name=message.text)
    await state.set_state(ProductFSM.waiting_for_description)
    await message.answer(
        f"Продукт: <b>{message.text}</b>\n\n"
        "Теперь опишите продукт — <b>текстом или голосовым сообщением</b>:"
    )


@router.message(ProductFSM.waiting_for_description)
async def handle_product_description(message: Message, state: FSMContext, bot: Bot) -> None:
    text = await get_text_or_voice(message, bot)
    if not text:
        await message.answer("Пожалуйста, отправьте текст или голосовое сообщение.")
        return

    await state.update_data(product_description=text)
    data = await state.get_data()
    name = data["product_name"]

    wait_msg = await message.answer("⏳ Генерирую саммери...")

    try:
        summary = await _ai.generate_product_summary(name, text)
    except Exception as exc:
        await wait_msg.edit_text(f"⚠️ Ошибка GPT: {exc}")
        return

    await state.update_data(product_summary=summary)
    await state.set_state(ProductFSM.reviewing_summary)

    for chunk in _send_long(f"📋 <b>Саммери продукта «{name}»:</b>\n\n{summary}"):
        await wait_msg.edit_text(chunk, reply_markup=_summary_kb())


# ─── Summary review ─────────────────────────────────────────

@router.callback_query(WizardCB.filter(F.action == "edit"))
async def handle_edit_summary(callback: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state()
    if current == ProductFSM.reviewing_summary.state:
        await state.set_state(ProductFSM.editing_summary)
        await callback.message.answer(
            "✏️ Отправьте исправление текстом или голосом.\n"
            "Можно написать что изменить, например: «Убери второй пункт» или «Добавь раздел про монетизацию»"
        )
    await callback.answer()


@router.message(ProductFSM.editing_summary)
async def handle_summary_edit_input(message: Message, state: FSMContext, bot: Bot) -> None:
    instruction = await get_text_or_voice(message, bot)
    if not instruction:
        await message.answer("Отправьте текст или голосовое.")
        return

    data = await state.get_data()
    wait_msg = await message.answer("⏳ Применяю правки...")

    try:
        new_summary = await _ai.edit_text(data["product_summary"], instruction)
    except Exception as exc:
        await wait_msg.edit_text(f"⚠️ Ошибка: {exc}")
        return

    await state.update_data(product_summary=new_summary)
    await state.set_state(ProductFSM.reviewing_summary)
    name = data["product_name"]

    for chunk in _send_long(f"📋 <b>Обновлённое саммери «{name}»:</b>\n\n{new_summary}"):
        await wait_msg.edit_text(chunk, reply_markup=_summary_kb())


@router.callback_query(WizardCB.filter(F.action == "next"))
async def handle_next_step(callback: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state()

    if current == ProductFSM.reviewing_summary.state:
        # Save product to backend, then generate features
        data = await state.get_data()
        await callback.message.edit_text("⏳ Сохраняю продукт и генерирую фичи...")

        try:
            product = await _product_api.create({
                "name": data["product_name"],
                "goal": data.get("product_summary", ""),
            })
            product_id = product["id"]
            await state.update_data(product_id=product_id)
        except Exception as exc:
            await callback.message.edit_text(f"⚠️ Ошибка создания: {exc}")
            await callback.answer()
            return

        try:
            features_data = await _ai.generate_features_json(
                data["product_name"], data.get("product_summary", "")
            )
        except Exception as exc:
            await callback.message.edit_text(
                f"✅ Продукт создан, но ошибка генерации фичей: {exc}"
            )
            await callback.answer()
            return

        # Save features to backend
        saved_features = []
        for fd in features_data:
            try:
                feat = await _feature_api.create({
                    "product_id": product_id,
                    "name": fd["name"],
                    "description": fd.get("description", ""),
                })
                saved_features.append(feat)
            except Exception:
                pass

        await state.update_data(features=saved_features)
        await state.set_state(ProductFSM.reviewing_features)

        text = f"✅ Продукт <b>{data['product_name']}</b> создан!\n\n"
        text += "📋 <b>Сгенерированные фичи:</b>\n"
        for i, f in enumerate(saved_features, 1):
            text += f"\n{i}. <b>{f['name']}</b>"
            if f.get("description"):
                text += f"\n   {f['description'][:80]}"

        await callback.message.edit_text(
            text,
            reply_markup=_features_kb(saved_features, product_id),
        )

    await callback.answer()


# ─── Product view ────────────────────────────────────────────

@router.callback_query(ProductCB.filter())
async def handle_product(callback: CallbackQuery, callback_data: ProductCB, state: FSMContext) -> None:
    pid = callback_data.id

    if callback_data.action == "view":
        try:
            product = await _product_api.get_by_id(pid)
        except Exception as exc:
            await callback.answer(f"Ошибка: {exc}", show_alert=True)
            return

        text = (
            f"📦 <b>{product['name']}</b>\n"
            f"Статус: {product.get('status', 'draft')}\n"
            f"Версия: {product.get('version', 1)}\n"
        )
        if product.get("goal"):
            text += f"\n{product['goal'][:1000]}"

        await callback.message.edit_text(text, reply_markup=_product_detail_kb(pid))

    elif callback_data.action == "next":
        # Show features for this product
        try:
            features = await _feature_api.get_all(product_id=pid)
        except Exception:
            features = []

        await callback.message.edit_text(
            "📋 <b>Фичи:</b>" if features else "Фичей пока нет. Нажмите «Сгенерировать».",
            reply_markup=_features_kb(features, pid),
        )

    elif callback_data.action == "gen_features":
        await callback.message.edit_text("⏳ Генерирую фичи через AI...")
        try:
            product = await _product_api.get_by_id(pid)
            features_data = await _ai.generate_features_json(
                product["name"], product.get("goal", "")
            )
            saved = []
            for fd in features_data:
                try:
                    feat = await _feature_api.create({
                        "product_id": pid,
                        "name": fd["name"],
                        "description": fd.get("description", ""),
                    })
                    saved.append(feat)
                except Exception:
                    pass
            features = await _feature_api.get_all(product_id=pid)
        except Exception as exc:
            await callback.message.edit_text(f"⚠️ Ошибка: {exc}")
            await callback.answer()
            return

        text = "📋 <b>Фичи:</b>\n"
        for i, f in enumerate(features, 1):
            text += f"\n{i}. {f['name']}"

        await callback.message.edit_text(
            text,
            reply_markup=_features_kb(features, pid),
        )

    elif callback_data.action == "edit":
        await state.update_data(editing_product_id=pid)
        await state.set_state(ProductFSM.editing_text)
        await callback.message.answer(
            "✏️ Опишите изменения текстом или голосом:"
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
        text += f"\nСтатус: {feature.get('status', 'draft')}"

        if stories:
            text += "\n\n📖 <b>User Stories:</b>"

        await callback.message.edit_text(
            text,
            reply_markup=_stories_kb(stories, fid),
        )

    elif callback_data.action == "gen_stories":
        await callback.message.edit_text("⏳ Генерирую user stories через AI...")
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
            await callback.message.edit_text(f"⚠️ Ошибка: {exc}")
            await callback.answer()
            return

        text = f"🔹 <b>{feature['name']}</b>\n\n📖 <b>User Stories:</b>"
        await callback.message.edit_text(
            text,
            reply_markup=_stories_kb(stories, fid),
        )

    elif callback_data.action == "back":
        # Go back to product's feature list
        try:
            feature = await _feature_api.get_by_id(fid)
            pid = feature["product_id"]
            features = await _feature_api.get_all(product_id=pid)
        except Exception:
            await callback.answer("Ошибка", show_alert=True)
            return

        await callback.message.edit_text(
            "📋 <b>Фичи:</b>",
            reply_markup=_features_kb(features, pid),
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
                text="◀️ Назад",
                callback_data=FeatureCB(id=story.get("feature_id", ""), action="view").pack(),
            )],
        ])
        await callback.message.edit_text(text, reply_markup=kb)

    await callback.answer()


# ─── Generic edit handler ────────────────────────────────────

@router.message(ProductFSM.editing_text)
async def handle_generic_edit(message: Message, state: FSMContext, bot: Bot) -> None:
    text = await get_text_or_voice(message, bot)
    if not text:
        await message.answer("Отправьте текст или голосовое.")
        return

    data = await state.get_data()
    pid = data.get("editing_product_id")
    if pid:
        try:
            product = await _product_api.get_by_id(pid)
            new_goal = await _ai.edit_text(product.get("goal", ""), text)
            # Update via API (simplified — just update name/goal)
            # For now just show the result
            await message.answer(
                f"✅ Обновлённый текст:\n\n{new_goal[:3000]}",
                reply_markup=_product_detail_kb(pid),
            )
        except Exception as exc:
            await message.answer(f"⚠️ Ошибка: {exc}")

    await state.clear()
