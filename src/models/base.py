"""Base entity metadata per specification section 6."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from src.enums.statuses import BaseStatus


class BaseEntity(BaseModel):
    """Every persistent entity must support at minimum these fields (section 6)."""
    version: int = Field(default=1, ge=1)
    status: BaseStatus = Field(default=BaseStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_by: str


class ApprovableEntity(BaseEntity):
    """Entity that supports approval workflow (section 6)."""
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_version: Optional[int] = None
    change_reason: Optional[str] = None
    deprecation_reason: Optional[str] = None
    archive_reason: Optional[str] = None
