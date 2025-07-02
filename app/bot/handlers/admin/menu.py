from aiogram import Router
from aiogram.types import Message
from bot.keyboards.admin_kb import get_admin_menu
from core.logger import logger
from bot.utils.auth import is_admin

router = Router()

@router.message(lambda message: message.text == "🔧 Admin Panel")
async def admin_menu(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        return
    await message.answer("Admin Panel:", reply_markup=get_admin_menu())
    logger.info(f"Admin {message.from_user.id} accessed admin panel")