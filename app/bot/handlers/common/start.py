from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.db.session import SessionLocal
from app.db.models.user import User
from app.bot.utils.captcha import generate_captcha, verify_captcha
from app.bot.keyboards.user_kb import get_main_menu
from app.core.logger import logger

router = Router()

class CaptchaState(StatesGroup):
    waiting_for_captcha = State()

@router.message()
async def handle_start(message: Message, state: FSMContext):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == str(message.from_user.id)).first()
        if not user:
            user = User(
                telegram_id=str(message.from_user.id),
                username=message.from_user.username,
                is_admin=False
            )
            db.add(user)
            db.commit()
            captcha_text, captcha_answer = generate_captcha()
            await state.update_data(captcha_answer=captcha_answer)
            await state.set_state(CaptchaState.waiting_for_captcha)
            await message.answer(f"Please solve this captcha: {captcha_text}")
            logger.info(f"New user {message.from_user.id} started captcha")
        else:
            if user.is_banned:
                await message.answer("You are banned from using this bot.")
                return
            await message.answer(
                f"Welcome back, {message.from_user.username or 'User'}!",
                reply_markup=get_main_menu(user.is_admin)
            )
            logger.info(f"User {message.from_user.id} started bot, admin: {user.is_admin}")

@router.message(CaptchaState.waiting_for_captcha)
async def process_captcha(message: Message, state: FSMContext):
    data = await state.get_data()
    if verify_captcha(message.text, data["captcha_answer"]):
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == str(message.from_user.id)).first()
            if user:
                await message.answer(
                    "Captcha passed! Welcome to the shop!",
                    reply_markup=get_main_menu(user.is_admin)
                )
                logger.info(f"User {message.from_user.id} passed captcha")
        await state.clear()
    else:
        captcha_text, captcha_answer = generate_captcha()
        await state.update_data(captcha_answer=captcha_answer)
        await message.answer(f"Incorrect. Try again: {captcha_text}")
        logger.warning(f"User {message.from_user.id} failed captcha")