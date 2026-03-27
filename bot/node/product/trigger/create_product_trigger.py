"""Trigger: captures user input to start product creation.

## Traceability
Feature: F001 — Product Management
Scenarios: SC001
"""
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


class CreateProductTrigger:
    """Extracts product name and description from the FSM conversation."""

    async def run(self, message: Message, state: FSMContext) -> dict:
        """Return the accumulated product data stored in FSM state."""
        data = await state.get_data()
        return {
            "name": data.get("product_name", ""),
            "description": data.get("product_description", ""),
        }
