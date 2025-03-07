"""
Entry point for the telegram bot.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import commands, add_material
from consts import BOT_TOKEN
from db.database import db  # Import the database instance


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s – [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


async def main():
    """Initialize and start the bot."""
    logger.info("Starting the bot")

    # Initialize database connection
    logger.info("Connecting to database")
    await db.connect()
    logger.info("Database connection established")

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Include routers
    dp.include_router(commands.router)
    dp.include_router(add_material.router)

    # Start polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started.")

    try:
        await dp.start_polling(bot)
    finally:
        # Close database connection when bot stops
        logger.info("Closing database connection")
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
