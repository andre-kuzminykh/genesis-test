"""Entry point for the Telegram bot.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

import asyncio

from core.loader import create_bot, create_dispatcher
from handler.include_router import include_routers


async def main():
    bot = create_bot()
    dp = create_dispatcher()
    include_routers(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
