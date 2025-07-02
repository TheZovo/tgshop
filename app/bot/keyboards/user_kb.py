from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🛒 Shop"), KeyboardButton(text="👤 Profile")],
        [KeyboardButton(text="📦 My Purchases"), KeyboardButton(text="💳 Top Up")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="🔧 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_products_keyboard(products):
    keyboard = InlineKeyboardMarkup()
    for product in products:
        keyboard.add(InlineKeyboardButton(
            text=f"{product.name} - ${product.price}",
            callback_data=f"product_{product.id}"
        ))
    return keyboard

def confirm_purchase_keyboard(product_id, include_skip=False, include_confirm=False):
    buttons = []
    if include_skip:
        buttons.append([InlineKeyboardButton(text="Skip", callback_data="skip_promocode")])
    if include_confirm:
        buttons.append([InlineKeyboardButton(text="Confirm Payment", callback_data=f"confirm_payment_{product_id}")])
    buttons.append([InlineKeyboardButton(text="Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Confirm Payment", callback_data="confirm_payment")],
        [InlineKeyboardButton(text="Cancel", callback_data="cancel")]
    ])