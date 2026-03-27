"""HTTP client for the UseCase backend.

## Traceability
Feature: F006
Scenarios: SC012, SC013
"""
import httpx

from core.config import config


class UseCaseAPI:
    def __init__(self, base_url: str | None = None):
        self._base_url = base_url or config.BACKEND_URL

    async def create(self, data: dict) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.post("/use-cases", json=data)
            resp.raise_for_status()
            return resp.json()

    async def get_by_id(self, entity_id: str) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get(f"/use-cases/{entity_id}")
            resp.raise_for_status()
            return resp.json()

    async def get_all(self, **params) -> list[dict]:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get("/use-cases", params=params)
            resp.raise_for_status()
            return resp.json()

    async def approve(self, entity_id: str) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.post(f"/use-cases/{entity_id}/approve")
            resp.raise_for_status()
            return resp.json()
