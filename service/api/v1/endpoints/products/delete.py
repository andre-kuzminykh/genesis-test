"""
Product DELETE endpoints.

## Traceability
Feature: F001 — Product Management
Scenarios: SC003 (delete)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.endpoints.products import router
from service.product.product_service import ProductService
from core.database import db_connect

_service = ProductService()


@router.delete("/{id}", status_code=204)
async def delete_product(
    id: str,
    session: AsyncSession = Depends(db_connect.get_session),
):
    """Delete a draft product."""
    await _service.delete(session, id)
