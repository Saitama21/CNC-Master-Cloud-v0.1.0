from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.cnc_logic import OPERATION_LABELS


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔧 Мой станок"),
                KeyboardButton(text="➕ Добавить станок"),
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


def machine_selector(items: list[dict]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=item["name"],
                callback_data=f"machine:{item['id']}",
            )]
            for item in items
        ]
    )


def machine_dashboard(machine_id: int) -> InlineKeyboardMarkup:
    rows = [
        [("📋 Характеристики", "char"), ("🧭 Возможности X/Y/Z/C", "caps")],
        [("🔩 Подобрать инструмент", "tool"), ("🧮 Рассчитать режимы", "modes")],
        [("➕ Создать операцию", "operation"), ("🛡 Проверить G-код", "gcode")],
        [("❗ Ошибки стойки", "alarms"), ("📝 Техпроцесс", "process")],
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=title, callback_data=f"mact:{machine_id}:{action}")
                for title, action in row
            ]
            for row in rows
        ]
    )


def operation_choices(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"{prefix}:{code}")]
            for code, label in OPERATION_LABELS.items()
        ]
    )


def material_choices(items: list[dict], prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{item['code']} — {item['name']}",
                callback_data=f"{prefix}:{item['id']}",
            )]
            for item in items[:20]
        ]
    )


def calculation_choices() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Точение / сверление", callback_data="calc:turning")],
            [InlineKeyboardButton(text="Фрезерование", callback_data="calc:milling")],
        ]
    )
