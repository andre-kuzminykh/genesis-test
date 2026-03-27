"""Widget: /start command — welcome message with available commands.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="start")

HELP_TEXT = (
    "👋 <b>Product Engineer Bot</b>\n\n"
    "🤖 <b>AI-команды:</b>\n"
    "/ask — GPT-чат (свободные вопросы)\n"
    "/generate_spec — сгенерировать спецификацию продукта\n"
    "/generate_features — предложить фичи\n"
    "/generate_stories — сгенерировать user stories\n\n"
    "📦 <b>Управление:</b>\n"
    "/products — список продуктов\n"
    "/create_product — создать продукт\n"
    "/features — список фич\n"
    "/stories — список историй\n"
    "/health — здоровье спецификации\n\n"
    "Начните с /ask или /create_product"
)


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(HELP_TEXT)
