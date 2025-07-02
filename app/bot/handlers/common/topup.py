from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.db.session import SessionLocal
from app.db.models.user import User
from app.db.models.payment import Payment
from app.bot.utils.payment_checker import create_cryptomus_payment
from app.bot.keyboards.user_kb import get_main_menu, confirm_payment_keyboard
from app.core.logger import logger
from app.main import check_user_not_banned, is_admin

router = Router()

class TopupState(StatesGroup):
    amount = State()
    waiting_for_payment = State()

@router.message(lambda message: message.text == "💳 Top Up")
async def start_topup(message: Message, state: FSMContext):
    if not await check_user_not_banned(message.from_user.id):
        await message.answer("You are banned from using this bot.")
        return
    await message.answer("Enter the amount to top up ($):", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Cancel")]], resize_keyboard=True
    ))
    await state.set_state(TopupState.amount)
    logger.info(f"User {message.from_user.id} started topup")

@router.message(TopupState.amount)
async def process_amount(message: Message, state: FSMContext):
    if message.text == "Cancel":
        await message.answer("Cancelled.", reply_markup=get_main_menu(await is_admin(message.from_user.id)))
        await state.clear()
        return
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer("Amount must be positive.")
            return
        payment_url, payment_uuid = await create_cryptomus_payment(amount, str(message.from_user.id))
        if payment_url:
            with SessionLocal() as db:
                payment = Payment(
                    user_id=message.from_user.id,
                    amount=amount,
                    transaction_id=payment_uuid,
                    cryptomus_uuid=payment_uuid
                )
                db.add(payment)
                db.commit()
            await message.answer(
                f"Please pay ${amount:.2f} in LTC using this link:\n{payment_url}\n\nPress 'Confirm Payment' after payment.",
                reply_markup=confirm_payment_keyboard()
            )
            await state.update_data(payment_uuid=payment_uuid, amount=amount)
            await state.set_state(TopupState.waiting_for_payment)
            logger.info(f"User {message.from_user.id} initiated topup of ${amount}")
        else:
            await message.answer("Failed to create payment. Please try again.")
            await state.clear()
    except ValueError:
        await message.answer("Please enter a valid number.")

@router.callback_query(F.data == "confirm_payment")
async def check_topup_payment(callback: CallbackQuery, state: FSMContext):
    if not await check_user_not_banned(callback.from_user.id):
        await callback.message.answer("You are banned from using this bot.")
        return
    data = await state.get_data()
    with SessionLocal() as db:
        payment = db.query(Payment).filter(Payment.cryptomus_uuid == data["payment_uuid"]).first()
        if payment and payment.status == "paid":
            user = db.query(User).filter(User.id == payment.user_id).first()
            user.balance += data["amount"]
            db.commit()
            await callback.message.answer(
                f"Balance topped up successfully! New balance: ${user.balance:.2f}",
                reply_markup=get_main_menu(await is_admin(callback.from_user.id))
            )
            logger.info(f"User {callback.from_user.id} topped up balance by ${data['amount']}")
            await state.clear()
        else:
            await callback.message.answer("Payment not confirmed yet. Please wait or contact support.")
        await callback.message.delete()