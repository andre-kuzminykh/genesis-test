"""
Base ORM model with shared metadata fields.

## Traceability
Feature: F001-F009 — All features (section 6: base entity metadata)
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class BaseModel:
    """Every persistent entity: id, version, status, timestamps, user tracking."""
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="draft")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(255), nullable=False, default="system")
    updated_by = Column(String(255), nullable=False, default="system")

    # Approval fields (section 6)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_version = Column(Integer, nullable=True)
