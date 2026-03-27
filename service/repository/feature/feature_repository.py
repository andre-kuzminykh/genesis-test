"""
FeatureRepository.

## Traceability
Feature: F002 — Feature Management
Scenarios: SC004, SC005, SC006
"""
from model.feature.feature_model import FeatureModel
from repository.base_repository import BaseRepository


class FeatureRepository(BaseRepository[FeatureModel]):
    def __init__(self):
        super().__init__(FeatureModel)
