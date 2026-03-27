"""
ProductService — product management with approval workflow.

## Traceability
Feature: F001 — Product Management
Scenarios: SC001, SC002, SC003

## Dependencies
- ProductRepository
"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from repository.product.product_repository import ProductRepository
from core.exceptions import NotFoundError, ValidationError


class ProductService:
    def __init__(self):
        self._repo = ProductRepository()

    async def create(self, session: AsyncSession, **kwargs):
        return await self._repo.create(session, **kwargs)

    async def get_by_id(self, session: AsyncSession, product_id: str):
        product = await self._repo.get_by_id(session, product_id)
        if not product:
            raise NotFoundError("Product", product_id)
        return product

    async def get_all(self, session: AsyncSession):
        return await self._repo.get_all(session)

    async def update(self, session: AsyncSession, product_id: str, **kwargs):
        product = await self.get_by_id(session, product_id)
        content_changed = any(
            getattr(product, k, None) != v
            for k, v in kwargs.items()
            if v is not None and hasattr(product, k)
        )
        if content_changed:
            kwargs["version"] = product.version + 1
            kwargs["updated_at"] = datetime.utcnow()
            # Invalidate approval if previously approved (section 7.2)
            if product.approved_version is not None:
                kwargs["status"] = "changed"
                kwargs["approved_at"] = None
                kwargs["approved_by"] = None
                kwargs["approved_version"] = None
        return await self._repo.update(session, product_id, **kwargs)

    async def approve(self, session: AsyncSession, product_id: str, approver: str = "system"):
        """Section 7.2 — version-bound approval."""
        product = await self.get_by_id(session, product_id)
        product.status = "approved"
        product.approved_at = datetime.utcnow()
        product.approved_by = approver
        product.approved_version = product.version
        await session.flush()
        await session.refresh(product)
        return product

    async def delete(self, session: AsyncSession, product_id: str):
        product = await self.get_by_id(session, product_id)
        if product.status != "draft":
            raise ValidationError("Can only delete draft products.")
        return await self._repo.delete(session, product_id)
