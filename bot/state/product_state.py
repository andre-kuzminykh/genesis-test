"""FSM states for the product decomposition wizard.

## Traceability
Feature: F001 — Product Management
"""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ProductFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    reviewing_summary = State()
    reviewing_features = State()
    reviewing_roles = State()
    reviewing_stories = State()
    reviewing_flows = State()
    reviewing_use_cases = State()
