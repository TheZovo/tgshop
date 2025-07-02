from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from db.session import SessionLocal
from db.models.product import Product
from bot.keyboards.admin_kb import get_admin_menu
from core.logger import logger
from bot.utils.auth import is_admin
from bot.utils.banned import check_user_not_banned

router = Router()

class AddProduct(StatesGroup):
    name = State()
    price = State()
    description = State()
    stock = State()

@router.message(lambda message: message.text == "📋 Products")
async def list_products(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        return
    with SessionLocal() as db:
        products = db.query(Product).all()
        if not products:
            await message.answer("No products available.", reply_markup=get_admin_menu())
            return
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{p.name} - ${p.price} (Stock: {p.stock})", callback_data=f"delete_product_{p.id}")]
            for p in products
        ])
        await message.answer("Products:", reply_markup=keyboard)
    logger.info(f"Admin {message.from_user.id} viewed product list")

@router.message(lambda message: message.text == "➕ Add Product")
async def start_add_product(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        return
    await message.answer("Enter product name:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Cancel")]], resize_keyboard=True
    ))
    await state.set_state(AddProduct.name)
    logger.info(f"Admin {message.from_user.id} started adding product")

@router.message(AddProduct.name)
async def process_name(message: Message, state: FSMContext):
    if message.text == "Cancel":
        await message.answer("Cancelled.", reply_markup=get_admin_menu())
        await state.clear()
        return
    await state.update_data(name=message.text)
    await message.answer("Enter product price:")
    await state.set_state(AddProduct.price)

@router.message(AddProduct.price)
async def process_price(message: Message, state: FSMContext):
    if message.text == "Cancel":
        await message.answer("Cancelled.", reply_markup=get_admin_menu())
        await state.clear()
        return
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer("Enter product description:")
        await state.set_state(AddProduct.description)
    except ValueError:
        await message.answer("Please enter a valid number for price")

@router.message(AddProduct.description)
async def process_description(message: Message, state: FSMContext):
    if message.text == "Cancel":
        await message.answer("Cancelled.", reply_markup=get_admin_menu())
        await state.clear()
        return
    await state.update_data(description=message.text)
    await message.answer("Enter stock quantity:")
    await state.set_state(AddProduct.stock)

@router.message(AddProduct.stock)
async def process_stock(message: Message, state: FSMContext):
    if message.text == "Cancel":
        await message.answer("Cancelled.", reply_markup=get_admin_menu())
        await state.clear()
        return
    try:
        stock = int(message.text)
        data = await state.get_data()
        with SessionLocal() as db:
            product = Product(
                name=data["name"],
                price=data["price"],
                description=data["description"],
                stock=stock
            )
            db.add(product)
            db.commit()
            await message.answer("Product added successfully!", reply_markup=get_admin_menu())
        logger.info(f"Admin {message.from_user.id} added product: {data['name']}")
        await state.clear()
    except ValueError:
        await message.answer("Please enter a valid number for stock")

@router.callback_query(F.data.startswith("delete_product_"))
async def delete_product(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("Access denied")
        return
    product_id = int(callback.data.split("_")[2])
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            db.delete(product)
            db.commit()
            await callback.message.answer(f"Product {product.name} deleted.", reply_markup=get_admin_menu())
            logger.info(f"Admin {callback.from_user.id} deleted product: {product.name}")
        else:
            await callback.message.answer("Product not found.")
        await callback.message.delete()