"""
RequirementRepository.

## Traceability
Feature: F007 — Requirement Management
Scenarios: SC014
"""
from model.requirement.requirement_model import RequirementModel
from repository.base_repository import BaseRepository


class RequirementRepository(BaseRepository[RequirementModel]):
    def __init__(self):
        super().__init__(RequirementModel)
