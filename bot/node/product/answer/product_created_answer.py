"""Answer: confirms successful product creation.

## Traceability
Feature: F001 — Product Management
Scenarios: SC001
"""
from aiogram.types import Message

from core.vocab import MSG_PRODUCT_CREATED


class ProductCreatedAnswer:
    """Send a confirmation message after product creation."""

    async def run(self, event: Message, data: dict) -> None:
        text = MSG_PRODUCT_CREATED.format(name=data.get("name", "Unknown"))
        await event.answer(text)
