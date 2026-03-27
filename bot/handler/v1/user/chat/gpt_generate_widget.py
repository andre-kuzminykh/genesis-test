"""Widget: GPT generates product spec, features, or stories.

- /generate_spec — generate product specification from name+description
- /generate_features — suggest features for a product
- /generate_stories — generate user stories for a feature

## Traceability
Product: Telegram Product Engineer Bot
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from service.ai.openai_service import OpenAIService

router = Router(name="gpt_generate")

_ai = OpenAIService()


class GenSpecFSM(StatesGroup):
    waiting_name = State()
    waiting_desc = State()


class GenFeaturesFSM(StatesGroup):
    waiting_input = State()


class GenStoriesFSM(StatesGroup):
    waiting_input = State()


# ── /generate_spec ──────────────────────────────────────

@router.message(Command("generate_spec"))
async def gen_spec_start(message: Message, state: FSMContext) -> None:
    await state.set_state(GenSpecFSM.waiting_name)
    await message.answer("Введите название продукта:")


@router.message(GenSpecFSM.waiting_name, F.text)
async def gen_spec_name(message: Message, state: FSMContext) -> None:
    await state.update_data(gen_product_name=message.text)
    await state.set_state(GenSpecFSM.waiting_desc)
    await message.answer("Кратко опишите идею продукта:")


@router.message(GenSpecFSM.waiting_desc, F.text)
async def gen_spec_desc(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    name = data["gen_product_name"]
    desc = message.text or ""

    await message.answer("⏳ Генерирую спецификацию...")

    try:
        result = await _ai.generate_product_spec(name, desc)
    except Exception as exc:
        await message.answer(f"⚠️ OpenAI error: {exc}")
        await state.clear()
        return

    await state.clear()

    if len(result) > 4000:
        for i in range(0, len(result), 4000):
            await message.answer(result[i:i + 4000])
    else:
        await message.answer(result)


# ── /generate_features ──────────────────────────────────

@router.message(Command("generate_features"))
async def gen_features_start(message: Message, state: FSMContext) -> None:
    await state.set_state(GenFeaturesFSM.waiting_input)
    await message.answer("Опишите продукт и его цель (в одном сообщении):")


@router.message(GenFeaturesFSM.waiting_input, F.text)
async def gen_features_input(message: Message, state: FSMContext) -> None:
    await message.answer("⏳ Генерирую фичи...")

    try:
        result = await _ai.generate_features(message.text or "", "")
    except Exception as exc:
        await message.answer(f"⚠️ OpenAI error: {exc}")
        await state.clear()
        return

    await state.clear()
    await message.answer(result[:4000])


# ── /generate_stories ───────────────────────────────────

@router.message(Command("generate_stories"))
async def gen_stories_start(message: Message, state: FSMContext) -> None:
    await state.set_state(GenStoriesFSM.waiting_input)
    await message.answer("Введите название фичи и актора (например: 'Авторизация, Пользователь'):")


@router.message(GenStoriesFSM.waiting_input, F.text)
async def gen_stories_input(message: Message, state: FSMContext) -> None:
    parts = (message.text or "").split(",", 1)
    feature = parts[0].strip()
    actor = parts[1].strip() if len(parts) > 1 else "User"

    await message.answer("⏳ Генерирую user stories...")

    try:
        result = await _ai.generate_user_stories(feature, actor)
    except Exception as exc:
        await message.answer(f"⚠️ OpenAI error: {exc}")
        await state.clear()
        return

    await state.clear()
    await message.answer(result[:4000])
