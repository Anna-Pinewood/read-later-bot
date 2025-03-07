"""
Custom filters for the bot.
"""
from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states import ContentItemStates


class NotCommandFilter(BaseFilter):
    """
    Filter for messages that are not commands and not part of an active dialog flow.
    """
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        """
        Check if message is not a command and not part of an active dialog.
        
        This filter returns True only if:
        1. The message is not a command (doesn't start with '/')
        2. The bot is not in the middle of a structured conversation
           (e.g., waiting for tag input)
        
        Args:
            message: Message to check
            state: Current FSM state
            
        Returns:
            bool: True if the message should be treated as new content
        """
        # First check if it's a command - if so, don't process as content
        if message.text and message.text.startswith('/'):
            return False
            
        # Check the current state - if waiting for user input in a specific
        # state, don't process as new content
        current_state = await state.get_state()
        
        # If we're in any state of the content addition flow,
        # don't treat this message as new content
        if current_state in [ContentItemStates.waiting_for_content_type, 
                             ContentItemStates.waiting_for_tag]:
            return False
            
        # Otherwise, it's not a command and not part of a flow, so it's new content
        return True