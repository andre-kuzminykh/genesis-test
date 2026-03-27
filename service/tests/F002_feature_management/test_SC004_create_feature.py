"""
Test SC004: Create a feature linked to a product.

## Traceability
Feature: F002 — Feature Management
Scenario: SC004 — Create Feature

## BDD
Given a product exists
When the user creates a feature linked to the product
Then the feature is created with status 201
"""
import pytest


@pytest.mark.asyncio
async def test_create_feature(client, product):
    product_id = product["id"]

    # Given: a product exists

    # When: the user creates a feature linked to the product
    resp = await client.post(
        "/api/v1/features",
        json={"product_id": product_id, "name": "Login Feature", "description": "User login capability"},
    )

    # Then: the feature is created with status 201
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Login Feature"
    assert data["description"] == "User login capability"
    assert data["product_id"] == product_id
