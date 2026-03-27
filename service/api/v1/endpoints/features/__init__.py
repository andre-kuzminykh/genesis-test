"""
Features API router.

## Traceability
Feature: F002 — Feature Management
Scenarios: SC004, SC005, SC006
"""
from fastapi import APIRouter

router = APIRouter(prefix="/features", tags=["Features"])

from api.v1.endpoints.features.get import router as get_router  # noqa: E402, F401
from api.v1.endpoints.features.post import router as post_router  # noqa: E402, F401
from api.v1.endpoints.features.put import router as put_router  # noqa: E402, F401
from api.v1.endpoints.features.delete import router as delete_router  # noqa: E402, F401
