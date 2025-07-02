from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.db.session import SessionLocal
from app.db.models.promocode import Promocode
from app.bot.keyboards.admin_kb import get_admin_menu
from app.core.logger import logger
from datetime import datetime, timedelta
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from app.main import is_admin

router = Router()

class AddPromocode(StatesGroup):
    code = State()
    discount = State()
    expires_at = State()

@router.message(lambda message: message.text == "🎟 Promocodes")
async def list_promocodes(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        return
    with SessionLocal() as db:
        promocodes = db.query(Promocode).all()
        if not promocodes:
            await message.answer("No promocodes available.", reply_markup=get_admin_menu())
            return
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{p.code} - {p.discount*100}% (Expires: {p.expires_at.strftime('%Y-%m-%d') if p.expires_at else 'Never'})",
                callback_data=f"delete_promocode_{p.id}"
            )] for p in promocodes
        ])
        await message.answer("Promocodes:", reply_markup=keyboard)
    logger.info(f"Admin {message.from_user.id} viewed promocode list")

@router.message(lambda message: message.text == "➕ Add Promocode")
async def start_add_promocode(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        return
    await message.answer("Enter promocode:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Cancel")]], resize_keyboard=True
    ))
    await state.set_state(AddPromocode.code)
    logger.info(f"Admin {message.from_user.id} started adding promocode")

@router.message(AddPromocode.code)
async def process_code(message: Message, state: FSMContext):
    if message.text == "Cancel":
        await message.answer("Cancelled.", reply_markup=get_admin_menu())
        await state.clear()
        return
    await state.update_data(code=message.text)
    await message.answer("Enter discount percentage (0-100):")
    await state.set_state(AddPromocode.discount)

@router.message(AddPromocode.discount)
async def process_discount(message: Message, state: FSMContext):
    if message.text == "Cancel":
        await message.answer("Cancelled.", reply_markup=get_admin_menu())
        await state.clear()
        return
    try:
        discount = float(message.text) / 100
        if 0 <= discount <= 1:
            await state.update_data(discount=discount)
            await message.answer("Enter expiration days (or press 'Skip' for no expiration):",
                               reply_markup=ReplyKeyboardMarkup(
                                   keyboard=[[KeyboardButton(text="Skip"), KeyboardButton(text="Cancel")]],
                                   resize_keyboard=True
                               ))
            await state.set_state(AddPromocode.expires_at)
        else:
            await message.answer("Discount must be between 0 and 100.")
    except ValueError:
        await message.answer("Please enter a valid number.")

@router.message(AddPromocode.expires_at)
async def process_expires_at(message: Message, state: FSMContext):
    if message.text == "Cancel":
        await message.answer("Cancelled.", reply_markup=get_admin_menu())
        await state.clear()
        return
    data = await state.get_data()
    expires_at = None
    if message.text != "Skip":
        try:
            days = int(message.text)
            expires_at = datetime.utcnow() + timedelta(days=days)
        except ValueError:
            await message.answer("Please enter a valid number of days.")
            return
    with SessionLocal() as db:
        promocode = Promocode(
            code=data["code"],
            discount=data["discount"],
            expires_at=expires_at
        )
        db.add(promocode)
        db.commit()
        await message.answer("Promocode added successfully!", reply_markup=get_admin_menu())
    logger.info(f"Admin {message.from_user.id} added promocode: {data['code']}")
    await state.clear()