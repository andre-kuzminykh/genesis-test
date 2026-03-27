"""
Use Cases API router.

## Traceability
Feature: F006 — Use Case Management
Scenarios: SC013
"""
from fastapi import APIRouter

router = APIRouter(prefix="/use-cases", tags=["Use Cases"])

from api.v1.endpoints.use_cases.get import router as get_router  # noqa: E402, F401
from api.v1.endpoints.use_cases.post import router as post_router  # noqa: E402, F401
