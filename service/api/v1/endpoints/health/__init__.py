"""
Health API router.

## Traceability
Feature: F009 — Specification Health Dashboard
Scenarios: SC017
"""
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])

from api.v1.endpoints.health.get import router as get_router  # noqa: E402, F401
