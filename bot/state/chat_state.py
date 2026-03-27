"""FSM states for GPT chat mode.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ChatFSM(StatesGroup):
    chatting = State()
