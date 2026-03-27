"""
Test SC003: Approve a product.

## Traceability
Feature: F001 — Product Management
Scenario: SC003 — Approve Product

## BDD
Given a product exists in draft status
When the user approves the product
Then the status becomes 'approved' and approved_version is set
"""
import pytest


@pytest.mark.asyncio
async def test_approve_product(client, product):
    product_id = product["id"]

    # Given: a product exists in draft status
    assert product["status"] == "draft"

    # When: the user approves the product
    resp = await client.post(f"/api/v1/products/{product_id}/approve")

    # Then: the status becomes 'approved' and approved_version is set
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"
    assert data["approved_version"] == data["version"]
