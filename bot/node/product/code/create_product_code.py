"""Code: calls the backend to persist a new product.

## Traceability
Feature: F001 — Product Management
Scenarios: SC001
"""
from __future__ import annotations

from service.api.product_api import ProductAPI


class CreateProductCode:
    """Business logic — delegate to ProductAPI and choose the answer."""

    def __init__(self, api: ProductAPI | None = None):
        self._api = api or ProductAPI()

    async def run(self, trigger_data: dict, state=None) -> dict:
        try:
            product = await self._api.create(trigger_data)
            return {"answer_name": "success", "data": product}
        except Exception as exc:
            return {"answer_name": "error", "data": {"detail": str(exc)}}
