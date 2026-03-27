"""FSM states for product management flows.

## Traceability
Feature: F001 — Product Management
Scenarios: SC001, SC002, SC003
"""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ProductFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    editing_name = State()
    editing_description = State()
    confirming = State()
