from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.session import SessionLocal
from db.models.user import User
from bot.keyboards.admin_kb import get_admin_menu
from core.logger import logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from bot.utils.auth import is_admin

router = Router()

class Mailing(StatesGroup):
    message = State()

@router.message(lambda message: message.text == "👥 Users")
async def list_users(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        return
    with SessionLocal() as db:
        users = db.query(User).all()
        if not users:
            await message.answer("No users found.", reply_markup=get_admin_menu())
            return
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"@{u.username or u.telegram_id} - {'Banned' if u.is_banned else 'Active'}",
                callback_data=f"ban_user_{u.id}"
            )] for u in users
        ])
        await message.answer("Users:", reply_markup=keyboard)
    logger.info(f"Admin {message.from_user.id} viewed user list")

@router.callback_query(F.data.startswith("ban_user_"))
async def ban_user(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("Access denied")
        return
    user_id = int(callback.data.split("_")[2])
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_banned = not user.is_banned
            db.commit()
            status = "banned" if user.is_banned else "unbanned"
            await callback.message.answer(f"User {user.username or user.telegram_id} {status}.", 
                                       reply_markup=get_admin_menu())
            logger.info(f"Admin {callback.from_user.id} {status} user: {user.username or user.telegram_id}")
        else:
            await callback.message.answer("User not found.")
        await callback.message.delete()

@router.message(lambda message: message.text == "📢 Mailing")
async def start_mailing(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        return
    await message.answer("Enter the message to send to all users:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Cancel")]], resize_keyboard=True
    ))
    await state.set_state(Mailing.message)
    logger.info(f"Admin {message.from_user.id} started mailing")

@router.message(Mailing.message)
async def send_mailing(message: Message, state: FSMContext, bot):
    if message.text == "Cancel":
        await message.answer("Cancelled.", reply_markup=get_admin_menu())
        await state.clear()
        return
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        return
    with SessionLocal() as db:
        users = db.query(User).filter(User.is_banned == False).all()
        sent_count = 0
        for user in users:
            try:
                await bot.send_message(user.telegram_id, message.text)
                sent_count += 1
            except:
                logger.error(f"Failed to send message to user {user.telegram_id}")
        await message.answer(f"Message sent to {sent_count} users.", reply_markup=get_admin_menu())
    logger.info(f"Admin {message.from_user.id} sent mailing to {sent_count} users")
    await state.clear()