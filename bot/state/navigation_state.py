"""FSM states for general navigation.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class NavigationState(StatesGroup):
    main_menu = State()
    entity_list = State()
    entity_detail = State()
