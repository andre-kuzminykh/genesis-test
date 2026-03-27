"""
Product PUT endpoints.

## Traceability
Feature: F001 — Product Management
Scenarios: SC002 (update)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.products import router
from schema.product.product_schema import ProductUpdateSchema, ProductResponseSchema
from service.product.product_service import ProductService
from core.database import db_connect

_service = ProductService()


@router.put("/{id}", response_model=ProductResponseSchema)
async def update_product(
    id: str,
    payload: ProductUpdateSchema,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Update a product."""
    return await _service.update(session, id, **payload.model_dump(exclude_unset=True))
