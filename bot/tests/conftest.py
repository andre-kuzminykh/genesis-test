"""Shared test fixtures — mocks for Message, FSMContext, and API clients.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_message() -> MagicMock:
    """Fake aiogram Message with an async .answer() method."""
    msg = MagicMock()
    msg.text = ""
    msg.answer = AsyncMock()
    msg.chat = MagicMock(id=1)
    msg.from_user = MagicMock(id=1, first_name="Test")
    return msg


@pytest.fixture
def mock_state() -> AsyncMock:
    """Fake FSMContext."""
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


@pytest.fixture
def mock_product_api() -> AsyncMock:
    """Fake ProductAPI."""
    api = AsyncMock()
    api.create = AsyncMock(return_value={"id": "1", "name": "TestProduct", "status": "draft", "description": "desc"})
    api.get_all = AsyncMock(return_value=[{"id": "1", "name": "TestProduct"}])
    api.get_by_id = AsyncMock(return_value={"id": "1", "name": "TestProduct", "status": "draft", "description": "desc"})
    api.approve = AsyncMock(return_value={"id": "1", "name": "TestProduct", "status": "approved"})
    return api


@pytest.fixture
def mock_story_api() -> AsyncMock:
    """Fake StoryAPI."""
    api = AsyncMock()
    api.create = AsyncMock(return_value={"id": "1", "title": "As a user...", "status": "draft"})
    api.get_all = AsyncMock(return_value=[{"id": "1", "title": "As a user..."}])
    api.get_by_id = AsyncMock(return_value={"id": "1", "title": "As a user...", "status": "draft"})
    api.approve = AsyncMock(return_value={"id": "1", "title": "As a user...", "status": "approved"})
    return api
