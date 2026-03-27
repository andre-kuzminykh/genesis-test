"""SC001 — Create a new product through the bot.

## Traceability
Feature: F001 — Product Management
Scenario: SC001 — Create product
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from node.product.trigger.create_product_trigger import CreateProductTrigger
from node.product.code.create_product_code import CreateProductCode
from node.product.answer.product_created_answer import ProductCreatedAnswer


@pytest.mark.asyncio
async def test_create_product_trigger_extracts_data(mock_message, mock_state):
    """Given a user has entered product name and description,
    When the trigger runs,
    Then it should return the stored FSM data.
    """
    # Given
    mock_state.get_data = AsyncMock(return_value={
        "product_name": "Widget",
        "product_description": "A cool widget",
    })

    # When
    trigger = CreateProductTrigger()
    result = await trigger.run(mock_message, mock_state)

    # Then
    assert result["name"] == "Widget"
    assert result["description"] == "A cool widget"


@pytest.mark.asyncio
async def test_create_product_code_calls_api(mock_product_api):
    """Given valid product data,
    When the code node runs,
    Then it should call ProductAPI.create and return success.
    """
    # Given
    trigger_data = {"name": "Widget", "description": "A cool widget"}

    # When
    code = CreateProductCode(api=mock_product_api)
    result = await code.run(trigger_data)

    # Then
    mock_product_api.create.assert_awaited_once_with(trigger_data)
    assert result["answer_name"] == "success"
    assert result["data"]["name"] == "TestProduct"


@pytest.mark.asyncio
async def test_create_product_code_handles_error():
    """Given the backend is unavailable,
    When the code node runs,
    Then it should return an error answer.
    """
    # Given
    api = AsyncMock()
    api.create = AsyncMock(side_effect=Exception("Connection refused"))

    # When
    code = CreateProductCode(api=api)
    result = await code.run({"name": "X", "description": "Y"})

    # Then
    assert result["answer_name"] == "error"
    assert "Connection refused" in result["data"]["detail"]


@pytest.mark.asyncio
async def test_product_created_answer_sends_message(mock_message):
    """Given a successfully created product,
    When the answer node runs,
    Then it should send a confirmation message.
    """
    # Given
    data = {"name": "Widget"}

    # When
    answer = ProductCreatedAnswer()
    await answer.run(event=mock_message, data=data)

    # Then
    mock_message.answer.assert_awaited_once()
    call_text = mock_message.answer.call_args[0][0]
    assert "Widget" in call_text
