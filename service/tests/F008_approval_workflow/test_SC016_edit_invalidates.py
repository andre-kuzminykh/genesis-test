"""
Test SC016: Editing an approved entity invalidates approval.

## Traceability
Feature: F008 — Approval Workflow
Scenario: SC016 — Edit Invalidates Approval

## BDD
Given a product is approved
When the user edits the product
Then the status reverts to 'draft' and the approval is invalidated
"""
import pytest


@pytest.mark.asyncio
async def test_edit_invalidates_approval(client):
    # Given: a product is approved
    create_resp = await client.post(
        "/api/v1/products",
        json={"name": "Stable Product", "goal": "Stability"},
    )
    assert create_resp.status_code == 201
    product = create_resp.json()
    product_id = product["id"]

    approve_resp = await client.post(f"/api/v1/products/{product_id}/approve")
    assert approve_resp.status_code == 200
    approved = approve_resp.json()
    assert approved["status"] == "approved"
    original_approved_version = approved["approved_version"]

    # When: the user edits the product
    update_resp = await client.put(
        f"/api/v1/products/{product_id}",
        json={"name": "Modified Product", "goal": "Changed goal"},
    )

    # Then: the status becomes 'changed' and the approval is invalidated (Section 7)
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["status"] == "changed"
    assert data["version"] > original_approved_version
