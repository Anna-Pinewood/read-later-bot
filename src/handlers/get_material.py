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
from src.keyboards.inline import get_status_update_keyboard

router = Router()
logger = logging.getLogger(__name__)

# Constants for pagination
ITEMS_PER_PAGE = 12


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
    logger.info("Message ID: %s, Chat ID: %s", message_id, chat_id)
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
            display_content = content[:500] + "..."
            display_content += f"\n\n<a href='{message_link}'>➡️ Перейти к оригиналу</a>"

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
        parse_mode="HTML"  # Use HTML parse mode
    )


def create_materials_keyboard(items, current_page, filter_type="status", status=None, tag_id=None):
    """
    Create an inline keyboard with numbered buttons for each item
    and navigation buttons.

    Args:
        items: List of content items
        current_page: Current page number
        filter_type: Type of filter being applied ('status' or 'tag')
        status: Optional status filter to preserve during navigation
        tag_id: Optional tag ID filter to preserve during navigation

    Returns:
        InlineKeyboardMarkup: Keyboard with item buttons and navigation
    """
    # Create numbered buttons for each item
    item_buttons = []
    for idx, item in enumerate(items, start=1):
        item_buttons.append(InlineKeyboardButton(
            text=str(idx),  # Simply use sequential numbers starting from 1
            callback_data=f"view:{item['id']}"
        ))

    # Navigation buttons with appropriate filter parameters
    nav_buttons = []

    # Previous page button (if not on first page)
    if current_page > 0:
        if filter_type == "tag" and tag_id is not None:
            callback_data = f"tag_list_page:{current_page-1}:{tag_id}"
        else:
            callback_data = f"list_page:{current_page-1}"
            if status:
                callback_data += f":{status}"

        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=callback_data
        ))

    # Page indicator
    nav_buttons.append(InlineKeyboardButton(
        text=f"📄 {current_page+1}",
        callback_data="current_page"
    ))

    # Next page button (if there might be more items)
    if len(items) == ITEMS_PER_PAGE:
        if filter_type == "tag" and tag_id is not None:
            callback_data = f"tag_list_page:{current_page+1}:{tag_id}"
        else:
            callback_data = f"list_page:{current_page+1}"
            if status:
                callback_data += f":{status}"

        nav_buttons.append(InlineKeyboardButton(
            text="Вперед ▶️",
            callback_data=callback_data
        ))

    # Build keyboard with proper layout
    keyboard = []

    # Add item buttons in rows of 6
    for i in range(0, len(item_buttons), 6):
        keyboard.append(item_buttons[i:i+6])

    # Add navigation row at the bottom
    keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


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


@router.callback_query(F.data.startswith("list_page:"))
async def process_page_navigation(callback: CallbackQuery) -> None:
    """
    Handle pagination navigation for the materials list.

    Args:
        callback: Callback query for page navigation
    """
    # Parse the callback data
    parts = callback.data.split(":")

    # Extract page number
    page = int(parts[1])

    # Extract status if provided
    status = parts[2] if len(parts) > 2 else None

    user_id = callback.from_user.id

    logger.info("User %s navigating to materials page %s with status filter: %s",
                user_id, page, status or "none")

    # Show the requested page with the same status filter
    await show_material_page(callback.message, user_id, page, status)

    # Answer callback to remove the loading indicator
    await callback.answer()


@router.callback_query(F.data.startswith("tag_list_page:"))
async def process_tag_page_navigation(callback: CallbackQuery) -> None:
    """
    Handle pagination navigation for tag-filtered materials list.

    Args:
        callback: Callback query for page navigation with tag filter
    """
    # Parse the callback data
    parts = callback.data.split(":")

    if len(parts) < 3:
        await callback.answer("Invalid callback data")
        return

    # Extract page number and tag ID
    page = int(parts[1])
    tag_id = int(parts[2])

    user_id = callback.from_user.id

    logger.info("User %s navigating to materials page %s with tag filter: %s",
                user_id, page, tag_id)

    # Show the requested page with tag filter
    await show_material_page(callback.message, user_id, page, tag_filter=tag_id)

    # Answer callback to remove the loading indicator
    await callback.answer()


@router.callback_query(F.data.startswith("view:"))
async def view_specific_material(callback: CallbackQuery) -> None:
    """
    Handle viewing a specific material from the list.

    Args:
        callback: Callback query with the content item ID
    """
    # Parse the content ID from callback data
    _, content_id_str = callback.data.split(":", 1)
    content_id = int(content_id_str)
    user_id = callback.from_user.id

    logger.info("User %s viewing specific content item %s", user_id, content_id)

    try:
        # Get the content item from database
        content_item = await db.get_content_item_by_id(content_id)

        if not content_item:
            await callback.answer("Материал не найден")
            return

        # Fix: Use the callback.message object directly (not chat property)
        await send_material_info(callback.message, content_item)

        # Answer the callback query
        await callback.answer()
    except Exception as e:
        logger.error("Error showing content item %s: %s", content_id, e)
        await callback.answer("Произошла ошибка при загрузке материала")


@router.callback_query(F.data == "current_page")
async def handle_current_page(callback: CallbackQuery) -> None:
    """Handle clicks on the current page indicator."""
    await callback.answer()


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

        try:
            # Если успешно обновили статус, получаем обновленный материал из БД
            updated_item = await db.get_content_item_by_id(content_id)
            if updated_item:
                # Отправляем новое сообщение с обновленной информацией вместо редактирования
                # Это помогает избежать проблем с форматированием
                await callback.message.delete()
                await send_material_info(callback.message.chat, updated_item)

                # If we're marking as read, add info message about availability
                if new_status == "processed":
                    notification = text.material_marked_as_read_msg
                    # Send separate notification about using /last and /random
                    await callback.message.answer(notification)
            else:
                logger.error("Could not find content item with id %s after status update", content_id)
                await callback.answer("Ошибка: Не удалось обновить отображение материала")
        except Exception as e:
            logger.error("Error updating message after status change: %s", e)
            await callback.answer("Отображение не обновлено, но статус изменен")
    else:
        await callback.answer("Произошла ошибка при обновлении статуса")
