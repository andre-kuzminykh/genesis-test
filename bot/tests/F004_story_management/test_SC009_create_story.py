"""SC009 — Create a new user story through the bot.

## Traceability
Feature: F004 — Story Management
Scenario: SC009 — Create story
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from service.api.story_api import StoryAPI


@pytest.mark.asyncio
async def test_story_api_create(mock_story_api):
    """Given valid story data,
    When StoryAPI.create is called,
    Then it should return the created story.
    """
    # Given
    story_data = {"title": "As a user, I want to log in", "feature_id": "feat-001"}

    # When
    result = await mock_story_api.create(story_data)

    # Then
    mock_story_api.create.assert_awaited_once_with(story_data)
    assert result["id"] == "1"
    assert result["title"] == "As a user..."


@pytest.mark.asyncio
async def test_story_api_create_handles_error():
    """Given the backend is unavailable,
    When StoryAPI.create is called,
    Then it should raise an exception.
    """
    # Given
    api = AsyncMock(spec=StoryAPI)
    api.create = AsyncMock(side_effect=Exception("Service unavailable"))

    # When / Then
    with pytest.raises(Exception, match="Service unavailable"):
        await api.create({"title": "Story"})


@pytest.mark.asyncio
async def test_story_list_returns_stories(mock_story_api):
    """Given stories exist in the backend,
    When StoryAPI.get_all is called,
    Then it should return a list of stories.
    """
    # Given / When
    result = await mock_story_api.get_all()

    # Then
    assert len(result) == 1
    assert result[0]["title"] == "As a user..."
