"""Answer: generic error response sent to the user.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

from aiogram.types import Message

from core.vocab import MSG_ERROR


class ErrorAnswer:
    """Send a generic error message."""

    async def run(self, event: Message, data: dict | None = None) -> None:
        detail = data.get("detail", MSG_ERROR) if data else MSG_ERROR
        await event.answer(detail)
