from aiogram import Router
from aiogram.types import Message
from app.db.session import SessionLocal
from app.db.models.user import User
from app.db.models.purchase import Purchase
from app.db.models.payment import Payment
from app.bot.keyboards.user_kb import get_main_menu
from app.core.logger import logger
from app.main import check_user_not_banned

router = Router()

@router.message(lambda message: message.text == "👤 Profile")
async def show_profile(message: Message):
    if not await check_user_not_banned(message.from_user.id):
        await message.answer("You are banned from using this bot.")
        return
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == str(message.from_user.id)).first()
        if not user:
            await message.answer("Profile not found.")
            return
        purchases = db.query(Purchase).filter(Purchase.user_id == user.id).count()
        payments = db.query(Payment).filter(Payment.user_id == user.id, Payment.status == "paid").count()
        
        profile_text = (
            f"👤 <b>Profile</b>\n\n"
            f"Username: @{user.username or 'N/A'}\n"
            f"Balance: ${user.balance:.2f}\n"
            f"Total Purchases: {purchases}\n"
            f"Successful Payments: {payments}\n"
            f"Status: {'Admin' if user.is_admin else 'User'}\n"
            f"Banned: {'Yes' if user.is_banned else 'No'}"
        )
        await message.answer(profile_text, parse_mode="HTML", reply_markup=get_main_menu(user.is_admin))
    logger.info(f"User {message.from_user.id} viewed profile")