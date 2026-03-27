"""Core package — configuration, loader, and vocabulary.

## Traceability
Product: Telegram Product Engineer Bot
"""
from core.config import config
from core.loader import bot, dp

__all__ = ["config", "bot", "dp"]
