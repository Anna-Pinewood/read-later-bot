"""
Inline keyboards for the bot.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import src.text as text

ITEMS_PER_PAGE = 6


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
    )

    # Add skip button separately
    builder.add(
        InlineKeyboardButton(text=text.skip_type_msg, callback_data="content_type:skip")
    )

    # Arrange buttons: main options on first row, skip on second row
    builder.adjust(2, 1)

    return builder.as_markup()


def get_tags_keyboard(tags: list[dict] = None, page: int = 0) -> InlineKeyboardMarkup:
    """
    Create keyboard with tag selection buttons with pagination.

    Args:
        tags: List of tag dictionaries with 'id' and 'name' keys
        page: Current page number (starting from 0)

    Returns:
        InlineKeyboardMarkup: Keyboard with tag buttons, navigation, and control buttons
    """
    builder = InlineKeyboardBuilder()

    # Define limits for pagination
    TAGS_PER_ROW = 6
    MAX_ROWS = 5
    TAGS_PER_PAGE = TAGS_PER_ROW * MAX_ROWS

    # Check if there are tags
    if tags:
        # Calculate total pages
        total_pages = (len(tags) + TAGS_PER_PAGE - 1) // TAGS_PER_PAGE

        # Ensure page is within valid range
        page = max(0, min(page, total_pages - 1))

        # Determine which tags to show on current page
        start_idx = page * TAGS_PER_PAGE
        end_idx = min(start_idx + TAGS_PER_PAGE, len(tags))
        current_page_tags = tags[start_idx:end_idx]

        # Add tag buttons for current page
        for tag in current_page_tags:
            builder.add(InlineKeyboardButton(
                text=tag['name'],
                callback_data=f"tag:{tag['id']}"
            ))

        # Calculate rows for current page tags
        tags_rows_count = (len(current_page_tags) + TAGS_PER_ROW - 1) // TAGS_PER_ROW
        rows_adjustment = [min(len(current_page_tags) - i * TAGS_PER_ROW, TAGS_PER_ROW)
                           for i in range(tags_rows_count)]

        # Add navigation buttons if there's more than one page
        if total_pages > 1:
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton(
                    text="◀️ Previous", callback_data=f"page:{page-1}"
                ))

            # Add page indicator
            nav_buttons.append(InlineKeyboardButton(
                text=f"📄 {page+1}/{total_pages}", callback_data="page:current"
            ))

            if page < total_pages - 1:
                nav_buttons.append(InlineKeyboardButton(
                    text="Next ▶️", callback_data=f"page:{page+1}"
                ))

            for button in nav_buttons:
                builder.add(button)

            # Adjust navigation row width based on how many navigation buttons we have
            rows_adjustment.append(len(nav_buttons))
    else:
        # Empty rows list if no tags
        rows_adjustment = []

    # Add 'add new tag' button
    builder.add(
        InlineKeyboardButton(
            text=text.add_new_tag_msg,
            callback_data="tag:new"
        )
    )

    # Add 'skip' button separately
    builder.add(
        InlineKeyboardButton(
            text=text.skip_tags_msg,
            callback_data="tag:skip"
        )
    )

    # Always add rows for control buttons
    rows_adjustment.append(1)  # "Add new tag" on its own row
    rows_adjustment.append(1)  # "Skip" on its own row at the bottom

    builder.adjust(*rows_adjustment)

    return builder.as_markup()


def get_status_update_keyboard(content_id: int) -> InlineKeyboardMarkup:
    """
    Create keyboard with buttons to update content status.

    Args:
        content_id: ID of the content item

    Returns:
        InlineKeyboardMarkup: Keyboard with buttons to mark as read/unread
    """
    builder = InlineKeyboardBuilder()

    # Add status update buttons
    builder.add(
        InlineKeyboardButton(
            text=text.mark_as_read_msg,
            callback_data=f"status:{content_id}:processed"
        ),
        InlineKeyboardButton(
            text=text.mark_as_unread_msg,
            callback_data=f"status:{content_id}:unread"
        )
    )

    # Arrange buttons in a row
    builder.adjust(2)

    return builder.as_markup()


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
