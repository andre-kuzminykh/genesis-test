"""
Feature fixtures for F005.

## Traceability
Feature: F005 — Flow Management
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
    resp = await client.post(
        "/api/v1/feature-actor-links",
        json={"product_id": product["id"], "feature_id": feature["id"], "actor_id": actor["id"]},
    )
    assert resp.status_code in (200, 201)
    return actor


@pytest_asyncio.fixture
async def story(client, product, feature, linked_actor):
    resp = await client.post(
        "/api/v1/stories",
        json={
            "product_id": product["id"],
            "feature_id": feature["id"],
            "title": "Test Story",
            "actor_id": linked_actor["id"],
            "want_text": "perform action",
            "benefit_text": "get benefit",
        },
    )
    assert resp.status_code == 201
    return resp.json()
