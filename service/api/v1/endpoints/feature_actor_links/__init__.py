"""
Feature-Actor Links API router.

## Traceability
Feature: F003 — Actor Management
Scenarios: SC008
"""
from fastapi import APIRouter

router = APIRouter(prefix="/feature-actor-links", tags=["Feature-Actor Links"])

from api.v1.endpoints.feature_actor_links.get import router as get_router  # noqa: E402, F401
from api.v1.endpoints.feature_actor_links.post import router as post_router  # noqa: E402, F401
