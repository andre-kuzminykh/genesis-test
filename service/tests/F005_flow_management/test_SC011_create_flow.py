"""
Test SC011: Create a primary flow with Mermaid diagram.

## Traceability
Feature: F005 — Flow Management
Scenario: SC011 — Create Primary Flow

## BDD
Given a story exists
When the user creates a primary flow with a Mermaid diagram
Then the flow is created with status 201
"""
import pytest


MERMAID_DIAGRAM = """graph TD
    A[Start] --> B[Login]
    B --> C[Dashboard]
    C --> D[End]
"""


@pytest.mark.asyncio
async def test_create_primary_flow(client, story):
    story_id = story["id"]

    # Given: a story exists

    # When: the user creates a primary flow with a Mermaid diagram
    resp = await client.post(
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

    # Then: the flow is created with status 201
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Primary Flow"
    assert data["flow_type"] == "primary"
    assert data["mermaid_source"] == MERMAID_DIAGRAM
