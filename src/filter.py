"""
Custom filters for the bot.
"""
from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states import ContentItemStates


class NotCommandFilter(BaseFilter):
    """
    Filter for messages that are not commands and should be treated as new content.

    This handles two cases:
    1. No active state - message is treated as new content
    2. Active state but not explicitly waiting for text input - treat as new content
       and reset the current conversation flow
    """

    async def __call__(self, message: Message, state: FSMContext) -> bool:
        """
        Check if message should be treated as new content.

        Args:
            message: Message to check
            state: Current FSM state

        Returns:
            bool: True if the message should be treated as new content
        """
        # First check if it's a command - if so, don't process as content
        if message.text and message.text.startswith('/'):
            return False

        # Get current state and state data
        current_state = await state.get_state()
        state_data = await state.get_data()

        # Special case: If we're explicitly waiting for new tag input,
        # don't treat as new content
        if current_state == ContentItemStates.waiting_for_tag and state_data.get("waiting_for_new_tag", False):
            return False

        # For all other states, even if we're in a flow (waiting for button press),
        # treat text messages as new content and interrupt the current flow
        if current_state:
            # Clear the current state so we can start fresh with the new content
            await state.clear()

        # Message should be treated as new content
        return True
