"""
Reply keyboards for the bot.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Create main keyboard for the bot.

    Returns:
        ReplyKeyboardMarkup: Keyboard with main commands
    """
    builder = ReplyKeyboardBuilder()

    # Add buttons
    builder.add(
        KeyboardButton(text="🔄 Случайный материал"),
        KeyboardButton(text="⏱ Последний материал")
    )

    # Set the keyboard as persistent
    return builder.as_markup(resize_keyboard=True, is_persistent=True)
