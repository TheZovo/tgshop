from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from cachetools import TTLCache
import time

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self.cache = TTLCache(maxsize=10000, ttl=5)

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        current_time = time.time()
        
        if user_id in self.cache:
            last_time = self.cache[user_id]
            if current_time - last_time < 1:
                if isinstance(event, Message):
                    await event.answer("Please wait a moment before sending another request.")
                return
        self.cache[user_id] = current_time
        return await handler(event, data)