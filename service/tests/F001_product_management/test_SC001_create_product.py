"""
Test SC001: Create a new product.

## Traceability
Feature: F001 — Product Management
Scenario: SC001 — Create Product

## BDD
Given the system has no products
When a user creates a product with a name and goal
Then the product is created with status 'draft' and version 1
"""
import pytest


@pytest.mark.asyncio
async def test_create_product(client):
    # Given: no products exist in the system

    # When: a user creates a product with a name and goal
    resp = await client.post(
        "/api/v1/products",
        json={"name": "My Product", "goal": "Deliver value"},
    )

    # Then: the product is created with status 'draft' and version 1
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Product"
    assert data["goal"] == "Deliver value"
    assert data["status"] == "draft"
    assert data["version"] == 1
