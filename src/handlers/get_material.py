"""
Handlers for retrieving materials (/random and /last commands).

These handlers allow users to retrieve content items from their collection
based on different criteria (last added or random unread).
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import re

from src.db.database import db
import src.text as text
from src.keyboards.inline import create_materials_keyboard

router = Router()
logger = logging.getLogger(__name__)

# Constants for pagination
ITEMS_PER_PAGE = 12


@router.message(Command("last"))
async def get_last_material(message: Message) -> None:
    """
    Handle the /last command.

    Retrieves and sends the most recently added material with 'unread' status,
    regardless of type or tags.

    Args:
        message: The incoming message with the /last command
    """
    user_id = message.from_user.id
    logger.info("User %s requested last unread material", user_id)

    # Get the last unread content item from the database
    # We'll modify the method call to include status filtering
    content_item = await db.get_last_content_item(user_id, status="unread")

    if not content_item:
        # No unread materials found
        await message.answer(text.no_unread_materials_msg)
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


@router.message(Command("all"))
async def get_all_materials(message: Message) -> None:
    """
    Handle the /all command.

    Retrieves and sends all unread materials as a paginated list,
    sorted from newest to oldest.

    Args:
        message: The incoming message with the /all command
    """
    user_id = message.from_user.id
    logger.info("User %s requested all unread materials", user_id)

    # Get the first page of content, filtered for unread items only
    await show_material_page(message, user_id, page=0, status="unread")


async def show_material_page(message, user_id, page=0, status=None, tag_filter=None):
    """
    Show a specific page of materials.

    Args:
        message: The message object to reply to
        user_id: Telegram user ID
        page: Page number (starting from 0)
        status: Optional status filter ('unread' or 'processed')
        tag_filter: Optional tag ID filter
    """
    try:
        # If tag_filter is provided, get materials filtered by tag
        if tag_filter is not None:
            content_items = await db.get_content_by_tags(
                user_id=user_id,
                tags=[tag_filter],
                limit=ITEMS_PER_PAGE,
                offset=page * ITEMS_PER_PAGE
            )
            filter_type = "tag"
        else:
            # Get paginated content items with optional status filter
            content_items = await db.get_user_content(
                user_id=user_id,
                limit=ITEMS_PER_PAGE,
                offset=page * ITEMS_PER_PAGE,
                status=status
            )
            filter_type = "status"

        if not content_items:
            if page == 0:
                # No materials found at all
                if tag_filter is not None:
                    tag_info = await db.get_tag_by_id(tag_filter)
                    tag_name = tag_info['name'] if tag_info else "выбранному тегу"
                    await message.answer(f"У вас нет материалов с тегом '{tag_name}'.")
                elif status == "unread":
                    await message.answer(text.no_unread_materials_msg)
                else:
                    await message.answer(text.no_materials_msg)
            else:
                # No materials on this page but there are previous pages
                await message.answer("На этой странице нет материалов. Попробуйте предыдущую страницу.")
            return

        # Format header based on filter type
        if tag_filter is not None:
            tag_info = await db.get_tag_by_id(tag_filter)
            tag_name = tag_info['name'] if tag_info else "выбранный тег"
            header_text = f"📚 Материалы с тегом '{tag_name}'"
        else:
            header_text = "📚 Ваши непрочитанные материалы" if status == "unread" else "📚 Ваши сохраненные материалы"

        header = f"{header_text} (стр. {page+1}):\n\n"

        # Format the list of materials
        numbered_list = []
        item_index = page * ITEMS_PER_PAGE + 1

        for idx, item in enumerate(content_items, start=item_index):
            # Format content preview
            content = item["content"]
            tags = item.get('tags', [])

            # Properly escape markdown characters in tags
            escaped_tags = []
            for tag in tags:
                # Escape all special markdown characters: _*[]()~`>#+-=|{}.!
                escaped_tag = re.sub(r'([_*\[\]()~`>#\+\-=|{}.!])', r'\\\1', tag)
                escaped_tags.append(escaped_tag)

            tags_str = " + ".join(escaped_tags) if escaped_tags else "Без тегов"

            # Create a preview of the content (first 30 chars)
            if len(content) > 30:
                content_preview = f"{content[:30]}..."
            else:
                content_preview = content

            # Format list item with title (content type) and preview
            list_item = f"{idx}. **{tags_str}** {content_preview}"
            numbered_list.append(list_item)

        # Join the list items into a single message
        materials_text = "\n".join(numbered_list)

        # Create inline keyboard for navigation and item selection
        keyboard = create_materials_keyboard(content_items, page, filter_type, status, tag_filter)

        # Send the message with keyboard
        await message.answer(
            header + materials_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error("Error showing material page: %s", e)
        await message.answer("Произошла ошибка при отображении списка материалов.")
