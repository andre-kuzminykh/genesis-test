"""
Test SC017: Health dashboard returns violations.

## Traceability
Feature: F009 — Spec Health
Scenario: SC017 — Health Dashboard

## BDD
Given the system contains products with potential specification issues
When the user requests the health dashboard
Then the response includes a list of violations
"""
import pytest


@pytest.mark.asyncio
async def test_health_dashboard_returns_violations(client):
    # Given: the system contains a product with potential specification issues
    create_resp = await client.post(
        "/api/v1/products",
        json={"name": "Incomplete Product", "goal": "Needs work"},
    )
    assert create_resp.status_code == 201
    product = create_resp.json()
    product_id = product["id"]

    # When: the user requests the health dashboard
    resp = await client.get(f"/api/v1/health/products/{product_id}")

    # Then: the response includes a list of violations
    assert resp.status_code == 200
    data = resp.json()
    assert "violations" in data
    assert isinstance(data["violations"], list)
