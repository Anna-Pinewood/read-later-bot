"""
Handlers for adding new materials.
"""

import logging
import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from filter import NotCommandFilter
from states import ContentItemStates
from keyboards.inline import get_content_type_keyboard, get_tags_keyboard
from db.database import db
import text

router = Router()
logger = logging.getLogger(__name__)

# Simple URL detection regex
URL_PATTERN = re.compile(r'https?://\S+')


@router.message(NotCommandFilter())
async def process_any_message(message: Message, state: FSMContext) -> None:
    """
    Handle any message as potential material for the collection.

    This handler will process messages as new content, even if the user was in the
    middle of adding another content item but sent a message instead of pressing buttons.

    Args:
        message: Any message from the user
        state: FSM context for managing conversation state
    """
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"

    # Extract content information
    content = message.text or message.caption or ""
    source = f"@{username}"

    # Log additional info for different message types
    if message.forward_from or message.forward_sender_name or message.forward_from_chat:
        logger.info("User %s forwarded a message to the collection", user_id)
        if message.forward_from_chat:
            source = f"@{message.forward_from_chat.username or 'channel'}"
    else:
        logger.info("User %s sent a message to the collection", user_id)

    # Log URLs if found
    if message.text and URL_PATTERN.search(message.text):
        url = URL_PATTERN.search(message.text).group(0)
        logger.info("Found URL in message: %s", url)

    # Save material in database immediately
    try:
        # Extract message and chat ID for forwarded content
        message_id = None
        chat_id = None
        if message.forward_from_chat:
            message_id = message.forward_from_message_id
            chat_id = message.forward_from_chat.id

        # Add content to database
        content_id = await db.add_content_item(
            user_id=user_id,
            content=content,
            source=source,
            message_id=message_id,
            chat_id=chat_id
        )

        # Store content_id in FSM state
        await state.update_data(content_id=content_id)

        # Send confirmation and ask for content type
        await message.answer(text.material_received_msg)
        await message.answer(
            text.ask_content_type_msg,
            reply_markup=get_content_type_keyboard()
        )

        # Set state to waiting for content type
        await state.set_state(ContentItemStates.waiting_for_content_type)

    except Exception as e:
        logger.error("Failed to save content for user %s: %s", user_id, e)
        # Notify user of error but don't reveal technical details
        await message.answer("Произошла ошибка при сохранении. Пожалуйста, попробуйте позже.")


@router.callback_query(F.data.startswith("content_type:"))
async def process_content_type(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Process content type selection.

    Note: We removed the state filter so it works even if the state was cleared
    by a new message being sent.

    Args:
        callback: Callback query from inline keyboard
        state: FSM context to track conversation state
    """
    # Get user ID
    user_id = callback.from_user.id

    # Parse content type from callback data
    _, content_type = callback.data.split(":", 1)

    # First, check if we have content_id in state
    state_data = await state.get_data()
    content_id = state_data.get("content_id")

    if not content_id:
        logger.warning("No content_id found in state for user %s. Callback may be outdated.", user_id)
        await callback.answer("Это сообщение устарело. Пожалуйста, используйте кнопки из последнего сообщения.")
        return

    try:
        if content_type != "skip":
            # Update content type in database
            await db.update_content_type(content_id, content_type)
            logger.info("Updated content type to '%s' for item %s", content_type, content_id)

            # Confirm content type selection
            content_type_name = text.text_type_msg if content_type == "text" else text.video_type_msg
            await callback.message.edit_text(
                text.content_type_selected_msg.format(content_type=content_type_name)
            )
        else:
            logger.info("User %s skipped content type selection", user_id)
            await callback.message.edit_text(text.content_skipped_msg)

        # Get user tags for the tag selection keyboard
        user_tags = await db.get_user_tags(user_id)

        # Ask for tags
        await callback.message.answer(
            text.ask_tags_msg,
            reply_markup=get_tags_keyboard(user_tags)
        )

        # Update state to waiting for tag
        await state.set_state(ContentItemStates.waiting_for_tag)

    except Exception as e:
        logger.error("Error processing content type for user %s: %s", user_id, e)
        await callback.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

    # Always answer the callback to remove loading indicator
    await callback.answer()


@router.callback_query(F.data.startswith("tag:"))
async def process_tag_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Process tag selection or 'add new tag' / 'skip' options.

    Note: We removed the state filter so it works even if the state was cleared
    by a new message being sent.

    Args:
        callback: Callback query from inline keyboard
        state: FSM context to track conversation state
    """
    user_id = callback.from_user.id

    # First, check if we have content_id in state
    state_data = await state.get_data()
    content_id = state_data.get("content_id")

    if not content_id:
        logger.warning("No content_id found in state for user %s. Callback may be outdated.", user_id)
        await callback.answer("Это сообщение устарело. Пожалуйста, используйте кнопки из последнего сообщения.")
        return

    # Parse tag action from callback data
    _, tag_data = callback.data.split(":", 1)

    try:
        if tag_data == "new":
            # User wants to add a new tag
            await callback.message.edit_text(text.new_tag_prompt_msg)
            # Keep the same state, but set a flag to indicate we're waiting for a new tag name
            await state.update_data(waiting_for_new_tag=True)
            await state.set_state(ContentItemStates.waiting_for_tag)  # Ensure we're in the correct state
            await callback.answer()
            return

        if tag_data == "skip":
            # User wants to skip tag selection
            logger.info("User %s skipped tag selection", user_id)
            await callback.message.edit_text(text.tag_skipped_msg)
            await callback.message.answer(text.material_saved_msg)
            # Clear state as we're done with this material
            await state.clear()
            await callback.answer()
            return

        # User selected an existing tag
        tag_id = int(tag_data)

        # Add tag to content
        await db.add_tag_to_content(content_id, tag_id)

        # Get tag name for confirmation
        user_tags = await db.get_user_tags(user_id)
        tag_name = next((tag['name'] for tag in user_tags if tag['id'] == tag_id), "Выбранный тег")

        logger.info("Added tag '%s' to content %s for user %s", tag_name, content_id, user_id)

        # Confirm tag addition
        await callback.answer(f"Тег '{tag_name}' добавлен")

        # Set state to ensure we're in the right state
        await state.set_state(ContentItemStates.waiting_for_tag)

        # Update keyboard to show the latest tags
        await callback.message.edit_text(
            text.tag_selected_msg.format(tag_name=tag_name) + "\n" + text.ask_tags_msg,
            reply_markup=get_tags_keyboard(user_tags)
        )

    except Exception as e:
        logger.error("Error processing tag selection for user %s: %s", user_id, e)
        await callback.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


@router.message(ContentItemStates.waiting_for_tag)
async def process_new_tag(message: Message, state: FSMContext) -> None:
    """
    Process a message containing a new tag name.

    Args:
        message: Message with the new tag name
        state: FSMcontext to track conversation state
    """
    user_id = message.from_user.id
    state_data = await state.get_data()

    # Check if we're actually waiting for a new tag name
    if not state_data.get("waiting_for_new_tag", False):
        # If we're in waiting_for_tag state but not specifically waiting for a new tag name,
        # it might be a new material the user sent without completing the previous flow
        # This should be caught by the NotCommandFilter now, but keeping as a fallback
        logger.warning("User %s sent message while in tag selection but not waiting for new tag", user_id)
        await message.answer("Для добавления нового материала, пожалуйста, завершите текущий процесс или нажмите 'Пропустить'")
        return

    content_id = state_data.get("content_id")
    if not content_id:
        logger.error("No content_id found in state for user %s", user_id)
        await message.answer("Ошибка. Пожалуйста, отправьте материал заново.")
        await state.clear()
        return

    # Get tag name from message
    tag_name = message.text.strip()

    if not tag_name:
        await message.answer("Название тега не может быть пустым. Пожалуйста, введите название тега.")
        return

    try:
        # Add tag to database
        tag_id = await db.add_tag(user_id, tag_name)

        # Add tag to content
        await db.add_tag_to_content(content_id, tag_id)

        logger.info("Created and added new tag '%s' to content %s for user %s", tag_name, content_id, user_id)

        # Confirm tag addition
        await message.answer(text.tag_selected_msg.format(tag_name=tag_name))

        # Reset the waiting_for_new_tag flag
        await state.update_data(waiting_for_new_tag=False)

        # Get user tags for the updated keyboard
        user_tags = await db.get_user_tags(user_id)

        # Ask if user wants to add more tags
        await message.answer(
            text.ask_tags_msg,
            reply_markup=get_tags_keyboard(user_tags)
        )

    except Exception as e:
        logger.error("Error adding new tag for user %s: %s", user_id, e)
        await message.answer("Произошла ошибка при добавлении тега. Пожалуйста, попробуйте позже.")


@router.callback_query(F.data.startswith("page:"))
async def process_tag_pagination(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle pagination for the tag selection keyboard.

    Args:
        callback: Callback query from inline keyboard
        state: FSM context to track conversation state
    """
    user_id = callback.from_user.id

    # Check if this is just the current page indicator (not a navigation button)
    if callback.data == "page:current":
        await callback.answer()
        return

    # Get the page number from the callback data
    _, page_str = callback.data.split(":", 1)

    try:
        page = int(page_str)

        # Get user tags for the updated keyboard
        user_tags = await db.get_user_tags(user_id)

        # Update the message with the new page of tags
        await callback.message.edit_reply_markup(
            reply_markup=get_tags_keyboard(user_tags, page=page)
        )

        # Make sure we're still in the right state
        current_state = await state.get_state()
        if current_state != ContentItemStates.waiting_for_tag:
            await state.set_state(ContentItemStates.waiting_for_tag)

        logger.info("User %s navigated to tag page %s", user_id, page)

    except Exception as e:
        logger.error("Error processing tag pagination for user %s: %s", user_id, e)
        await callback.answer("Произошла ошибка при навигации. Пожалуйста, попробуйте позже.")

    await callback.answer()
