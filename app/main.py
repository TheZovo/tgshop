from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from core.config import settings
from bot.handlers import common, user, admin
from bot.middlewares.throttling import ThrottlingMiddleware
from core.logger import logger
from db.session import SessionLocal
from db.models.user import User

async def is_admin(user_id: int) -> bool:
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        return user.is_admin if user else False

async def check_user_not_banned(user_id: int) -> bool:
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        return user and not user.is_banned

async def main():
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    
    dp.include_router(common.router)
    dp.include_router(user.router)
    dp.include_router(admin.router)
    
    logger.info("Starting bot")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())