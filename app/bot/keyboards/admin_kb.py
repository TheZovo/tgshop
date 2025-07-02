from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Products"), KeyboardButton(text="🎟 Promocodes")],
            [KeyboardButton(text="👥 Users"), KeyboardButton(text="📜 Logs")],
            [KeyboardButton(text="📢 Mailing")]
        ],
        resize_keyboard=True
    )