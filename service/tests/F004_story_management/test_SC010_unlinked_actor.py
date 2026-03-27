"""
Test SC010: Create a story with an unlinked actor.

## Traceability
Feature: F004 — Story Management
Scenario: SC010 — Unlinked Actor Rejected

## BDD
Given a feature exists and an actor is NOT linked to it
When the user creates a story referencing the unlinked actor
Then the request is rejected with status 422
"""
import pytest


@pytest.mark.asyncio
async def test_create_story_with_unlinked_actor(client, feature, actor):
    feature_id = feature["id"]
    actor_id = actor["id"]

    # Given: a feature exists and an actor is NOT linked to it
    # (actor fixture exists but linked_actor fixture is not used)

    # When: the user creates a story referencing the unlinked actor
    resp = await client.post(
        "/api/v1/stories",
        json={
            "product_id": feature["product_id"],
            "feature_id": feature_id,
            "title": "User can log in",
            "actor_id": actor_id,
            "want_text": "log in to the system",
            "benefit_text": "access protected resources",
        },
    )

    # Then: the request is rejected with status 422
    assert resp.status_code == 422
