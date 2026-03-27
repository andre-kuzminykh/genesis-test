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
    editing_summary = State()
    reviewing_features = State()
    editing_feature = State()
    reviewing_stories = State()
    editing_story = State()
    reviewing_flows = State()
    editing_text = State()
