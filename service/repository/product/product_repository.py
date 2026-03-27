"""
ProductRepository.

## Traceability
Feature: F001 — Product Management
Scenarios: SC001, SC002, SC003
"""
from model.product.product_model import ProductModel
from repository.base_repository import BaseRepository


class ProductRepository(BaseRepository[ProductModel]):
    def __init__(self):
        super().__init__(ProductModel)
