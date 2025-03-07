"""
Handlers for adding new materials.
"""

import logging
import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from filter import NotCommandFilter
import text

router = Router()
logger = logging.getLogger(__name__)

# Simple URL detection regex (used for logging purposes only)
URL_PATTERN = re.compile(r'https?://\S+')


@router.message(NotCommandFilter())  # Match any message that is not a command
async def process_any_message(message: Message) -> None:
    """
    Handle any message as potential material for the collection.
    
    Args:
        message: Any message from the user
    """
    user_id = message.from_user.id
    
    # Log extra info if message is forwarded
    if message.forward_from or message.forward_sender_name or message.forward_from_chat:
        logger.info("User %s forwarded a message to the collection", user_id)
    else:
        logger.info("User %s sent a message to the collection", user_id)
    
    # Log URLs if found (for information purposes)
    if message.text and URL_PATTERN.search(message.text):
        url = URL_PATTERN.search(message.text).group(0)
        logger.info("Found URL in message: %s", url)
    
    # In the future, here we'll:
    # 1. Ask user to specify content type if needed
    # 2. Save the message content and type to the database

    await message.answer(text.material_received_msg)