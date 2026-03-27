"""
Test SC012: Attempt to create a second primary flow.

## Traceability
Feature: F005 — Flow Management
Scenario: SC012 — Duplicate Primary Flow Rejected

## BDD
Given a story already has a primary flow
When the user attempts to create another primary flow
Then the request is rejected with status 409 (conflict)
"""
import pytest


MERMAID_DIAGRAM = """graph TD
    A[Start] --> B[Step]
    B --> C[End]
"""


@pytest.mark.asyncio
async def test_duplicate_primary_flow(client, story):
    story_id = story["id"]

    # Given: a story already has a primary flow
    first_resp = await client.post(
        "/api/v1/flows",
        json={
            "product_id": story["product_id"],
            "feature_id": story["feature_id"],
            "story_id": story_id,
            "title": "Primary Flow",
            "flow_type": "primary",
            "mermaid_source": MERMAID_DIAGRAM,
        },
    )
    assert first_resp.status_code == 201

    # When: the user attempts to create another primary flow
    second_resp = await client.post(
        "/api/v1/flows",
        json={
            "product_id": story["product_id"],
            "feature_id": story["feature_id"],
            "story_id": story_id,
            "title": "Another Primary",
            "flow_type": "primary",
            "mermaid_source": MERMAID_DIAGRAM,
        },
    )

    # Then: the request is rejected with status 409 (conflict)
    assert second_resp.status_code == 409
