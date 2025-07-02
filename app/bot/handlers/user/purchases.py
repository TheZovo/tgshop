from aiogram import Router
from aiogram.types import Message
from app.db.session import SessionLocal
from app.db.models.purchase import Purchase
from app.db.models.product import Product
from app.bot.keyboards.user_kb import get_main_menu
from app.core.logger import logger
from app.main import check_user_not_banned, is_admin

router = Router()

@router.message(lambda message: message.text == "📦 My Purchases")
async def show_purchases(message: Message):
    if not await check_user_not_banned(message.from_user.id):
        await message.answer("You are banned from using this bot.")
        return
    with SessionLocal() as db:
        purchases = db.query(Purchase).join(Product).filter(Purchase.user_id == message.from_user.id).all()
        if not purchases:
            await message.answer("You have no purchases.", reply_markup=get_main_menu(await is_admin(message.from_user.id)))
            return
        text = "<b>Purchase History</b>\n\n"
        for purchase in purchases:
            text += (
                f"ID: {purchase.id}\n"
                f"Product: {purchase.product.name}\n"
                f"Price: ${purchase.product.price:.2f}\n"
                f"Date: {purchase.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Status: {purchase.status}\n\n"
            )
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu(await is_admin(message.from_user.id)))
    logger.info(f"User {message.from_user.id} viewed purchase history")