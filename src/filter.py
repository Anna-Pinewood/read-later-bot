from aiogram.filters import BaseFilter
from aiogram.types import Message

class NotCommandFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        # Check if message text exists and does not start with '/'
        return not (message.text and message.text.startswith('/'))
