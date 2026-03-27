"""
Test SC006: Delete a feature that has linked stories.

## Traceability
Feature: F002 — Feature Management
Scenario: SC006 — Delete Referenced Feature

## BDD
Given a feature exists with linked stories
When the user attempts to delete the feature
Then the deletion is rejected with status 409 (conflict)
"""
import pytest


@pytest.mark.asyncio
async def test_delete_referenced_feature(client, product, feature):
    product_id = product["id"]
    feature_id = feature["id"]

    # Given: a feature exists with linked stories
    # Create an actor first
    actor_resp = await client.post(
        "/api/v1/actors",
        json={"product_id": product_id, "name": "End User", "description": "A regular user"},
    )
    assert actor_resp.status_code == 201
    actor = actor_resp.json()

    # Link the actor to the feature
    link_resp = await client.post(
        "/api/v1/feature-actor-links",
        json={"product_id": product_id, "feature_id": feature_id, "actor_id": actor["id"]},
    )
    assert link_resp.status_code in (200, 201)

    # Create a story linked to the feature
    story_resp = await client.post(
        "/api/v1/stories",
        json={
            "product_id": product_id,
            "feature_id": feature_id,
            "title": "User can log in",
            "actor_id": actor["id"],
            "want_text": "log in",
            "benefit_text": "access the system",
        },
    )
    assert story_resp.status_code == 201

    # When: the user attempts to delete the feature
    resp = await client.delete(f"/api/v1/features/{feature_id}")

    # Then: the deletion is rejected with status 409 (conflict)
    assert resp.status_code == 409
