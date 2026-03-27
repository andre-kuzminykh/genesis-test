"""Widget: list features for a product.

## Traceability
Feature: F002 — Feature Management
Scenarios: SC004
"""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from service.api.feature_api import FeatureAPI
from core.vocab import MSG_FEATURE_LIST_HEADER, MSG_EMPTY_LIST
from node.common.answer.error_answer import ErrorAnswer

router = Router(name="feature_list")


class FeatureListAnswer:
    """Answer: render a list of features."""

    async def run(self, event: Message, data: dict) -> None:
        features = data.get("features", [])
        product_name = data.get("product_name", "N/A")
        if not features:
            await event.answer(MSG_EMPTY_LIST)
            return
        lines = [MSG_FEATURE_LIST_HEADER.format(product_name=product_name)]
        for idx, feat in enumerate(features, start=1):
            lines.append(f"{idx}. {feat.get('name', 'N/A')}")
        await event.answer("\n".join(lines))


ANSWER_REGISTRY = {
    "success": FeatureListAnswer(),
    "error": ErrorAnswer(),
}


class ListTrigger:
    """Trigger: /features command received."""

    async def run(self, message: Message, state: FSMContext) -> dict:
        return {}


class ListCode:
    """Code: fetch all features from the backend."""

    def __init__(self, api: FeatureAPI | None = None):
        self._api = api or FeatureAPI()

    async def run(self, trigger_data: dict, state: FSMContext) -> dict:
        try:
            features = await self._api.get_all()
            return {
                "answer_name": "success",
                "data": {"features": features, "product_name": "All"},
            }
        except Exception as exc:
            return {"answer_name": "error", "data": {"detail": str(exc)}}


@router.message(Command("features"))
async def handle_feature_list(message: Message, state: FSMContext) -> None:
    trigger = ListTrigger()
    trigger_data = await trigger.run(message, state)
    code = ListCode()
    code_result = await code.run(trigger_data, state)
    answer = ANSWER_REGISTRY[code_result["answer_name"]]
    await answer.run(event=message, data=code_result["data"])
