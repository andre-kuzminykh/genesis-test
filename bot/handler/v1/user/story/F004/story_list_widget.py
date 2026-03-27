"""Widget: list user stories.

## Traceability
Feature: F004 — Story Management
Scenarios: SC008
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from service.api.story_api import StoryAPI
from core.vocab import MSG_STORY_LIST_HEADER, MSG_EMPTY_LIST
from node.common.answer.error_answer import ErrorAnswer

router = Router(name="story_list")


class StoryListAnswer:
    """Answer: render a list of user stories."""

    async def run(self, event: Message, data: list[dict]) -> None:
        if not data:
            await event.answer(MSG_EMPTY_LIST)
            return
        lines = [MSG_STORY_LIST_HEADER]
        for idx, story in enumerate(data, start=1):
            lines.append(f"{idx}. {story.get('title', 'N/A')}")
        await event.answer("\n".join(lines))


ANSWER_REGISTRY = {
    "success": StoryListAnswer(),
    "error": ErrorAnswer(),
}


class ListTrigger:
    """Trigger: /stories command received."""

    async def run(self, message: Message, state: FSMContext) -> dict:
        return {}


class ListCode:
    """Code: fetch all stories from the backend."""

    def __init__(self, api: StoryAPI | None = None):
        self._api = api or StoryAPI()

    async def run(self, trigger_data: dict, state: FSMContext) -> dict:
        try:
            stories = await self._api.get_all()
            return {"answer_name": "success", "data": stories}
        except Exception as exc:
            return {"answer_name": "error", "data": {"detail": str(exc)}}


@router.message(Command("stories"))
async def handle_story_list(message: Message, state: FSMContext) -> None:
    trigger = ListTrigger()
    trigger_data = await trigger.run(message, state)
    code = ListCode()
    code_result = await code.run(trigger_data, state)
    answer = ANSWER_REGISTRY[code_result["answer_name"]]
    await answer.run(event=message, data=code_result["data"])
