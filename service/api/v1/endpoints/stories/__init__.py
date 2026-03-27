"""
Stories API router.

## Traceability
Feature: F004 — User Story Management
Scenarios: SC009, SC010
"""
from fastapi import APIRouter

router = APIRouter(prefix="/stories", tags=["Stories"])

from api.v1.endpoints.stories.get import router as get_router  # noqa: E402, F401
from api.v1.endpoints.stories.post import router as post_router  # noqa: E402, F401
from api.v1.endpoints.stories.put import router as put_router  # noqa: E402, F401
