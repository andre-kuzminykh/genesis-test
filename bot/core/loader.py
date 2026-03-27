"""Bot and Dispatcher factory.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from core.config import config


def create_bot() -> Bot:
    try:
        from aiogram.client.default import DefaultBotProperties
        return Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    except ImportError:
        return Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)


def create_dispatcher() -> Dispatcher:
    return Dispatcher()
