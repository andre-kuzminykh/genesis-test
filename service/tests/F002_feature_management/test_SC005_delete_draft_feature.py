"""
Test SC005: Delete an unreferenced draft feature.

## Traceability
Feature: F002 — Feature Management
Scenario: SC005 — Delete Draft Feature

## BDD
Given a feature exists with no linked stories
When the user deletes the feature
Then the feature is removed and status 204 is returned
"""
import pytest


@pytest.mark.asyncio
async def test_delete_draft_feature(client, product, feature):
    feature_id = feature["id"]

    # Given: a feature exists with no linked stories

    # When: the user deletes the feature
    resp = await client.delete(f"/api/v1/features/{feature_id}")

    # Then: the feature is removed and status 204 is returned
    assert resp.status_code == 204

    # Verify the feature is gone
    get_resp = await client.get(f"/api/v1/features/{feature_id}")
    assert get_resp.status_code == 404
