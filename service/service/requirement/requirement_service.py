"""
RequirementService — requirement management.

## Traceability
Feature: F007 — Requirement Management
Scenarios: SC014

## Dependencies
- RequirementRepository
- UseCaseRepository (for approval gate)
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from repository.requirement.requirement_repository import RequirementRepository
from repository.use_case.use_case_repository import UseCaseRepository
from core.exceptions import NotFoundError, ValidationError


class RequirementService:
    def __init__(self):
        self._repo = RequirementRepository()
        self._uc_repo = UseCaseRepository()

    async def create(self, session: AsyncSession, **kwargs):
        # Section 16.5: requirement_type must be set
        if not kwargs.get("requirement_type"):
            raise ValidationError("Requirement must have an explicit type.")

        # Section 16.5: must have at least one upstream traceable source
        uc_id = kwargs.get("primary_use_case_id")
        source_id = kwargs.get("source_id")
        if not uc_id and not source_id:
            raise ValidationError("Requirement must have at least one upstream traceable source.")

        # Section 15.3: Use Case must be approved
        if uc_id:
            uc = await self._uc_repo.get_by_id(session, uc_id)
            if not uc:
                raise NotFoundError("UseCase", uc_id)
            if uc.status != "approved":
                raise ValidationError("Use Case must be approved before Requirement generation.")

        return await self._repo.create(session, **kwargs)

    async def get_by_id(self, session: AsyncSession, req_id: str):
        req = await self._repo.get_by_id(session, req_id)
        if not req:
            raise NotFoundError("Requirement", req_id)
        return req

    async def get_all(self, session: AsyncSession, feature_id: str | None = None):
        if feature_id:
            return await self._repo.get_all(session, feature_id=feature_id)
        return await self._repo.get_all(session)

    async def approve(self, session: AsyncSession, req_id: str, approver: str = "system"):
        req = await self.get_by_id(session, req_id)
        req.status = "approved"
        req.approved_at = datetime.utcnow()
        req.approved_by = approver
        req.approved_version = req.version
        await session.flush()
        await session.refresh(req)
        return req
