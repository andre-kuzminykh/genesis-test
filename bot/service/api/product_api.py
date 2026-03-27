"""HTTP client for the Product backend.

## Traceability
Feature: F001
Scenarios: SC001, SC002, SC003
"""
import httpx

from core.config import config


class ProductAPI:
    def __init__(self, base_url: str | None = None):
        self._base_url = base_url or config.BACKEND_URL

    async def create(self, data: dict) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.post("/products", json=data)
            resp.raise_for_status()
            return resp.json()

    async def get_by_id(self, entity_id: str) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get(f"/products/{entity_id}")
            resp.raise_for_status()
            return resp.json()

    async def get_all(self, **params) -> list[dict]:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get("/products", params=params)
            resp.raise_for_status()
            return resp.json()

    async def approve(self, entity_id: str) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.post(f"/products/{entity_id}/approve")
            resp.raise_for_status()
            return resp.json()
