"""
Product GET endpoints.

## Traceability
Feature: F001 — Product Management
Scenarios: SC001 (list), SC002 (get by id)
"""
from typing import List
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.products import router
from schema.product.product_schema import ProductResponseSchema
from service.product.product_service import ProductService
from core.database import db_connect

_service = ProductService()


@router.get("", response_model=List[ProductResponseSchema])
async def list_products(session: AsyncSession = Depends(db_connect.get_session)):
    """List all products."""
    return await _service.get_all(session)


@router.get("/{id}", response_model=ProductResponseSchema)
async def get_product(id: str, session: AsyncSession = Depends(db_connect.get_session)):
    """Get a product by id."""
    return await _service.get_by_id(session, id)
