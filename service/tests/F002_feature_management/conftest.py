"""
Feature fixtures for F002.

## Traceability
Feature: F002 — Feature Management
"""
import pytest_asyncio


@pytest_asyncio.fixture
async def product(client):
    resp = await client.post(
        "/api/v1/products",
        json={"name": "Test Product", "goal": "Test goal"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def feature(client, product):
    resp = await client.post(
        "/api/v1/features",
        json={"product_id": product["id"], "name": "Test Feature", "description": "A test feature"},
    )
    assert resp.status_code == 201
    return resp.json()
