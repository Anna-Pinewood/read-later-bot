"""
Handlers for filtering materials by tags.

This module provides handlers for the /bytags command
which allows users to browse their content filtered by specific tags.
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.states import GetTagStates
from src.keyboards.inline import get_tags_keyboard
from src.db.database import db
from src.handlers.get_material import show_material_page
import src.text as text

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("bytags"))
async def get_by_tags_command(message: Message, state: FSMContext) -> None:
    """
    Handle the /bytags command.
    
    Shows a keyboard with the user's tags to select for filtering.
    
    Args:
        message: The incoming message with the command
        state: FSM context for managing conversation state
    """
    user_id = message.from_user.id
    logger.info("User %s requested materials by tag filter", user_id)
    
    # Clear any previous state
    await state.clear()
    
    # Get user's tags
    user_tags = await db.get_user_tags(user_id)
    
    if not user_tags:
        # No tags found
        await message.answer(text.no_tags_msg)
        return
    
    # Show tag selection keyboard
    await message.answer(
        text.select_tag_msg,
        reply_markup=get_tags_keyboard(user_tags)
    )
    
    # Set state to waiting for tag selection
    await state.set_state(GetTagStates.waiting_for_tag_selection)


@router.callback_query(GetTagStates.waiting_for_tag_selection, F.data.startswith("tag:"))
async def process_tag_filter_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Process tag selection for filtering materials.
    Only triggered when in the GetTagStates.waiting_for_tag_selection state.
    
    Args:
        callback: Callback query from tag selection keyboard
        state: FSM context for managing conversation state
    """
    user_id = callback.from_user.id
    
    # Parse tag action from callback data
    _, tag_data = callback.data.split(":", 1)
    
    # Handle 'new' or 'skip' as special cases
    if tag_data == "new":
        await callback.answer("В этом режиме нельзя создавать новые теги. Пожалуйста, выберите существующий тег.")
        return
    
    if tag_data == "skip":
        # Cancel tag filtering
        await callback.message.edit_text(text.filter_cancelled_msg)
        await state.clear()
        await callback.answer()
        return
    
    try:
        # User selected a tag
        tag_id = int(tag_data)
        
        # Get tag name for confirmation
        user_tags = await db.get_user_tags(user_id)
        tag_name = next((tag['name'] for tag in user_tags if tag['id'] == tag_id), "Выбранный тег")
        
        logger.info("User %s filtering content by tag ID %s ('%s')", user_id, tag_id, tag_name)
        
        # Store selected tag in state for any future interactions
        await state.update_data(selected_tag_id=tag_id, selected_tag_name=tag_name)
        
        # Confirm tag selection
        await callback.answer(f"Показываю материалы с тегом '{tag_name}'")
        
        # Edit original message to show we're filtering
        await callback.message.edit_text(text.filtering_by_tag_msg.format(tag_name=tag_name))
        
        # Get content items with this tag
        content_items = await db.get_content_by_tags(user_id, [tag_id])
        
        if not content_items:
            await callback.message.answer(text.no_materials_with_tag_msg.format(tag_name=tag_name))
            await state.clear()
            return
        
        # Get the first page of filtered content
        # We'll reuse the same function used by the /all command
        # but with our tag filter applied
        await show_material_page(
            callback.message,
            user_id,
            page=0,
            status=None,  # Show all items regardless of status
            tag_filter=tag_id
        )
        
    except Exception as e:
        logger.error("Error processing tag selection for user %s: %s", user_id, e)
        await callback.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    # Clear the state since we've shown the filtered results
    await state.clear()


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

@router.callback_query(GetTagStates.waiting_for_tag_selection, F.data.startswith("page:"))
async def process_tag_selection_pagination(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle pagination for the tag selection keyboard during tag filtering.
    Only triggers when in the FilterStates.waiting_for_tag_selection state.
    
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
        
        logger.info("User %s navigated to tag page %s during tag filtering", user_id, page)
        
    except Exception as e:
        logger.error("Error processing tag pagination for user %s: %s", user_id, e)
        await callback.answer("Произошла ошибка при навигации. Пожалуйста, попробуйте позже.")
    
    await callback.answer()