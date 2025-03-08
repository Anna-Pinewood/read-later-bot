"""
Reply keyboards for the bot.

Contains keyboard layouts for the main UI and navigation.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import src.text as text


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Create the main reply keyboard with primary commands.

    Returns:
        ReplyKeyboardMarkup: Keyboard with /random, /last, and /all buttons
    """
    builder = ReplyKeyboardBuilder()

    # Add command buttons
    builder.add(
        KeyboardButton(text="/random"),
        KeyboardButton(text="/last"),
        KeyboardButton(text="/all")
    )

    # Arrange buttons in a row
    builder.adjust(3)

    return builder.as_markup(resize_keyboard=True, persistent=True)
