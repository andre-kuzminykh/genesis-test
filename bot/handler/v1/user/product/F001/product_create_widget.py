"""Widget: create a new product via multi-step FSM flow.

## Traceability
Feature: F001 — Product Management
Scenarios: SC001
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from state.product_state import ProductFSM
from node.product.trigger.create_product_trigger import CreateProductTrigger
from node.product.code.create_product_code import CreateProductCode
from node.product.answer.product_created_answer import ProductCreatedAnswer
from node.common.answer.error_answer import ErrorAnswer
from core.vocab import MSG_ENTER_PRODUCT_NAME, MSG_ENTER_PRODUCT_DESCRIPTION

router = Router(name="product_create")

ANSWER_REGISTRY = {
    "success": ProductCreatedAnswer(),
    "error": ErrorAnswer(),
}


@router.message(Command("create_product"))
async def handle_create_product_start(message: Message, state: FSMContext) -> None:
    """Step 1: ask for the product name."""
    await state.set_state(ProductFSM.waiting_for_name)
    await message.answer(MSG_ENTER_PRODUCT_NAME)


@router.message(ProductFSM.waiting_for_name)
async def handle_product_name(message: Message, state: FSMContext) -> None:
    """Step 2: store name, ask for description."""
    await state.update_data(product_name=message.text)
    await state.set_state(ProductFSM.waiting_for_description)
    await message.answer(MSG_ENTER_PRODUCT_DESCRIPTION)


@router.message(ProductFSM.waiting_for_description)
async def handle_product_description(message: Message, state: FSMContext) -> None:
    """Step 3: store description, run Trigger -> Code -> Answer."""
    await state.update_data(product_description=message.text)

    trigger = CreateProductTrigger()
    trigger_data = await trigger.run(message, state)

    code = CreateProductCode()
    code_result = await code.run(trigger_data, state)

    answer = ANSWER_REGISTRY[code_result["answer_name"]]
    await answer.run(event=message, data=code_result["data"])

    await state.clear()
