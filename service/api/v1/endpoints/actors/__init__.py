"""
Actors API router.

## Traceability
Feature: F003 — Actor Management
Scenarios: SC007, SC008
"""
from fastapi import APIRouter

router = APIRouter(prefix="/actors", tags=["Actors"])

from api.v1.endpoints.actors.get import router as get_router  # noqa: E402, F401
from api.v1.endpoints.actors.post import router as post_router  # noqa: E402, F401
