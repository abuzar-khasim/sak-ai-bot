from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def category_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🎓 Student"),
                KeyboardButton(text="💼 Working Professional"),
            ],
            [
                KeyboardButton(text="🏢 Business Owner"),
                KeyboardButton(text="🧑‍💻 Freelancer"),
            ],
            [
                KeyboardButton(text="🔹 Other"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🚀 About SAK AI"),
                KeyboardButton(text="📩 Contact Us"),
            ],
            [
                KeyboardButton(text="🔎 Ask SAK AI"),
                KeyboardButton(text="📢 Updates"),
            ],
        ],
        resize_keyboard=True,
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Add Update"),
                KeyboardButton(text="📋 Manage Updates"),
            ],
            [
                KeyboardButton(text="🔙 Main Menu"),
            ],
        ],
        resize_keyboard=True,
    )    