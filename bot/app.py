"""Entry point for the Telegram bot.

## Traceability
Product: Telegram Product Engineer Bot
"""
import asyncio

from core.loader import dp, bot


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
