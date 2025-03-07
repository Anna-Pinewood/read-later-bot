"""
Command handlers for the bot.

Handles the basic commands like /start and /help.
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

import text
from keyboards.reply import get_main_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    """
    Handle the /start command.
    
    Sends a welcome message with help information and displays the main keyboard.
    
    Args:
        message: The incoming message with the /start command
    """
    user_id = message.from_user.id
    username = message.from_user.username
    logger.info("User %s (%s) started the bot", user_id, username)
    
    # Send welcome message with main keyboard
    await message.answer(
        text.help_msg, 
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    """
    Handle the /help command.
    
    Sends help information about bot usage.
    
    Args:
        message: The incoming message with the /help command
    """
    user_id = message.from_user.id
    logger.info("User %s requested help", user_id)
    
    await message.answer(
        text.help_msg, 
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )