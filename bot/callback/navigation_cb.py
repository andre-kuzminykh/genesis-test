"""Callback data factories for inline-keyboard navigation.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix="m"):
    """Top-level menu actions."""
    action: str  # products, create_product


class ProductCB(CallbackData, prefix="p"):
    """Product-level actions."""
    id: str
    action: str = "view"  # view, edit, next, delete, approve


class FeatureCB(CallbackData, prefix="f"):
    """Feature-level actions."""
    id: str
    action: str = "view"  # view, edit, approve, next, gen


class StoryCB(CallbackData, prefix="s"):
    """Story-level actions."""
    id: str
    action: str = "view"


class FlowCB(CallbackData, prefix="fl"):
    """Flow-level actions."""
    id: str
    action: str = "view"


class WizardCB(CallbackData, prefix="w"):
    """Wizard control buttons."""
    action: str  # next, edit, approve, back, approve_all
    ctx: str = ""  # context id (product_id, feature_id, etc.)
