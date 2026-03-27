"""
FlowService — flow management with Mermaid validation and primary uniqueness.

## Traceability
Feature: F005 — User Flow Management
Scenarios: SC011, SC012

## Dependencies
- FlowRepository
"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from repository.flow.flow_repository import FlowRepository
from core.exceptions import NotFoundError, ValidationError, ConflictError


class FlowService:
    def __init__(self):
        self._repo = FlowRepository()

    async def create(self, session: AsyncSession, **kwargs):
        # Section 14: All User Flows must contain Mermaid source
        mermaid = kwargs.get("mermaid_source")
        if not mermaid or not mermaid.strip():
            raise ValidationError("User Flow must contain Mermaid source.")

        # Section 14.4: one primary flow per story
        if kwargs.get("flow_type") == "primary":
            has_primary = await self._repo.has_primary_flow(session, kwargs["story_id"])
            if has_primary:
                raise ConflictError("A Story must have at most one primary Flow.")

        return await self._repo.create(session, **kwargs)

    async def get_by_id(self, session: AsyncSession, flow_id: str):
        flow = await self._repo.get_by_id(session, flow_id)
        if not flow:
            raise NotFoundError("Flow", flow_id)
        return flow

    async def get_all(self, session: AsyncSession, story_id: str | None = None):
        if story_id:
            return await self._repo.get_all(session, story_id=story_id)
        return await self._repo.get_all(session)

    async def update(self, session: AsyncSession, flow_id: str, **kwargs):
        flow = await self.get_by_id(session, flow_id)
        if "mermaid_source" in kwargs:
            mermaid = kwargs["mermaid_source"]
            if not mermaid or not mermaid.strip():
                raise ValidationError("User Flow must contain Mermaid source.")
        content_changed = any(
            getattr(flow, k, None) != v
            for k, v in kwargs.items()
            if v is not None and hasattr(flow, k)
        )
        if content_changed:
            kwargs["version"] = flow.version + 1
            kwargs["updated_at"] = datetime.utcnow()
            if flow.approved_version is not None:
                kwargs["status"] = "changed"
                kwargs["approved_at"] = None
                kwargs["approved_by"] = None
                kwargs["approved_version"] = None
        return await self._repo.update(session, flow_id, **kwargs)

    async def approve(self, session: AsyncSession, flow_id: str, approver: str = "system"):
        flow = await self.get_by_id(session, flow_id)
        flow.status = "approved"
        flow.approved_at = datetime.utcnow()
        flow.approved_by = approver
        flow.approved_version = flow.version
        await session.flush()
        await session.refresh(flow)
        return flow
