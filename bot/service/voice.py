"""Voice message transcription helper.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

import tempfile
import os

from aiogram.types import Message

from service.ai.openai_service import OpenAIService


async def transcribe_message(message: Message, bot) -> str:
    """Download voice/audio from Telegram message and transcribe via Whisper."""
    ai = OpenAIService()

    if message.voice:
        file = await bot.get_file(message.voice.file_id)
    elif message.audio:
        file = await bot.get_file(message.audio.file_id)
    else:
        return message.text or ""

    tmp = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
    try:
        await bot.download_file(file.file_path, tmp.name)
        text = await ai.transcribe_voice(tmp.name)
        return text
    finally:
        os.unlink(tmp.name)


async def get_text_or_voice(message: Message, bot) -> str:
    """Extract text from a text message or transcribe voice."""
    if message.text:
        return message.text
    if message.voice or message.audio:
        return await transcribe_message(message, bot)
    return ""
