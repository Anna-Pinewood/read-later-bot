"""
State classes for the bot's FSM (Finite State Machine).
"""
from aiogram.fsm.state import State, StatesGroup


class ContentItemStates(StatesGroup):
    """States for adding a content item."""
    waiting_for_content_type = State()
    waiting_for_tag = State()


class GetTagStates(StatesGroup):
    """States for filtering content by tags."""
    waiting_for_tag_selection = State()
