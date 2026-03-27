"""Entry point for the Telegram bot.

## Traceability
Product: Telegram Product Engineer Bot
"""
import asyncio

from core.loader import dp, bot
from handler.include_router import include_routers


async def main():
    include_routers(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
