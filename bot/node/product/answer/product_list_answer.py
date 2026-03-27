"""Answer: renders the list of products.

## Traceability
Feature: F001 — Product Management
Scenarios: SC002
"""
from __future__ import annotations

from aiogram.types import Message

from core.vocab import MSG_PRODUCT_LIST_HEADER, MSG_EMPTY_LIST


class ProductListAnswer:
    """Format and send the product list to the user."""

    async def run(self, event: Message, data: list[dict]) -> None:
        if not data:
            await event.answer(MSG_EMPTY_LIST)
            return

        lines = [MSG_PRODUCT_LIST_HEADER]
        for idx, product in enumerate(data, start=1):
            lines.append(f"{idx}. {product.get('name', 'N/A')}")
        await event.answer("\n".join(lines))
