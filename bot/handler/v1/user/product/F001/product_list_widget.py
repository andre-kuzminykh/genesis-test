"""Widget: list all products.

## Traceability
Feature: F001 — Product Management
Scenarios: SC002
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from service.api.product_api import ProductAPI
from node.product.answer.product_list_answer import ProductListAnswer
from node.common.answer.error_answer import ErrorAnswer

router = Router(name="product_list")

ANSWER_REGISTRY = {
    "success": ProductListAnswer(),
    "error": ErrorAnswer(),
}


class ListTrigger:
    """Trigger: /products command received."""

    async def run(self, message: Message, state: FSMContext) -> dict:
        return {}


class ListCode:
    """Code: fetch all products from the backend."""

    def __init__(self, api: ProductAPI | None = None):
        self._api = api or ProductAPI()

    async def run(self, trigger_data: dict, state: FSMContext) -> dict:
        try:
            products = await self._api.get_all()
            return {"answer_name": "success", "data": products}
        except Exception as exc:
            return {"answer_name": "error", "data": {"detail": str(exc)}}


@router.message(Command("products"))
async def handle_product_list(message: Message, state: FSMContext) -> None:
    trigger = ListTrigger()
    trigger_data = await trigger.run(message, state)
    code = ListCode()
    code_result = await code.run(trigger_data, state)
    answer = ANSWER_REGISTRY[code_result["answer_name"]]
    await answer.run(event=message, data=code_result["data"])
