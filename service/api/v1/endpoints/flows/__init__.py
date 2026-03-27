"""
Flows API router.

## Traceability
Feature: F005 — User Flow Management
Scenarios: SC011, SC012
"""
from fastapi import APIRouter

router = APIRouter(prefix="/flows", tags=["Flows"])

from api.v1.endpoints.flows.get import router as get_router  # noqa: E402, F401
from api.v1.endpoints.flows.post import router as post_router  # noqa: E402, F401
from api.v1.endpoints.flows.put import router as put_router  # noqa: E402, F401
