"""
Command handlers for the bot.
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

import text

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username
    logger.info("User %s (%s) started the bot", user_id, username)
    
    await message.answer(text.help_msg, parse_mode="Markdown")


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    user_id = message.from_user.id
    logger.info("User %s requested help", user_id)
    
    await message.answer(text.help_msg, parse_mode="Markdown")