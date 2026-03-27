"""
UseCaseService — use case management.

## Traceability
Feature: F006 — Use Case Management
Scenarios: SC013

## Dependencies
- UseCaseRepository
- FlowRepository (for approval gate)
"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from repository.use_case.use_case_repository import UseCaseRepository
from repository.flow.flow_repository import FlowRepository
from core.exceptions import NotFoundError, ValidationError


class UseCaseService:
    def __init__(self):
        self._repo = UseCaseRepository()
        self._flow_repo = FlowRepository()

    async def create(self, session: AsyncSession, **kwargs):
        # Section 14.4: Flow must be approved before Use Case generation
        flow = await self._flow_repo.get_by_id(session, kwargs.get("flow_id", ""))
        if not flow:
            raise NotFoundError("Flow", kwargs.get("flow_id", ""))
        if flow.status != "approved":
            raise ValidationError("Flow must be approved before Use Case generation.")
        return await self._repo.create(session, **kwargs)

    async def get_by_id(self, session: AsyncSession, uc_id: str):
        uc = await self._repo.get_by_id(session, uc_id)
        if not uc:
            raise NotFoundError("UseCase", uc_id)
        return uc

    async def get_all(self, session: AsyncSession, flow_id: str | None = None):
        if flow_id:
            return await self._repo.get_all(session, flow_id=flow_id)
        return await self._repo.get_all(session)

    async def approve(self, session: AsyncSession, uc_id: str, approver: str = "system"):
        uc = await self.get_by_id(session, uc_id)
        uc.status = "approved"
        uc.approved_at = datetime.utcnow()
        uc.approved_by = approver
        uc.approved_version = uc.version
        await session.flush()
        await session.refresh(uc)
        return uc
