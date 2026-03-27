"""
Requirements API router.

## Traceability
Feature: F007 — Requirement Management
Scenarios: SC014
"""
from fastapi import APIRouter

router = APIRouter(prefix="/requirements", tags=["Requirements"])

from api.v1.endpoints.requirements.get import router as get_router  # noqa: E402, F401
from api.v1.endpoints.requirements.post import router as post_router  # noqa: E402, F401
