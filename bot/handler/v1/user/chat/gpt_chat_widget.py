"""Widget: GPT-powered chat assistant.

Users can ask product-engineering questions in free text.
- /ask — enter chat mode
- /stop — exit chat mode
- Any text while in chat mode goes to GPT

## Traceability
Product: Telegram Product Engineer Bot
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from state.chat_state import ChatFSM
from service.ai.openai_service import OpenAIService

router = Router(name="gpt_chat")

_ai = OpenAIService()

# Per-user conversation history kept in FSM data (in-memory, resets on /stop).
MAX_HISTORY = 20  # keep last N messages to control token usage


@router.message(Command("ask"))
async def handle_ask_start(message: Message, state: FSMContext) -> None:
    """Enter GPT chat mode."""
    await state.set_state(ChatFSM.chatting)
    await state.update_data(chat_history=[])
    await message.answer(
        "🤖 GPT-режим включён.\n"
        "Пишите любой вопрос — я отвечу с помощью AI.\n"
        "Для выхода: /stop"
    )


@router.message(ChatFSM.chatting, Command("stop"))
async def handle_ask_stop(message: Message, state: FSMContext) -> None:
    """Exit GPT chat mode."""
    await state.clear()
    await message.answer("GPT-режим выключен. Используйте /ask чтобы начать снова.")


@router.message(ChatFSM.chatting, F.text)
async def handle_chat_message(message: Message, state: FSMContext) -> None:
    """Forward user message to GPT and reply."""
    data = await state.get_data()
    history: list[dict] = data.get("chat_history", [])

    user_text = message.text or ""

    try:
        reply = await _ai.chat(user_text, history=history)
    except Exception as exc:
        await message.answer(f"⚠️ OpenAI error: {exc}")
        return

    # Update history
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": reply})

    # Trim history to save tokens
    if len(history) > MAX_HISTORY * 2:
        history = history[-(MAX_HISTORY * 2):]

    await state.update_data(chat_history=history)

    # Telegram message limit is 4096 chars
    if len(reply) > 4000:
        for i in range(0, len(reply), 4000):
            await message.answer(reply[i:i + 4000])
    else:
        await message.answer(reply)
