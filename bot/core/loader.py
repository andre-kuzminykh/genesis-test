"""Bot and Dispatcher factory.

## Traceability
Product: Telegram Product Engineer Bot
"""
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from core.config import config

bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
