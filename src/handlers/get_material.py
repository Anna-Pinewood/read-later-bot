"""
Handlers for retrieving materials (/random and /last commands).

These handlers allow users to retrieve content items from their collection
based on different criteria (last added or random unread).
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
import re

from db.database import db
import text
from keyboards.inline import get_status_update_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("last"))
async def get_last_material(message: Message) -> None:
    """
    Handle the /last command.
    
    Retrieves and sends the most recently added material, regardless of type or tags.
    
    Args:
        message: The incoming message with the /last command
    """
    user_id = message.from_user.id
    logger.info("User %s requested last material", user_id)
    
    # Get the last content item from the database
    content_item = await db.get_last_content_item(user_id)
    
    if not content_item:
        # No materials found
        await message.answer(text.no_materials_msg)
        return
    
    # Send the material information with status update buttons
    await send_material_info(message, content_item)


@router.message(Command("random"))
async def get_random_material(message: Message) -> None:
    """
    Handle the /random command.
    
    Retrieves and sends a random unread material, regardless of type or tags.
    
    Args:
        message: The incoming message with the /random command
    """
    user_id = message.from_user.id
    logger.info("User %s requested random material", user_id)
    
    # Get a random unread content item from the database
    content_item = await db.get_random_content_item(user_id)
    
    if not content_item:
        # No unread materials found
        await message.answer(text.no_unread_materials_msg)
        return
    
    # Send the material information with status update buttons
    await send_material_info(message, content_item)


async def send_material_info(message: Message, content_item: dict) -> None:
    """
    Format and send material information to the user.
    
    Args:
        message: The original command message
        content_item: Content item data from the database
    """
    # Extract content information
    content_id = content_item["id"]
    content = content_item["content"]
    content_type = content_item["content_type"] or "Не указан"
    date_added = content_item["date_added"].strftime("%d.%m.%Y %H:%M")
    status = "Прочитано" if content_item["status"] == "processed" else "Не прочитано"
    
    # Check if this is a forwarded message and create a link if possible
    message_link = None
    message_id = content_item.get("message_id")
    chat_id = content_item.get("chat_id")
    
    if message_id and chat_id:
        # For private chats/channels, Telegram API adds -100 prefix to chat_id
        # We need to strip it for the link
        if str(chat_id).startswith('-100'):
            chat_id_for_link = str(chat_id)[4:]  # Remove '-100' prefix
            message_link = f"https://t.me/c/{chat_id_for_link}/{message_id}"
        else:
            # For public chats, we'd need the username which we don't have stored
            # This is a fallback that might work in some cases
            message_link = f"https://t.me/{chat_id}/{message_id}"
    
    # If the content is a URL, use it directly
    if content and (content.startswith('http://') or content.startswith('https://')):
        display_content = content  # The URL will be displayed as is and clickable
    else:
        # For text content or forwarded messages with a message link
        display_content = content
        if message_link:
            display_content += f"\n\n[➡️ Перейти к оригиналу]({message_link})"
    
    # Format the message
    response = text.material_info_template.format(
        content=display_content,
        content_type=content_type,
        date_added=date_added,
        status=status
    )
    
    # Send the message with status update buttons
    await message.answer(
        response,
        reply_markup=get_status_update_keyboard(content_id),
        disable_web_page_preview=False,  # Enable link previews
        parse_mode="Markdown"  # Enable markdown for the message link
    )


@router.callback_query(F.data.startswith("status:"))
async def update_material_status(callback: CallbackQuery) -> None:
    """
    Handle status update button callbacks.
    
    Args:
        callback: Callback query from status update buttons
    """
    # Parse callback data to get content_id and new status
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Invalid callback data")
        return
    
    _, content_id_str, new_status = parts
    content_id = int(content_id_str)
    user_id = callback.from_user.id
    
    logger.info("User %s changing status of content %s to %s", user_id, content_id, new_status)
    
    # Update the status in the database
    success = await db.update_content_status(content_id, new_status)
    
    if success:
        # Update the message to reflect the new status
        status_text = "Прочитано" if new_status == "processed" else "Не прочитано"
        await callback.answer(f"Статус изменен на: {status_text}")
        
        # Update the message text to reflect the change
        message_text = callback.message.text
        old_status = "Прочитано" if new_status == "unread" else "Не прочитано"
        new_status_text = "Прочитано" if new_status == "processed" else "Не прочитано"
        
        updated_text = message_text.replace(f"Статус: {old_status}", f"Статус: {new_status_text}")
        
        # Send updated message
        await callback.message.edit_text(
            updated_text,
            reply_markup=get_status_update_keyboard(content_id),
            disable_web_page_preview=False
        )
    else:
        await callback.answer("Произошла ошибка при обновлении статуса")