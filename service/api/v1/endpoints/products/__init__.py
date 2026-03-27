"""
Products API router.

## Traceability
Feature: F001 — Product Management
Scenarios: SC001, SC002, SC003
"""
from fastapi import APIRouter

router = APIRouter(prefix="/products", tags=["Products"])

from api.v1.endpoints.products.get import router as get_router  # noqa: E402, F401
from api.v1.endpoints.products.post import router as post_router  # noqa: E402, F401
from api.v1.endpoints.products.put import router as put_router  # noqa: E402, F401
from api.v1.endpoints.products.delete import router as delete_router  # noqa: E402, F401
