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
        ReplyKeyboardMarkup: Keyboard with main command buttons
    """
    builder = ReplyKeyboardBuilder()

    # Add command buttons
    builder.add(
        KeyboardButton(text="/random"),
        KeyboardButton(text="/last"),
        KeyboardButton(text="/all"),
        KeyboardButton(text="/bytags")
    )

    # Arrange buttons in two rows with 2 buttons per row
    builder.adjust(2, 2)

    return builder.as_markup(resize_keyboard=True, persistent=True)
