"""F001-specific fixtures.

## Traceability
Feature: F001 — Product Management
"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def sample_product() -> dict:
    return {
        "id": "prod-001",
        "name": "My Product",
        "description": "A great product",
        "status": "draft",
    }


@pytest.fixture
def sample_product_list() -> list[dict]:
    return [
        {"id": "prod-001", "name": "Product A"},
        {"id": "prod-002", "name": "Product B"},
    ]
