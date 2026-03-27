"""Register all feature routers with the root dispatcher.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

from aiogram import Dispatcher

from handler.v1.user.wizard.main_widget import router as wizard_router


def include_routers(dp: Dispatcher) -> None:
    """Attach every feature router to the dispatcher."""
    dp.include_routers(
        wizard_router,
    )
