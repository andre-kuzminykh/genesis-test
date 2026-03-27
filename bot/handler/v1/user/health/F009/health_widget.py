"""Widget: backend health check.

## Traceability
Feature: F009 — Health Check
Scenarios: SC020
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from service.api.health_api import HealthAPI
from core.vocab import MSG_HEALTH_OK, MSG_HEALTH_FAIL

router = Router(name="health")


class HealthAnswer:
    """Answer: report backend health status."""

    async def run(self, event: Message, data: dict) -> None:
        if data.get("healthy"):
            await event.answer(MSG_HEALTH_OK)
        else:
            await event.answer(MSG_HEALTH_FAIL)


ANSWER_REGISTRY = {
    "success": HealthAnswer(),
    "error": HealthAnswer(),
}


class HealthTrigger:
    """Trigger: /health command received."""

    async def run(self, message: Message, state: FSMContext) -> dict:
        return {}


class HealthCode:
    """Code: ping the backend health endpoint."""

    def __init__(self, api: HealthAPI | None = None):
        self._api = api or HealthAPI()

    async def run(self, trigger_data: dict, state: FSMContext) -> dict:
        try:
            result = await self._api.check()
            return {"answer_name": "success", "data": {"healthy": True, **result}}
        except Exception:
            return {"answer_name": "error", "data": {"healthy": False}}


@router.message(Command("health"))
async def handle_health(message: Message, state: FSMContext) -> None:
    trigger = HealthTrigger()
    trigger_data = await trigger.run(message, state)
    code = HealthCode()
    code_result = await code.run(trigger_data, state)
    answer = ANSWER_REGISTRY[code_result["answer_name"]]
    await answer.run(event=message, data=code_result["data"])
