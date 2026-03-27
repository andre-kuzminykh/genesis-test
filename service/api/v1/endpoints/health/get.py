"""
Health GET endpoints.

## Traceability
Feature: F009 — Specification Health Dashboard
Scenarios: SC017 (product health check)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.health import router
from service.health.health_service import HealthService
from core.database import db_connect

_service = HealthService()


@router.get("/products/{product_id}")
async def get_product_health(
    product_id: str,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Get specification health report for a product."""
    health = await _service.get_health(session, product_id)
    violations = []
    for fid in health["features_without_approved_stories"]:
        violations.append({"type": "feature_without_approved_stories", "entity_id": fid})
    for sid in health["stories_without_actors"]:
        violations.append({"type": "story_without_actor", "entity_id": sid})
    for sid in health["stories_without_primary_flow"]:
        violations.append({"type": "story_without_primary_flow", "entity_id": sid})
    for fid in health["approved_flows_without_use_cases"]:
        violations.append({"type": "approved_flow_without_use_cases", "entity_id": fid})
    for uid in health["approved_use_cases_without_requirements"]:
        violations.append({"type": "approved_use_case_without_requirements", "entity_id": uid})
    return {
        "product_id": product_id,
        "violations": violations,
        "totals": {
            "features": health["total_features"],
            "stories": health["total_stories"],
            "flows": health["total_flows"],
            "use_cases": health["total_use_cases"],
            "requirements": health["total_requirements"],
        },
    }
