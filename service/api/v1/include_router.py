"""
Router registration for the FastAPI application.

## Traceability
Feature: F001-F009 — All features
"""
from core.config import config


def include_routers(app):
    from api.v1.endpoints.products import router as products_router
    from api.v1.endpoints.features import router as features_router
    from api.v1.endpoints.actors import router as actors_router
    from api.v1.endpoints.feature_actor_links import router as feature_actor_links_router
    from api.v1.endpoints.stories import router as stories_router
    from api.v1.endpoints.flows import router as flows_router
    from api.v1.endpoints.use_cases import router as use_cases_router
    from api.v1.endpoints.requirements import router as requirements_router
    from api.v1.endpoints.health import router as health_router

    app.include_router(products_router, prefix=config.API_V1_PREFIX)
    app.include_router(features_router, prefix=config.API_V1_PREFIX)
    app.include_router(actors_router, prefix=config.API_V1_PREFIX)
    app.include_router(feature_actor_links_router, prefix=config.API_V1_PREFIX)
    app.include_router(stories_router, prefix=config.API_V1_PREFIX)
    app.include_router(flows_router, prefix=config.API_V1_PREFIX)
    app.include_router(use_cases_router, prefix=config.API_V1_PREFIX)
    app.include_router(requirements_router, prefix=config.API_V1_PREFIX)
    app.include_router(health_router, prefix=config.API_V1_PREFIX)
