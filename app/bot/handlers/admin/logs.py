from aiogram import Router
from aiogram.types import Message
from core.logger import get_logs
from bot.keyboards.admin_kb import get_admin_menu
from core.logger import logger
from bot.utils.auth import is_admin

router = Router()

@router.message(lambda message: message.text == "📜 Logs")
async def show_logs(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        return
    logs = get_logs()
    if not logs:
        await message.answer("No logs available.", reply_markup=get_admin_menu())
        return
    await message.answer(logs, parse_mode="HTML", reply_markup=get_admin_menu())
    logger.info(f"Admin {message.from_user.id} viewed logs")