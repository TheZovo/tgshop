from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.models import promocode
from db.session import SessionLocal
from db.models.product import Product
from db.models.purchase import Purchase
from db.models.promocode import Promocode
from db.models.payment import Payment
from bot.keyboards.user_kb import get_products_keyboard, confirm_purchase_keyboard
from bot.utils.payment_checker import create_cryptomus_payment
from core.logger import logger
from bot.utils.banned import check_user_not_banned

router = Router()

class PurchaseState(StatesGroup):
    waiting_for_promocode = State()
    waiting_for_payment = State()

@router.message(lambda message: message.text == "🛒 Shop")
async def show_shop(message: Message):
    if not await check_user_not_banned(message.from_user.id):
        await message.answer("You are banned from using this bot.")
        return
    with SessionLocal() as db:
        products = db.query(Product).filter(Product.stock > 0).all()
        if not products:
            await message.answer("No products available.")
            return
        await message.answer("Available products:", reply_markup=get_products_keyboard(products))
    logger.info(f"User {message.from_user.id} viewed shop")

@router.callback_query(F.data.startswith("product_"))
async def process_product_selection(callback: CallbackQuery, state: FSMContext):
    if not await check_user_not_banned(callback.from_user.id):
        await callback.message.answer("You are banned from using this bot.")
        return
    product_id = int(callback.data.split("_")[1])
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            await state.update_data(product_id=product_id)
            await callback.message.answer(
                f"{product.name}\nPrice: ${product.price}\n{product.description}\n\nEnter promocode (or press 'Skip' to proceed):",
                reply_markup=confirm_purchase_keyboard(product_id, include_skip=True)
            )
            await state.set_state(PurchaseState.waiting_for_promocode)
        else:
            await callback.message.answer("Product not found.")
        await callback.message.delete()
    logger.info(f"User {callback.from_user.id} selected product {product_id}")

@router.callback_query(F.data == "skip_promocode")
async def skip_promocode(callback: CallbackQuery, state: FSMContext):
    await process_promocode(callback.message, state, None)
    await callback.message.delete()

@router.message(PurchaseState.waiting_for_promocode)
async def process_promocode(message: Message, state: FSMContext, promocode_code: str = None):
    if not await check_user_not_banned(message.from_user.id):
        await message.answer("You are banned from using this bot.")
        return
    data = await state.get_data()
    product_id = data["product_id"]
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        promocode = None
        if promocode_code:
            promocode = db.query(Promocode).filter(Promocode.code == promocode_code).first()
        elif message.text:
            promocode = db.query(Promocode).filter(Promocode.code == message.text).first()
            if not promocode:
                await message.answer("Invalid promocode. Proceeding without discount.")
        
        final_price = product.price * (1 - (promocode.discount if promocode else 0))
        payment_url, payment_uuid = await create_cryptomus_payment(final_price, str(message.from_user.id))
        
        if payment_url:
            payment = Payment(
                user_id=message.from_user.id,
                amount=final_price,
                transaction_id=payment_uuid,
                cryptomus_uuid=payment_uuid
            )
            db.add(payment)
            db.commit()
            
            await state.update_data(payment_uuid=payment_uuid, final_price=final_price)
            await state.set_state(PurchaseState.waiting_for_payment)
            await message.answer(
                f"Please pay ${final_price:.2f} in LTC using this link:\n{payment_url}\n\nPress 'Confirm Payment' after payment.",
                reply_markup=confirm_purchase_keyboard(product_id, include_confirm=True)
            )
            logger.info(f"User {message.from_user.id} initiated payment for product {product_id}")
        else:
            await message.answer("Failed to create payment. Please try again.")
            await state.clear()

@router.callback_query(F.data.startswith("confirm_payment_"))
async def check_payment(callback: CallbackQuery, state: FSMContext):
    if not await check_user_not_banned(callback.from_user.id):
        await callback.message.answer("You are banned from using this bot.")
        return
    data = await state.get_data()
    with SessionLocal() as db:
        payment = db.query(Payment).filter(Payment.cryptomus_uuid == data["payment_uuid"]).first()
        if payment and payment.status == "paid":
            product = db.query(Product).filter(Product.id == data["product_id"]).first()
            if product.stock > 0:
                purchase = Purchase(
                    user_id=callback.from_user.id,
                    product_id=product.id,
                    promocode_id=promocode.id if promocode else None
                )
                product.stock -= 1
                db.add(purchase)
                db.commit()
                await callback.message.answer("Purchase successful! Check 'My Purchases' for details.")
                logger.info(f"User {callback.from_user.id} completed purchase of product {product.id}")
            else:
                await callback.message.answer("Product is out of stock.")
            await state.clear()
        else:
            await callback.message.answer("Payment not confirmed yet. Please wait or contact support.")
        await callback.message.delete()