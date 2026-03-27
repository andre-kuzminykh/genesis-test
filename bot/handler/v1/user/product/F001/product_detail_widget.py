"""Widget: view product details via inline callback.

## Traceability
Feature: F001 — Product Management
Scenarios: SC003
"""
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from callback.navigation_cb import EntityActionCallback
from service.api.product_api import ProductAPI
from node.product.answer.product_detail_answer import ProductDetailAnswer
from node.common.answer.error_answer import ErrorAnswer

router = Router(name="product_detail")

ANSWER_REGISTRY = {
    "success": ProductDetailAnswer(),
    "error": ErrorAnswer(),
}


class DetailTrigger:
    """Trigger: extract product_id from the callback data."""

    async def run(self, callback: CallbackQuery, cb_data: EntityActionCallback) -> dict:
        return {"product_id": cb_data.entity_id}


class DetailCode:
    """Code: fetch product by id from the backend."""

    def __init__(self, api: ProductAPI | None = None):
        self._api = api or ProductAPI()

    async def run(self, trigger_data: dict, state: FSMContext) -> dict:
        try:
            product = await self._api.get_by_id(trigger_data["product_id"])
            return {"answer_name": "success", "data": product}
        except Exception as exc:
            return {"answer_name": "error", "data": {"detail": str(exc)}}


@router.callback_query(EntityActionCallback.filter())
async def handle_product_detail(
    callback: CallbackQuery,
    callback_data: EntityActionCallback,
    state: FSMContext,
) -> None:
    if callback_data.entity_type != "product" or callback_data.action != "view":
        return
    trigger = DetailTrigger()
    trigger_data = await trigger.run(callback, callback_data)
    code = DetailCode()
    code_result = await code.run(trigger_data, state)
    answer = ANSWER_REGISTRY[code_result["answer_name"]]
    await answer.run(event=callback.message, data=code_result["data"])
    await callback.answer()
