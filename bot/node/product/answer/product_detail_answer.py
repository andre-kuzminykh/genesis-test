"""Answer: renders a single product's details.

## Traceability
Feature: F001 — Product Management
Scenarios: SC003
"""
from __future__ import annotations

from aiogram.types import Message

from core.vocab import MSG_PRODUCT_DETAIL


class ProductDetailAnswer:
    """Format and send product details to the user."""

    async def run(self, event: Message, data: dict) -> None:
        text = MSG_PRODUCT_DETAIL.format(
            name=data.get("name", "N/A"),
            status=data.get("status", "N/A"),
            description=data.get("description", "N/A"),
        )
        await event.answer(text)
