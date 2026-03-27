"""
Test SC009: Create a story with a linked actor.

## Traceability
Feature: F004 — Story Management
Scenario: SC009 — Create Story

## BDD
Given a feature exists and an actor is linked to it
When the user creates a story referencing the linked actor
Then the story is created with status 201
"""
import pytest


@pytest.mark.asyncio
async def test_create_story_with_linked_actor(client, feature, linked_actor):
    feature_id = feature["id"]
    actor_id = linked_actor["id"]

    # Given: a feature exists and an actor is linked to it

    # When: the user creates a story referencing the linked actor
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

    # Then: the story is created with status 201
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "User can log in"
    assert data["actor_id"] == actor_id
    assert data["want_text"] == "log in to the system"
    assert data["benefit_text"] == "access protected resources"
