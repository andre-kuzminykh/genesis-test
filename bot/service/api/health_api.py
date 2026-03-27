"""HTTP client for the Health backend.

## Traceability
Feature: F009
Scenarios: SC020
"""
from __future__ import annotations

import httpx

from core.config import config


class HealthAPI:
    def __init__(self, base_url: str | None = None):
        self._base_url = base_url or config.BACKEND_URL

    async def check(self) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get("/health")
            resp.raise_for_status()
            return resp.json()
