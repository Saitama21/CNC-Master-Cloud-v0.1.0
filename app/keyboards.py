from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Добавить станок"),
                KeyboardButton(text="🖥 Мои станки"),
            ],
            [
                KeyboardButton(text="📚 G/M-коды"),
                KeyboardButton(text="🧱 Материалы"),
            ],
            [
                KeyboardButton(text="⚙️ Стойки ЧПУ"),
                KeyboardButton(text="ℹ️ О проекте"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел CNC Master Cloud",
    )


def machine_types() -> InlineKeyboardMarkup:
    rows = [
        ("Токарный", "turning"),
        ("Фрезерный", "milling"),
        ("Токарно-фрезерный", "multitasking"),
        ("5-осевой центр", "5-axis"),
        ("Другое", "other"),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=title, callback_data=f"type:{value}")]
            for title, value in rows
        ]
    )


def manufacturers(items: list[dict]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=item["name"],
                callback_data=f"mfr:{item['id']}",
            )]
            for item in items
        ]
    )


def controllers(items: list[dict]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=item["name"],
                callback_data=f"ctl:{item['id']}",
            )]
            for item in items
        ]
    )
