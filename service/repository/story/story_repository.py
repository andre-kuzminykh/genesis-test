"""
StoryRepository.

## Traceability
Feature: F004 — User Story Management
Scenarios: SC009, SC010
"""
from model.story.story_model import StoryModel
from repository.base_repository import BaseRepository


class StoryRepository(BaseRepository[StoryModel]):
    def __init__(self):
        super().__init__(StoryModel)
