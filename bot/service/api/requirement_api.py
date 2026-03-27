"""HTTP client for the Requirement backend.

## Traceability
Feature: F007
Scenarios: SC014, SC015
"""
from __future__ import annotations

import httpx

from core.config import config


class RequirementAPI:
    def __init__(self, base_url: str | None = None):
        self._base_url = base_url or config.BACKEND_URL

    async def create(self, data: dict) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.post("/requirements", json=data)
            resp.raise_for_status()
            return resp.json()

    async def get_by_id(self, entity_id: str) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get(f"/requirements/{entity_id}")
            resp.raise_for_status()
            return resp.json()

    async def get_all(self, **params) -> list[dict]:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get("/requirements", params=params)
            resp.raise_for_status()
            return resp.json()

    async def approve(self, entity_id: str) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.post(f"/requirements/{entity_id}/approve")
            resp.raise_for_status()
            return resp.json()
