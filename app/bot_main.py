from __future__ import annotations

import asyncio
import html
import logging
import re
from typing import Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, Message

from app.api_client import CNCAPI, CNCAPIError
from app.calculators import CALCULATORS, calculate, expected_count
from app.catalog_data import CATEGORY_LABELS
from app.cnc_logic import (
    MACHINE_TYPE_LABELS,
    OPERATION_LABELS,
    analyze_gcode,
    capability_lines,
    diagnose_alarm,
    known_specs,
)
from app.config import settings
from app.keyboards import (
    calculator_choices,
    catalog_categories,
    catalog_item_actions,
    catalog_items,
    controllers as controllers_keyboard,
    machine_dashboard,
    machine_selector,
    machine_types,
    main_menu,
    manufacturers as manufacturers_keyboard,
    material_choices,
    multi_operation_choices,
    operation_choices,
    tool_hub,
    tool_material_choices,
)
from app.tool_catalog import ISO_LABELS, format_tool_selection, select_tool, tool_parameter_prompt

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

router = Router()
api = CNCAPI(settings.api_base_url)


class MachineWizard(StatesGroup):
    choosing_type = State()
    choosing_manufacturer = State()
    choosing_controller = State()
    entering_name = State()
    entering_axes = State()


class CodeSearch(StatesGroup):
    waiting_query = State()


class ToolWizard(StatesGroup):
    choosing_operation = State()
    choosing_material = State()
    entering_parameters = State()


class MultiToolWizard(StatesGroup):
    choosing_operations = State()
    choosing_material = State()
    entering_parameters = State()


class CalculatorWizard(StatesGroup):
    choosing = State()
    entering_values = State()


class GCodeCheck(StatesGroup):
    waiting_code = State()


class AlarmCheck(StatesGroup):
    waiting_alarm = State()


def controller_parts(machine: dict) -> tuple[dict, dict]:
    controller = machine.get("controller") or {}
    manufacturer = controller.get("manufacturer") or {}
    return controller, manufacturer


async def get_machine_or_error(telegram_id: int, machine_id: int, target: Message) -> dict | None:
    try:
        return await api.machine(telegram_id, machine_id)
    except CNCAPIError as exc:
        await target.answer(f"⚠️ {html.escape(str(exc))}")
        return None


async def allowed(user_id: int, feature_key: str, target: Message) -> bool:
    try:
        decision = await api.consume(user_id, feature_key)
    except CNCAPIError as exc:
        await target.answer(f"⚠️ Не удалось проверить лимит: {html.escape(str(exc))}")
        return False
    if decision.get("allowed"):
        remaining = decision.get("remaining")
        if remaining is not None and remaining <= 2:
            await target.answer(f"ℹ️ Осталось использований в этом часу: {remaining}")
        return True
    reset = decision.get("reset_at")
    reset_text = f"\nСброс: <code>{html.escape(reset)}</code>" if reset else ""
    await target.answer(
        f"⛔ <b>{html.escape(decision.get('title') or feature_key)}</b>\n"
        f"{html.escape(decision.get('reason') or 'Доступ ограничен администратором.')}"
        f"{reset_text}"
    )
    return False


async def show_machine_dashboard(target: Message, machine: dict, *, edit: bool = False) -> None:
    controller, manufacturer = controller_parts(machine)
    text = (
        f"<b>🔧 {html.escape(machine['name'])}</b>\n\n"
        f"Тип: {html.escape(MACHINE_TYPE_LABELS.get(machine.get('machine_type'), machine.get('machine_type') or '—'))}\n"
        f"Стойка: {html.escape(manufacturer.get('name', ''))} {html.escape(controller.get('name', ''))}\n"
        f"Оси: <code>{html.escape(machine.get('axes') or 'не указаны')}</code>\n\n"
        "Выберите рабочий модуль:"
    )
    markup = machine_dashboard(machine["id"])
    if edit:
        await target.edit_text(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


def parse_numbers(text: str) -> list[float]:
    return [float(x.replace(",", ".")) for x in re.findall(r"[-+]?\d+(?:[.,]\d+)?", text)]


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        await api.upsert_user(message.from_user)
        categories = await api.tool_categories()
    except CNCAPIError:
        logger.exception("Unable to initialize user")
        await message.answer("⚠️ Сервер базы временно недоступен. Проверь запуск API и базы.")
        return
    await message.answer(
        "<b>⚙️ CNC Master Cloud FULL PRO v1.0.0</b>\n\n"
        f"Каталог: <b>{categories.get('count', 0)}+</b> стандартных позиций инструмента.\n"
        "Подбор нескольких операций, калькуляторы, сохранённые комплекты и управляемые лимиты.",
        reply_markup=main_menu(),
    )


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_menu())


@router.message(F.text == "➕ Добавить станок")
async def add_machine(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(MachineWizard.choosing_type)
    await message.answer("<b>1/4. Выберите тип оборудования:</b>", reply_markup=machine_types())


@router.callback_query(MachineWizard.choosing_type, F.data.startswith("type:"))
async def choose_type(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(machine_type=callback.data.split(":", 1)[1])
    try:
        items = await api.manufacturers()
    except CNCAPIError as exc:
        await callback.message.answer(f"⚠️ {html.escape(str(exc))}")
        await callback.answer()
        return
    await state.set_state(MachineWizard.choosing_manufacturer)
    await callback.message.edit_text(
        "<b>2/4. Выберите производителя стойки:</b>",
        reply_markup=manufacturers_keyboard(items),
    )
    await callback.answer()


@router.callback_query(MachineWizard.choosing_manufacturer, F.data.startswith("mfr:"))
async def choose_manufacturer(callback: CallbackQuery, state: FSMContext) -> None:
    manufacturer_id = int(callback.data.split(":", 1)[1])
    try:
        items = await api.controllers(manufacturer_id)
    except CNCAPIError as exc:
        await callback.message.answer(f"⚠️ {html.escape(str(exc))}")
        await callback.answer()
        return
    if not items:
        await callback.message.answer("Для производителя пока нет моделей.")
        await callback.answer()
        return
    await state.set_state(MachineWizard.choosing_controller)
    await callback.message.edit_text(
        "<b>3/4. Выберите модель стойки:</b>", reply_markup=controllers_keyboard(items)
    )
    await callback.answer()


@router.callback_query(MachineWizard.choosing_controller, F.data.startswith("ctl:"))
async def choose_controller(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(controller_id=int(callback.data.split(":", 1)[1]))
    await state.set_state(MachineWizard.entering_name)
    await callback.message.edit_text(
        "<b>4/4. Напишите название профиля станка.</b>\n\n"
        "Например: <code>Tengyue CK52PT-Y</code>"
    )
    await callback.answer()


@router.message(MachineWizard.entering_name, F.text)
async def enter_machine_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name or len(name) > 150:
        await message.answer("Название должно содержать 1–150 символов.")
        return
    await state.update_data(name=name)
    await state.set_state(MachineWizard.entering_axes)
    await message.answer(
        "Укажите оси: <code>X/Z</code>, <code>X/Z/C</code>, <code>X/Z/Y/C</code> и т. д.\n"
        "Чтобы пропустить, отправьте <code>-</code>."
    )


@router.message(MachineWizard.entering_axes, F.text)
async def enter_machine_axes(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    axes = None if message.text.strip() == "-" else message.text.strip()
    try:
        item = await api.create_machine({
            "telegram_id": message.from_user.id,
            "controller_id": data["controller_id"],
            "name": data["name"],
            "machine_type": data["machine_type"],
            "axes": axes,
            "driven_tools": data["machine_type"] == "multitasking",
        })
    except CNCAPIError as exc:
        await message.answer(f"⚠️ Не удалось сохранить: {html.escape(str(exc))}")
        return
    await state.clear()
    await message.answer("✅ <b>Станок сохранён</b>", reply_markup=main_menu())
    await show_machine_dashboard(message, item)


@router.message(F.text.in_({"🔧 Мой станок", "🖥 Мои станки"}))
async def my_machine(message: Message) -> None:
    try:
        items = await api.machines(message.from_user.id)
    except CNCAPIError as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}")
        return
    if not items:
        await message.answer("У вас пока нет станков. Нажмите «➕ Добавить станок».")
        return
    await message.answer(
        "<b>Выберите станок, с которым хотите работать:</b>",
        reply_markup=machine_selector(items),
    )


@router.callback_query(F.data == "machine:add")
async def add_machine_from_selector(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(MachineWizard.choosing_type)
    await callback.message.edit_text("<b>1/4. Выберите тип оборудования:</b>", reply_markup=machine_types())
    await callback.answer()


@router.callback_query(F.data.startswith("machine:"))
async def select_machine(callback: CallbackQuery) -> None:
    machine_id = int(callback.data.split(":", 1)[1])
    machine = await get_machine_or_error(callback.from_user.id, machine_id, callback.message)
    if machine:
        await show_machine_dashboard(callback.message, machine, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("mact:"))
async def machine_action(callback: CallbackQuery, state: FSMContext) -> None:
    _, machine_id_raw, action = callback.data.split(":", 2)
    machine_id = int(machine_id_raw)
    machine = await get_machine_or_error(callback.from_user.id, machine_id, callback.message)
    if machine is None:
        await callback.answer()
        return
    controller, manufacturer = controller_parts(machine)
    controller_name = f"{manufacturer.get('name', '')} {controller.get('name', '')}".strip()

    if action == "char":
        specs = known_specs(machine["name"])
        lines = [
            f"<b>📋 Характеристики: {html.escape(machine['name'])}</b>",
            f"Тип: {html.escape(MACHINE_TYPE_LABELS.get(machine.get('machine_type'), machine.get('machine_type') or '—'))}",
            f"Стойка: {html.escape(controller_name)}",
            f"Оси: <code>{html.escape(machine.get('axes') or '—')}</code>",
        ]
        if specs:
            lines.extend(["", f"Производитель: {html.escape(specs['manufacturer'])}",
                          f"Модель: {html.escape(specs['model'])}", f"Мощность: {html.escape(specs['power'])}",
                          f"Макс. пруток: {html.escape(specs['max_bar'])}", f"Масса: {html.escape(specs['weight'])}",
                          f"Питание: {html.escape(specs['power_supply'])}", f"Источник: {html.escape(specs['source'])}"])
        await callback.message.answer("\n".join(lines))
    elif action == "caps":
        lines = [f"<b>🧭 Возможности {html.escape(machine['name'])}</b>"]
        lines.extend(f"\n• {html.escape(item)}" for item in capability_lines(machine))
        await callback.message.answer("".join(lines))
    elif action == "tool":
        await state.clear()
        await callback.message.answer(
            f"<b>🔩 Инструмент: {html.escape(machine['name'])}</b>\nВыберите режим:",
            reply_markup=tool_hub(machine_id),
        )
    elif action == "modes":
        if await allowed(callback.from_user.id, "calculators", callback.message):
            await state.clear()
            await state.update_data(machine_id=machine_id)
            await state.set_state(CalculatorWizard.choosing)
            await callback.message.answer("Выберите калькулятор:", reply_markup=calculator_choices())
    elif action == "operation":
        await start_multi_operations(callback, state, machine_id)
    elif action == "gcode":
        if await allowed(callback.from_user.id, "gcode_check", callback.message):
            await state.clear()
            await state.update_data(machine_id=machine_id, controller_name=controller_name)
            await state.set_state(GCodeCheck.waiting_code)
            await callback.message.answer("Вставьте G-код одним сообщением. Для отмены: /cancel")
    elif action == "alarms":
        if await allowed(callback.from_user.id, "alarms", callback.message):
            await state.clear()
            await state.update_data(machine_id=machine_id, controller_name=controller_name)
            await state.set_state(AlarmCheck.waiting_alarm)
            await callback.message.answer("Отправьте полный номер и текст ошибки со стойки.")
    elif action == "process":
        if await allowed(callback.from_user.id, "process", callback.message):
            await show_process(callback.message, callback.from_user.id, machine_id, machine["name"])
    await callback.answer()


@router.callback_query(F.data.startswith("thub:"))
async def tool_hub_action(callback: CallbackQuery, state: FSMContext) -> None:
    _, machine_id_raw, action = callback.data.split(":", 2)
    machine_id = int(machine_id_raw)
    if action == "select":
        if not await allowed(callback.from_user.id, "tool_selector", callback.message):
            await callback.answer(); return
        await state.clear()
        await state.update_data(machine_id=machine_id)
        await state.set_state(ToolWizard.choosing_operation)
        await callback.message.answer("Выберите операцию:", reply_markup=operation_choices("toolop"))
    elif action == "catalog":
        if not await allowed(callback.from_user.id, "tool_catalog", callback.message):
            await callback.answer(); return
        await callback.message.answer("Выберите категорию готового инструмента:", reply_markup=catalog_categories(machine_id))
    elif action == "multi":
        await start_multi_operations(callback, state, machine_id)
    elif action == "saved":
        await show_saved_tools(callback.message, callback.from_user.id, machine_id)
    await callback.answer()


@router.callback_query(ToolWizard.choosing_operation, F.data.startswith("toolop:"))
async def tool_choose_operation(callback: CallbackQuery, state: FSMContext) -> None:
    operation = callback.data.split(":", 1)[1]
    await state.update_data(operation=operation)
    try:
        materials = await api.materials()
    except CNCAPIError as exc:
        await callback.message.answer(f"⚠️ {html.escape(str(exc))}"); await callback.answer(); return
    await state.set_state(ToolWizard.choosing_material)
    await callback.message.edit_text("Выберите материал или ISO-группу:", reply_markup=tool_material_choices(materials))
    await callback.answer()


@router.callback_query(ToolWizard.choosing_material, F.data.startswith("toolmat:"))
async def tool_choose_material(callback: CallbackQuery, state: FSMContext) -> None:
    material_id = int(callback.data.split(":", 1)[1])
    materials = await api.materials()
    material = next((item for item in materials if item["id"] == material_id), None)
    if material is None:
        await callback.message.answer("Материал не найден."); await callback.answer(); return
    data = await state.get_data()
    await state.update_data(material_name=material["name"], iso_group=(material.get("iso_group") or "P").upper())
    await state.set_state(ToolWizard.entering_parameters)
    await callback.message.edit_text(
        f"<b>Материал:</b> {html.escape(material['name'])} (ISO {html.escape(material.get('iso_group') or '—')})\n\n"
        + tool_parameter_prompt(data["operation"])
    )
    await callback.answer()


@router.callback_query(ToolWizard.choosing_material, F.data.startswith("tooliso:"))
async def tool_choose_iso_group(callback: CallbackQuery, state: FSMContext) -> None:
    group = callback.data.split(":", 1)[1].upper()
    data = await state.get_data()
    await state.update_data(material_name=ISO_LABELS.get(group, group), iso_group=group)
    await state.set_state(ToolWizard.entering_parameters)
    await callback.message.edit_text(
        f"<b>ISO {group}:</b> {html.escape(ISO_LABELS.get(group, 'материал'))}\n\n"
        + tool_parameter_prompt(data["operation"])
    )
    await callback.answer()


@router.message(ToolWizard.entering_parameters, F.text)
async def tool_enter_parameters(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    machine = await get_machine_or_error(message.from_user.id, data["machine_id"], message)
    if machine is None:
        return
    try:
        selection = select_tool(data["operation"], data["iso_group"], message.text, machine)
    except ValueError as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}\n\n{tool_parameter_prompt(data['operation'])}")
        return
    await state.clear()
    await message.answer(format_tool_selection(
        selection, data["operation"], data["material_name"], data["iso_group"]
    ))


async def start_multi_operations(callback: CallbackQuery, state: FSMContext, machine_id: int) -> None:
    if not await allowed(callback.from_user.id, "multi_operations", callback.message):
        return
    await state.clear()
    await state.update_data(machine_id=machine_id, selected_operations=[])
    await state.set_state(MultiToolWizard.choosing_operations)
    await callback.message.answer(
        "<b>🧩 Выберите несколько операций</b>\nНажимайте операции, затем «Готово».",
        reply_markup=multi_operation_choices([]),
    )


@router.callback_query(MultiToolWizard.choosing_operations, F.data.startswith("multiop:"))
async def multi_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    code = callback.data.split(":", 1)[1]
    data = await state.get_data()
    selected = list(data.get("selected_operations", []))
    if code == "clear":
        selected = []
    elif code == "done":
        if not selected:
            await callback.answer("Выберите хотя бы одну операцию", show_alert=True)
            return
        materials = await api.materials()
        await state.set_state(MultiToolWizard.choosing_material)
        await callback.message.edit_text("Выберите материал для комплекта операций:", reply_markup=material_choices(materials, "multimat"))
        await callback.answer(); return
    elif code in OPERATION_LABELS:
        if code in selected:
            selected.remove(code)
        else:
            selected.append(code)
    await state.update_data(selected_operations=selected)
    await callback.message.edit_reply_markup(reply_markup=multi_operation_choices(selected))
    await callback.answer()


@router.callback_query(MultiToolWizard.choosing_material, F.data.startswith("multimat:"))
async def multi_material(callback: CallbackQuery, state: FSMContext) -> None:
    material_id = int(callback.data.split(":", 1)[1])
    materials = await api.materials()
    material = next((item for item in materials if item["id"] == material_id), None)
    if material is None:
        await callback.answer("Материал не найден", show_alert=True); return
    data = await state.get_data()
    selected = data["selected_operations"]
    await state.update_data(
        material_name=material["name"], material_code=material["code"],
        iso_group=(material.get("iso_group") or "P").upper(), operation_index=0, results=[],
    )
    await state.set_state(MultiToolWizard.entering_parameters)
    first = selected[0]
    await callback.message.edit_text(
        f"<b>Операция 1/{len(selected)}:</b> {html.escape(OPERATION_LABELS[first])}\n\n"
        + tool_parameter_prompt(first)
    )
    await callback.answer()


@router.message(MultiToolWizard.entering_parameters, F.text)
async def multi_parameters(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    selected = data["selected_operations"]
    index = int(data["operation_index"])
    operation = selected[index]
    machine = await get_machine_or_error(message.from_user.id, data["machine_id"], message)
    if machine is None:
        return
    try:
        selection = select_tool(operation, data["iso_group"], message.text, machine)
    except ValueError as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}\n\n{tool_parameter_prompt(operation)}")
        return
    results = list(data.get("results", []))
    results.append({
        "operation": operation,
        "operation_label": OPERATION_LABELS[operation],
        "parameters": message.text,
        "tool": selection.holder,
        "cutting_part": selection.cutting_part,
        "cutting_data": selection.cutting_data,
        "warnings": list(selection.warnings),
    })
    index += 1
    if index < len(selected):
        await state.update_data(operation_index=index, results=results)
        next_op = selected[index]
        await message.answer(
            f"✅ {html.escape(OPERATION_LABELS[operation])} добавлена.\n\n"
            f"<b>Операция {index + 1}/{len(selected)}:</b> {html.escape(OPERATION_LABELS[next_op])}\n\n"
            + tool_parameter_prompt(next_op)
        )
        return
    try:
        plan = await api.create_process_plan({
            "telegram_id": message.from_user.id,
            "machine_id": data["machine_id"],
            "title": f"Комплект из {len(results)} операций",
            "material_code": data["material_code"],
            "operations": results,
        })
    except CNCAPIError as exc:
        await message.answer(f"⚠️ План рассчитан, но не сохранён: {html.escape(str(exc))}")
        plan = {"id": "—"}
    await state.clear()
    lines = [
        f"<b>✅ Комплект операций #{plan.get('id')}</b>",
        f"Материал: {html.escape(data['material_name'])} (ISO {html.escape(data['iso_group'])})",
    ]
    for i, item in enumerate(results, 1):
        lines.append(
            f"\n<b>{i}. {html.escape(item['operation_label'])}</b>\n"
            f"Державка/оснастка: <code>{html.escape(item['tool'])}</code>\n"
            f"Режущая часть: <code>{html.escape(item['cutting_part'])}</code>\n"
            f"{html.escape(item['cutting_data'])}"
        )
    lines.append("\n⚠️ Это стартовый подбор. Перед запуском проверьте паспорт станка и каталог производителя инструмента.")
    await message.answer("\n".join(lines)[:4000])


@router.callback_query(F.data.startswith("catroot:"))
async def catalog_root(callback: CallbackQuery) -> None:
    machine_id = int(callback.data.split(":", 1)[1])
    await callback.message.edit_text("Выберите категорию:", reply_markup=catalog_categories(machine_id))
    await callback.answer()


@router.callback_query(F.data.startswith("catc:"))
async def catalog_category(callback: CallbackQuery) -> None:
    _, machine_id_raw, category, page_raw = callback.data.split(":", 3)
    machine_id, page = int(machine_id_raw), int(page_raw)
    try:
        items = await api.tools(category=category, page=page, limit=8)
    except CNCAPIError as exc:
        await callback.message.answer(f"⚠️ {html.escape(str(exc))}"); await callback.answer(); return
    if not items and page > 0:
        await callback.answer("Больше позиций нет", show_alert=True); return
    await callback.message.edit_text(
        f"<b>{html.escape(CATEGORY_LABELS.get(category, category))}</b> · страница {page + 1}",
        reply_markup=catalog_items(machine_id, category, page, items),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cati:"))
async def catalog_item(callback: CallbackQuery) -> None:
    _, machine_id_raw, tool_key, category, page_raw = callback.data.split(":", 4)
    try:
        item = await api.tool(tool_key)
    except CNCAPIError as exc:
        await callback.message.answer(f"⚠️ {html.escape(str(exc))}"); await callback.answer(); return
    text = (
        f"<b>🔩 {html.escape(item['name'])}</b>\n"
        f"Код: <code>{html.escape(item['code'])}</code>\n"
        f"Категория: {html.escape(CATEGORY_LABELS.get(item['category'], item['category']))}\n"
        f"ISO: <code>{html.escape(', '.join(item.get('iso_groups') or []))}</code>\n\n"
        f"Размеры: {html.escape(item.get('dimensions') or '—')}\n"
        f"Назначение: {html.escape(item.get('description') or '—')}\n"
        f"Совместимость: {html.escape(item.get('compatibility') or '—')}\n"
        f"Подсказка: {html.escape(item.get('grade_hint') or '—')}\n\n"
        f"Источник: {html.escape(item.get('source') or '—')}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=catalog_item_actions(int(machine_id_raw), tool_key, category, int(page_raw)),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cats:"))
async def catalog_save(callback: CallbackQuery) -> None:
    _, machine_id_raw, tool_key = callback.data.split(":", 2)
    try:
        item = await api.tool(tool_key)
        await api.save_tool({
            "telegram_id": callback.from_user.id, "machine_id": int(machine_id_raw),
            "tool_key": tool_key, "tool_snapshot": item,
        })
    except CNCAPIError as exc:
        await callback.message.answer(f"⚠️ {html.escape(str(exc))}")
    else:
        await callback.answer("Сохранено для станка", show_alert=True)
        return
    await callback.answer()


async def show_saved_tools(target: Message, telegram_id: int, machine_id: int) -> None:
    try:
        items = await api.saved_tools(telegram_id, machine_id)
    except CNCAPIError as exc:
        await target.answer(f"⚠️ {html.escape(str(exc))}"); return
    if not items:
        await target.answer("⭐ Сохранённых инструментов пока нет.")
        return
    lines = ["<b>⭐ Сохранённый инструмент</b>"]
    for index, saved in enumerate(items[:30], 1):
        item = saved.get("tool_snapshot") or {}
        lines.append(
            f"\n<b>{index}. {html.escape(item.get('name', saved['tool_key']))}</b>\n"
            f"<code>{html.escape(item.get('code', saved['tool_key']))}</code>"
        )
    await target.answer("\n".join(lines)[:4000])


@router.message(F.text == "🧮 Калькуляторы")
async def calculators_start(message: Message, state: FSMContext) -> None:
    if not await allowed(message.from_user.id, "calculators", message):
        return
    await state.clear()
    await state.set_state(CalculatorWizard.choosing)
    await message.answer("<b>🧮 Калькуляторы FULL PRO</b>", reply_markup=calculator_choices())


@router.callback_query(CalculatorWizard.choosing, F.data.startswith("calc:"))
async def calculator_choose(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    spec = next((item for item in CALCULATORS if item.key == key), None)
    if spec is None:
        await callback.answer("Калькулятор не найден", show_alert=True); return
    await state.update_data(calculator_key=key)
    await state.set_state(CalculatorWizard.entering_values)
    await callback.message.edit_text(f"<b>{html.escape(spec.label)}</b>\n\n{html.escape(spec.prompt)}\n\nДля отмены: /cancel")
    await callback.answer()


@router.message(CalculatorWizard.entering_values, F.text)
async def calculator_values(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    key = data["calculator_key"]
    values = parse_numbers(message.text)
    count = expected_count(key)
    if len(values) != count:
        spec = next(item for item in CALCULATORS if item.key == key)
        await message.answer(f"⚠️ Нужно ровно {count} чисел.\n{html.escape(spec.prompt)}")
        return
    try:
        result = calculate(key, values)
    except (ValueError, ZeroDivisionError) as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}")
        return
    await state.clear()
    await message.answer(f"<b>Результат</b>\n<pre>{html.escape(result)}</pre>\n⚠️ Перед вводом в стойку проверьте единицы и ограничения станка.")


@router.message(GCodeCheck.waiting_code, F.text)
async def gcode_check(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    findings = analyze_gcode(message.text, data.get("controller_name", ""))
    await state.clear()
    icons = {"error": "🔴", "warning": "🟠", "info": "🔵"}
    lines = ["<b>🛡 Статическая проверка G-кода</b>"]
    for item in findings:
        lines.append(f"\n{icons.get(item.severity, '•')} <b>{html.escape(item.title)}</b>\n{html.escape(item.details)}")
    lines.append("\n⚠️ Проверка не является симуляцией станка. Выполните графику, Single Block и сухой прогон.")
    await message.answer("\n".join(lines)[:4000])


@router.message(AlarmCheck.waiting_alarm, F.text)
async def alarm_check(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    text = diagnose_alarm(message.text, data.get("controller_name", ""))
    await state.clear()
    await message.answer(text)


async def show_process(target: Message, telegram_id: int, machine_id: int, machine_name: str) -> None:
    try:
        operations = await api.operations(telegram_id, machine_id)
        plans = await api.process_plans(telegram_id, machine_id)
    except CNCAPIError as exc:
        await target.answer(f"⚠️ {html.escape(str(exc))}"); return
    if not operations and not plans:
        await target.answer("<b>📝 Техпроцесс пока пуст</b>\nСоздайте комплект через «➕ Операции».")
        return
    parts = [f"<b>📝 Техпроцесс: {html.escape(machine_name)}</b>"]
    for plan in plans[:10]:
        parts.append(f"\n<b>Комплект #{plan['id']}: {html.escape(plan['title'])}</b>\nМатериал: {html.escape(plan.get('material_code') or '—')}")
        for idx, op in enumerate(plan.get("operations") or [], 1):
            parts.append(
                f"{idx}. {html.escape(op.get('operation_label', op.get('operation', 'Операция')))} — "
                f"<code>{html.escape(op.get('tool', ''))}</code> + <code>{html.escape(op.get('cutting_part', ''))}</code>"
            )
    for index, op in enumerate(operations[:10], 1):
        parts.append(f"\n{index}. <b>{html.escape(op['title'])}</b> — {html.escape(op['details'])}")
    parts.append("\n⚠️ Добавьте установ, базирование, контроль размеров и безопасный отвод.")
    await target.answer("\n".join(parts)[:4000])


@router.message(F.text == "📚 G/M-коды")
async def code_search_start(message: Message, state: FSMContext) -> None:
    if not await allowed(message.from_user.id, "codes", message):
        return
    await state.clear()
    await state.set_state(CodeSearch.waiting_query)
    await message.answer("Введите код или название, например <code>G96</code>, <code>M3</code>, «резьба».")


@router.message(CodeSearch.waiting_query, F.text)
async def code_search_result(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        items = await api.codes(message.text)
    except CNCAPIError as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}"); return
    if not items:
        await message.answer("Ничего не найдено."); return
    parts = []
    for item in items:
        controller = item.get("controller") or {}
        manufacturer = controller.get("manufacturer") or {}
        parts.append(
            f"<b>{html.escape(item['code'])} — {html.escape(item['title'])}</b>\n"
            f"Стойка: {html.escape(manufacturer.get('name', ''))} {html.escape(controller.get('name', ''))}\n"
            f"{html.escape(item['description'])}\nСинтаксис: <code>{html.escape(item.get('syntax') or '—')}</code>"
        )
    await message.answer("\n\n".join(parts)[:4000])


@router.message(F.text == "🧱 Материалы")
async def materials_list(message: Message) -> None:
    try:
        items = await api.materials()
    except CNCAPIError as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}"); return
    lines = ["<b>🧱 Материалы</b>"]
    for item in items[:50]:
        lines.append(
            f"\n<b>{html.escape(item['code'])}</b> — {html.escape(item['name'])}\n"
            f"ISO: {html.escape(item.get('iso_group') or '—')}; Vc: {item.get('vc_min') or '—'}–{item.get('vc_max') or '—'} м/мин"
        )
    await message.answer("\n".join(lines)[:4000])


@router.message(F.text == "⚙️ Стойки ЧПУ")
async def controllers_list(message: Message) -> None:
    try:
        items = await api.controllers()
    except CNCAPIError as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}"); return
    lines = ["<b>⚙️ Стойки ЧПУ в базе</b>"]
    for item in items:
        manufacturer = item.get("manufacturer") or {}
        lines.append(f"\n• {html.escape(manufacturer.get('name', ''))} — {html.escape(item['name'])}")
    await message.answer("".join(lines)[:4000])


@router.message(F.text == "ℹ️ О проекте")
async def about(message: Message) -> None:
    try:
        info = await api.tool_categories()
    except CNCAPIError:
        info = {"count": "—"}
    await message.answer(
        "<b>CNC Master Cloud FULL PRO v1.0.0</b>\n"
        "Создатель: <b>Єрошов Іван</b>\n"
        f"Стандартных позиций инструмента: <b>{info.get('count')}</b>+\n\n"
        "Модули: станки и стойки, подбор инструмента, готовый каталог, несколько операций, "
        "калькуляторы, G/M-коды, проверка G-кода, ошибки и техпроцесс.\n\n"
        "Администратор управляет часовыми лимитами и временем доступности функций через /admin.\n\n"
        "⚠️ Рекомендации стартовые. Оператор обязан проверить паспорт станка, фактическую оснастку и каталог изготовителя."
    )


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Выберите кнопку меню или отправьте /start.", reply_markup=main_menu())


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not configured")
    await api.start()
    try:
        storage = RedisStorage.from_url(settings.redis_url) if settings.redis_url else MemoryStorage()
        dispatcher = Dispatcher(storage=storage)
        dispatcher.include_router(router)
        bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        await dispatcher.start_polling(bot)
    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())
