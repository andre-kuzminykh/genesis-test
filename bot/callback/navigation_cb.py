"""Callback data factories for inline-keyboard navigation.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class NavigationCallback(CallbackData, prefix="nav"):
    """General navigation callback: go to a section or page."""

    section: str
    page: int = 1


class EntityActionCallback(CallbackData, prefix="entity"):
    """Action on a specific entity (view, approve, delete)."""

    entity_type: str
    entity_id: str
    action: str = "view"
