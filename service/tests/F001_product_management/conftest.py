"""
Feature fixtures for F001.

## Traceability
Feature: F001 — Product Management
"""
import pytest_asyncio


@pytest_asyncio.fixture
async def product(client):
    resp = await client.post("/api/v1/products", json={"name": "Test Product", "goal": "Test"})
    assert resp.status_code == 201
    return resp.json()
