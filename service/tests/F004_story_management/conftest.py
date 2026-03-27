"""
Feature fixtures for F004.

## Traceability
Feature: F004 — Story Management
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


@pytest_asyncio.fixture
async def actor(client, product):
    resp = await client.post(
        "/api/v1/actors",
        json={"product_id": product["id"], "name": "End User", "description": "A regular user"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def linked_actor(client, product, feature, actor):
    """Actor linked to the feature."""
    resp = await client.post(
        "/api/v1/feature-actor-links",
        json={"product_id": product["id"], "feature_id": feature["id"], "actor_id": actor["id"]},
    )
    assert resp.status_code in (200, 201)
    return actor
