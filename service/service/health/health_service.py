"""
HealthService — specification health checks.

## Traceability
Feature: F009 — Specification Health Dashboard
Scenarios: SC017

## Business context
Section 32 — health checks for spec completeness.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from repository.feature.feature_repository import FeatureRepository
from repository.story.story_repository import StoryRepository
from repository.flow.flow_repository import FlowRepository
from repository.use_case.use_case_repository import UseCaseRepository
from repository.requirement.requirement_repository import RequirementRepository


class HealthService:
    def __init__(self):
        self._feature_repo = FeatureRepository()
        self._story_repo = StoryRepository()
        self._flow_repo = FlowRepository()
        self._uc_repo = UseCaseRepository()
        self._req_repo = RequirementRepository()

    async def get_health(self, session: AsyncSession, product_id: str) -> dict:
        features = await self._feature_repo.get_all(session, product_id=product_id)
        stories = await self._story_repo.get_all(session, product_id=product_id)
        flows = await self._flow_repo.get_all(session, product_id=product_id)
        use_cases = await self._uc_repo.get_all(session, product_id=product_id)
        requirements = await self._req_repo.get_all(session, product_id=product_id)

        # Features without approved stories
        approved_story_fids = {s.feature_id for s in stories if s.status == "approved"}
        features_no_stories = [f.id for f in features if f.id not in approved_story_fids]

        # Stories without actors
        stories_no_actors = [s.id for s in stories if not s.actor_id]

        # Stories without primary flow
        stories_with_primary = {
            f.story_id for f in flows if f.flow_type == "primary"
        }
        stories_no_flow = [s.id for s in stories if s.id not in stories_with_primary]

        # Approved flows without use cases
        flows_with_uc = {uc.flow_id for uc in use_cases}
        flows_no_uc = [f.id for f in flows if f.status == "approved" and f.id not in flows_with_uc]

        # Approved use cases without requirements
        ucs_with_req = {r.primary_use_case_id for r in requirements if r.primary_use_case_id}
        ucs_no_req = [uc.id for uc in use_cases if uc.status == "approved" and uc.id not in ucs_with_req]

        return {
            "product_id": product_id,
            "features_without_approved_stories": features_no_stories,
            "stories_without_actors": stories_no_actors,
            "stories_without_primary_flow": stories_no_flow,
            "approved_flows_without_use_cases": flows_no_uc,
            "approved_use_cases_without_requirements": ucs_no_req,
            "total_features": len(features),
            "total_stories": len(stories),
            "total_flows": len(flows),
            "total_use_cases": len(use_cases),
            "total_requirements": len(requirements),
        }
