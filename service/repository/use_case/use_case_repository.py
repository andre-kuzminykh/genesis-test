"""
UseCaseRepository.

## Traceability
Feature: F006 — Use Case Management
Scenarios: SC013
"""
from model.use_case.use_case_model import UseCaseModel
from repository.base_repository import BaseRepository


class UseCaseRepository(BaseRepository[UseCaseModel]):
    def __init__(self):
        super().__init__(UseCaseModel)
