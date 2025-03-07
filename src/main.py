"""
Entry point for the telegram bot.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import commands, add_material
from consts import BOT_TOKEN


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s – [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


async def main():
    """Initialize and start the bot."""
    logger.info("Starting the bot")

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Include routers
    dp.include_router(commands.router)
    dp.include_router(add_material.router)

    # Start polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
