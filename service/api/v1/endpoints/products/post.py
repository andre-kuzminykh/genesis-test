"""
Product POST endpoints.

## Traceability
Feature: F001 — Product Management
Scenarios: SC001 (create), SC003 (approve)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.products import router
from schema.product.product_schema import ProductCreateSchema, ProductResponseSchema
from service.product.product_service import ProductService
from core.database import db_connect

_service = ProductService()


@router.post("", response_model=ProductResponseSchema, status_code=201)
async def create_product(
    payload: ProductCreateSchema,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Create a new product."""
    return await _service.create(session, **payload.model_dump())


@router.post("/{id}/approve", response_model=ProductResponseSchema)
async def approve_product(
    id: str,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Approve a product at its current version."""
    return await _service.approve(session, id)
