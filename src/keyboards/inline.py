"""
Inline keyboards for the bot.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import text


def get_content_type_keyboard() -> InlineKeyboardMarkup:
    """
    Create keyboard with content type selection buttons.
    
    Returns:
        InlineKeyboardMarkup: Keyboard with text/video/skip buttons
    """
    builder = InlineKeyboardBuilder()
    
    # Add content type buttons
    builder.add(
        InlineKeyboardButton(text=text.text_type_msg, callback_data="content_type:text"),
        InlineKeyboardButton(text=text.video_type_msg, callback_data="content_type:video"),
        InlineKeyboardButton(text=text.skip_type_msg, callback_data="content_type:skip")
    )
    
    # Arrange buttons in a row
    builder.adjust(3)
    
    return builder.as_markup()


def get_tags_keyboard(tags: list[dict] = None) -> InlineKeyboardMarkup:
    """
    Create keyboard with tag selection buttons.
    
    Args:
        tags: List of tag dictionaries with 'id' and 'name' keys
        
    Returns:
        InlineKeyboardMarkup: Keyboard with tag buttons and add/skip options
    """
    builder = InlineKeyboardBuilder()
    
    # Add existing tags if provided
    if tags:
        for tag in tags:
            builder.add(InlineKeyboardButton(
                text=tag['name'], 
                callback_data=f"tag:{tag['id']}"
            ))
    
    # Add 'add new tag' and 'skip' buttons
    builder.add(
        InlineKeyboardButton(
            text=text.add_new_tag_msg, 
            callback_data="tag:new"
        ),
        InlineKeyboardButton(
            text=text.skip_tags_msg, 
            callback_data="tag:skip"
        )
    )
    
    # Arrange buttons: tags in rows of 2, control buttons in a separate row of 2
    if tags:
        # Располагаем существующие теги по 2 в ряд
        tag_rows = (len(tags) + 1) // 2  # Округляем вверх
        builder.adjust(*([2] * tag_rows + [2]))  # [2, 2, ..., 2] - последняя двойка для кнопок управления
    else:
        # Если нет тегов, просто располагаем кнопки управления в один ряд
        builder.adjust(2)
    
    return builder.as_markup()