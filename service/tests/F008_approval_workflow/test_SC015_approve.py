"""
Test SC015: Approve an entity sets status and approved_version.

## Traceability
Feature: F008 — Approval Workflow
Scenario: SC015 — Approve Entity

## BDD
Given a product exists in draft status
When the user approves the product
Then the status is set to 'approved' and approved_version matches the current version
"""
import pytest


@pytest.mark.asyncio
async def test_approve_sets_status_and_version(client):
    # Given: a product exists in draft status
    create_resp = await client.post(
        "/api/v1/products",
        json={"name": "Approvable Product", "goal": "To be approved"},
    )
    assert create_resp.status_code == 201
    product = create_resp.json()
    product_id = product["id"]
    assert product["status"] == "draft"

    # When: the user approves the product
    approve_resp = await client.post(f"/api/v1/products/{product_id}/approve")

    # Then: the status is set to 'approved' and approved_version matches current version
    assert approve_resp.status_code == 200
    data = approve_resp.json()
    assert data["status"] == "approved"
    assert data["approved_version"] is not None
    assert data["approved_version"] == data["version"]
