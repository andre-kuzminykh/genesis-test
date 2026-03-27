"""
FeatureService — feature management with deletion rules.

## Traceability
Feature: F002 — Feature Management
Scenarios: SC004, SC005, SC006

## Dependencies
- FeatureRepository
- StoryRepository (for deletion check)
- ProductRepository (for existence check)
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from repository.feature.feature_repository import FeatureRepository
from repository.story.story_repository import StoryRepository
from repository.product.product_repository import ProductRepository
from core.exceptions import NotFoundError, ValidationError, ConflictError


class FeatureService:
    def __init__(self):
        self._repo = FeatureRepository()
        self._story_repo = StoryRepository()
        self._product_repo = ProductRepository()

    async def create(self, session: AsyncSession, **kwargs):
        product = await self._product_repo.get_by_id(session, kwargs.get("product_id", ""))
        if not product:
            raise NotFoundError("Product", kwargs.get("product_id", ""))
        return await self._repo.create(session, **kwargs)

    async def get_by_id(self, session: AsyncSession, feature_id: str):
        feature = await self._repo.get_by_id(session, feature_id)
        if not feature:
            raise NotFoundError("Feature", feature_id)
        return feature

    async def get_all(self, session: AsyncSession, product_id: str | None = None):
        if product_id:
            return await self._repo.get_all(session, product_id=product_id)
        return await self._repo.get_all(session)

    async def update(self, session: AsyncSession, feature_id: str, **kwargs):
        feature = await self.get_by_id(session, feature_id)
        content_changed = any(
            getattr(feature, k, None) != v
            for k, v in kwargs.items()
            if v is not None and hasattr(feature, k)
        )
        if content_changed:
            kwargs["version"] = feature.version + 1
            kwargs["updated_at"] = datetime.utcnow()
            if feature.approved_version is not None:
                kwargs["status"] = "changed"
                kwargs["approved_at"] = None
                kwargs["approved_by"] = None
                kwargs["approved_version"] = None
        return await self._repo.update(session, feature_id, **kwargs)

    async def approve(self, session: AsyncSession, feature_id: str, approver: str = "system"):
        feature = await self.get_by_id(session, feature_id)
        feature.status = "approved"
        feature.approved_at = datetime.utcnow()
        feature.approved_by = approver
        feature.approved_version = feature.version
        await session.flush()
        await session.refresh(feature)
        return feature

    async def delete(self, session: AsyncSession, feature_id: str):
        """Section 11 — physical deletion only for unreferenced drafts."""
        feature = await self.get_by_id(session, feature_id)
        if feature.status != "draft":
            raise ConflictError("Cannot delete feature that is not in draft status.")
        stories = await self._story_repo.get_all(session, feature_id=feature_id)
        if stories:
            raise ConflictError("Cannot delete feature that has downstream references.")
        return await self._repo.delete(session, feature_id)
