from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.calculators import CALCULATORS
from app.catalog_data import CATEGORY_LABELS
from app.cnc_logic import OPERATION_LABELS


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔧 Мой станок"), KeyboardButton(text="➕ Добавить станок")],
            [KeyboardButton(text="📚 G/M-коды"), KeyboardButton(text="🧱 Материалы")],
            [KeyboardButton(text="🧮 Калькуляторы"), KeyboardButton(text="⚙️ Стойки ЧПУ")],
            [KeyboardButton(text="ℹ️ О проекте")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел CNC Master Cloud FULL PRO",
    )


def machine_types() -> InlineKeyboardMarkup:
    rows = [
        ("Токарный", "turning"), ("Фрезерный", "milling"),
        ("Токарно-фрезерный", "multitasking"), ("5-осевой центр", "5-axis"),
        ("Другое", "other"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"type:{code}")]
        for label, code in rows
    ])


def manufacturers(items: list[dict]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=item["name"], callback_data=f"mfr:{item['id']}")]
        for item in items
    ])


def controllers(items: list[dict]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=item["name"], callback_data=f"ctl:{item['id']}")]
        for item in items
    ])


def machine_selector(items: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        controller = item.get("controller") or {}
        rows.append([InlineKeyboardButton(
            text=f"🔧 {item['name']} · {controller.get('name', 'стойка')}",
            callback_data=f"machine:{item['id']}",
        )])
    rows.append([InlineKeyboardButton(text="➕ Добавить ещё станок", callback_data="machine:add")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def machine_dashboard(machine_id: int) -> InlineKeyboardMarkup:
    rows = [
        [("📋 Паспорт", "char"), ("🧭 Возможности", "caps")],
        [("🔩 Инструмент", "tool"), ("🧮 Режимы", "modes")],
        [("➕ Операции", "operation"), ("🛡 G-код", "gcode")],
        [("❗ Ошибки", "alarms"), ("📝 Техпроцесс", "process")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=title, callback_data=f"mact:{machine_id}:{action}")
         for title, action in row]
        for row in rows
    ])


def tool_hub(machine_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Подбор по параметрам", callback_data=f"thub:{machine_id}:select")],
        [InlineKeyboardButton(text="📦 Готовый каталог", callback_data=f"thub:{machine_id}:catalog")],
        [InlineKeyboardButton(text="🧩 Несколько операций", callback_data=f"thub:{machine_id}:multi")],
        [InlineKeyboardButton(text="⭐ Сохранённый инструмент", callback_data=f"thub:{machine_id}:saved")],
    ])


def operation_choices(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"{prefix}:{code}")]
        for code, label in OPERATION_LABELS.items()
    ])


def multi_operation_choices(selected: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for code, label in OPERATION_LABELS.items():
        mark = "✅" if code in selected else "▫️"
        rows.append([InlineKeyboardButton(text=f"{mark} {label}", callback_data=f"multiop:{code}")])
    rows.append([
        InlineKeyboardButton(text="🧹 Очистить", callback_data="multiop:clear"),
        InlineKeyboardButton(text="Готово ➡️", callback_data="multiop:done"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def material_choices(items: list[dict], prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{item['code']} — {item['name']}", callback_data=f"{prefix}:{item['id']}"
        )]
        for item in items[:30]
    ])


def tool_material_choices(items: list[dict]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=f"{item['code']} — {item['name']}", callback_data=f"toolmat:{item['id']}"
    )] for item in items[:20]]
    rows.extend([
        [InlineKeyboardButton(text="ISO P — стали", callback_data="tooliso:P")],
        [InlineKeyboardButton(text="ISO M — нержавейка", callback_data="tooliso:M")],
        [InlineKeyboardButton(text="ISO K — чугун", callback_data="tooliso:K")],
        [InlineKeyboardButton(text="ISO N — алюминий / цветные / пластик", callback_data="tooliso:N")],
        [InlineKeyboardButton(text="ISO S — титан / жаропрочные", callback_data="tooliso:S")],
        [InlineKeyboardButton(text="ISO H — закалённые", callback_data="tooliso:H")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def calculation_choices() -> InlineKeyboardMarkup:
    return calculator_choices()


def calculator_choices() -> InlineKeyboardMarkup:
    rows = []
    for index in range(0, len(CALCULATORS), 2):
        row = [InlineKeyboardButton(
            text=CALCULATORS[index].label, callback_data=f"calc:{CALCULATORS[index].key}"
        )]
        if index + 1 < len(CALCULATORS):
            row.append(InlineKeyboardButton(
                text=CALCULATORS[index + 1].label,
                callback_data=f"calc:{CALCULATORS[index + 1].key}",
            ))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def catalog_categories(machine_id: int) -> InlineKeyboardMarkup:
    rows = []
    pairs = list(CATEGORY_LABELS.items())
    for index in range(0, len(pairs), 2):
        row = [InlineKeyboardButton(
            text=pairs[index][1], callback_data=f"catc:{machine_id}:{pairs[index][0]}:0"
        )]
        if index + 1 < len(pairs):
            row.append(InlineKeyboardButton(
                text=pairs[index + 1][1], callback_data=f"catc:{machine_id}:{pairs[index + 1][0]}:0"
            ))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def catalog_items(machine_id: int, category: str, page: int, items: list[dict], page_size: int = 8) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=f"{item['code']} — {item['name']}"[:58],
        callback_data=f"cati:{machine_id}:{item['key']}:{category}:{page}",
    )] for item in items]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"catc:{machine_id}:{category}:{page-1}"))
    if len(items) == page_size:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"catc:{machine_id}:{category}:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="📂 Категории", callback_data=f"catroot:{machine_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def catalog_item_actions(machine_id: int, tool_key: str, category: str, page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Сохранить для станка", callback_data=f"cats:{machine_id}:{tool_key}")],
        [InlineKeyboardButton(text="⬅️ К списку", callback_data=f"catc:{machine_id}:{category}:{page}")],
    ])
