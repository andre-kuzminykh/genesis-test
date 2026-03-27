"""
Test SC002: Update an existing product.

## Traceability
Feature: F001 — Product Management
Scenario: SC002 — Update Product

## BDD
Given a product exists
When the user updates the product name or goal
Then the version increments and approval is invalidated if previously approved
"""
import pytest


@pytest.mark.asyncio
async def test_update_product_increments_version(client, product):
    product_id = product["id"]

    # Given: a product exists with version 1
    assert product["version"] == 1

    # When: the user updates the product name
    resp = await client.put(
        f"/api/v1/products/{product_id}",
        json={"name": "Updated Product", "goal": "Updated goal"},
    )

    # Then: the version increments
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == 2
    assert data["name"] == "Updated Product"


@pytest.mark.asyncio
async def test_update_approved_product_invalidates_approval(client, product):
    product_id = product["id"]

    # Given: a product is approved
    approve_resp = await client.post(f"/api/v1/products/{product_id}/approve")
    assert approve_resp.status_code == 200
    approved_data = approve_resp.json()
    assert approved_data["status"] == "approved"

    # When: the user updates the approved product
    resp = await client.put(
        f"/api/v1/products/{product_id}",
        json={"name": "Changed After Approval", "goal": "Changed"},
    )

    # Then: the approval is invalidated (status becomes 'changed' per Section 7)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "changed"
