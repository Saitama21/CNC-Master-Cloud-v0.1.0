import asyncio
import html
import logging

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
from app.cnc_logic import (
    MACHINE_TYPE_LABELS,
    OPERATION_LABELS,
    analyze_gcode,
    calculate_milling,
    calculate_turning,
    capability_lines,
    diagnose_alarm,
    known_specs,
)
from app.config import settings
from app.tool_catalog import (
    ISO_LABELS,
    format_tool_selection,
    select_tool,
    tool_parameter_prompt,
)
from app.keyboards import (
    calculation_choices,
    controllers as controllers_keyboard,
    machine_dashboard,
    machine_selector,
    machine_types,
    main_menu,
    manufacturers as manufacturers_keyboard,
    material_choices,
    tool_material_choices,
    operation_choices,
)

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


class ModeWizard(StatesGroup):
    choosing_mode = State()
    entering_values = State()


class OperationWizard(StatesGroup):
    choosing_operation = State()
    choosing_material = State()
    entering_details = State()


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


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        await api.upsert_user(message.from_user)
    except CNCAPIError:
        logger.exception("Unable to upsert Telegram user")
        await message.answer("⚠️ Сервер базы временно недоступен. Проверь запуск API и базы.")
        return

    await message.answer(
        "<b>⚙️ CNC Master Cloud v0.3.0</b>\n\n"
        "Облачная база стоек ЧПУ и рабочие модули выбранного станка.",
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
        "<b>3/4. Выберите модель стойки:</b>",
        reply_markup=controllers_keyboard(items),
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
    if len(name) > 150:
        await message.answer("Название слишком длинное. Максимум 150 символов.")
        return
    await state.update_data(name=name)
    await state.set_state(MachineWizard.entering_axes)
    await message.answer(
        "Укажите оси станка, например <code>X/Z</code>, <code>X/Z/C</code> или <code>X/Z/Y/C</code>.\n"
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

    # Всегда показываем выбор профиля, даже если станок пока только один.
    # Так интерфейс ведёт себя одинаково сегодня и после добавления новых станков.
    await message.answer(
        "<b>Выберите станок, с которым хотите работать:</b>",
        reply_markup=machine_selector(items),
    )


@router.callback_query(F.data == "machine:add")
async def add_machine_from_selector(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(MachineWizard.choosing_type)
    await callback.message.edit_text(
        "<b>1/4. Выберите тип оборудования:</b>",
        reply_markup=machine_types(),
    )
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
            lines.extend([
                "",
                f"Производитель станка: {html.escape(specs['manufacturer'])}",
                f"Модель: {html.escape(specs['model'])}",
                f"Мощность: {html.escape(specs['power'])}",
                f"Макс. диаметр прутка: {html.escape(specs['max_bar'])}",
                f"Масса: {html.escape(specs['weight'])}",
                f"Питание: {html.escape(specs['power_supply'])}",
                f"Источник: {html.escape(specs['source'])}",
            ])
        await callback.message.answer("\n".join(lines))

    elif action == "caps":
        lines = [f"<b>🧭 Возможности {html.escape(machine['name'])}</b>"]
        lines.extend(f"\n• {html.escape(item)}" for item in capability_lines(machine))
        await callback.message.answer("".join(lines))

    elif action == "tool":
        await state.clear()
        await state.update_data(machine_id=machine_id)
        await state.set_state(ToolWizard.choosing_operation)
        await callback.message.answer("Выберите операцию:", reply_markup=operation_choices("toolop"))

    elif action == "modes":
        await state.clear()
        await state.update_data(machine_id=machine_id)
        await state.set_state(ModeWizard.choosing_mode)
        await callback.message.answer("Выберите расчёт:", reply_markup=calculation_choices())

    elif action == "operation":
        await state.clear()
        await state.update_data(machine_id=machine_id)
        await state.set_state(OperationWizard.choosing_operation)
        await callback.message.answer("Выберите операцию для техпроцесса:", reply_markup=operation_choices("opcreate"))

    elif action == "gcode":
        await state.clear()
        await state.update_data(machine_id=machine_id, controller_name=controller_name)
        await state.set_state(GCodeCheck.waiting_code)
        await callback.message.answer(
            "Вставьте G-код одним сообщением. Я выполню статическую проверку типовых рисков.\n"
            "Для отмены: /cancel"
        )

    elif action == "alarms":
        await state.clear()
        await state.update_data(machine_id=machine_id, controller_name=controller_name)
        await state.set_state(AlarmCheck.waiting_alarm)
        await callback.message.answer(
            "Отправьте полный номер и текст ошибки со стойки.\n"
            "Например: <code>700012 spindle...</code>"
        )

    elif action == "process":
        try:
            operations = await api.operations(callback.from_user.id, machine_id)
        except CNCAPIError as exc:
            await callback.message.answer(f"⚠️ {html.escape(str(exc))}")
        else:
            if not operations:
                await callback.message.answer(
                    "<b>📝 Техпроцесс пока пуст</b>\n\n"
                    "Сначала добавьте операции через «➕ Создать операцию»."
                )
            else:
                parts = [f"<b>📝 Техпроцесс: {html.escape(machine['name'])}</b>"]
                for index, op in enumerate(operations, 1):
                    parts.append(
                        f"\n<b>{index}. {html.escape(op['title'])}</b>\n"
                        f"Материал: {html.escape(op.get('material_code') or 'не указан')}\n"
                        f"{html.escape(op['details'])}"
                    )
                parts.append(
                    "\n\n⚠️ Перед обработкой добавьте установ, базирование, инструмент, контрольный размер и безопасный отвод."
                )
                await callback.message.answer("\n".join(parts)[:4000])
    await callback.answer()


@router.callback_query(ToolWizard.choosing_operation, F.data.startswith("toolop:"))
async def tool_choose_operation(callback: CallbackQuery, state: FSMContext) -> None:
    operation = callback.data.split(":", 1)[1]
    await state.update_data(operation=operation)
    try:
        materials = await api.materials()
    except CNCAPIError as exc:
        await callback.message.answer(f"⚠️ {html.escape(str(exc))}")
        await callback.answer()
        return
    await state.set_state(ToolWizard.choosing_material)
    await callback.message.edit_text(
        "Выберите материал из базы или только ISO-группу:",
        reply_markup=tool_material_choices(materials),
    )
    await callback.answer()


@router.callback_query(ToolWizard.choosing_material, F.data.startswith("toolmat:"))
async def tool_choose_material(callback: CallbackQuery, state: FSMContext) -> None:
    material_id = int(callback.data.split(":", 1)[1])
    try:
        materials = await api.materials()
    except CNCAPIError as exc:
        await callback.message.answer(f"⚠️ {html.escape(str(exc))}")
        await callback.answer()
        return
    material = next((item for item in materials if item["id"] == material_id), None)
    if material is None:
        await callback.message.answer("Материал не найден.")
        await callback.answer()
        return
    data = await state.get_data()
    operation = data["operation"]
    await state.update_data(
        material_name=material["name"],
        iso_group=(material.get("iso_group") or "P").upper(),
    )
    await state.set_state(ToolWizard.entering_parameters)
    await callback.message.edit_text(
        f"<b>Материал:</b> {html.escape(material['name'])} (ISO {html.escape(material.get('iso_group') or '—')})\n\n"
        + tool_parameter_prompt(operation)
    )
    await callback.answer()


@router.callback_query(ToolWizard.choosing_material, F.data.startswith("tooliso:"))
async def tool_choose_iso_group(callback: CallbackQuery, state: FSMContext) -> None:
    iso_group = callback.data.split(":", 1)[1].upper()
    if iso_group not in ISO_LABELS:
        await callback.answer("Неизвестная ISO-группа", show_alert=True)
        return
    data = await state.get_data()
    operation = data["operation"]
    material_name = f"ISO {iso_group} — {ISO_LABELS[iso_group]}"
    await state.update_data(material_name=material_name, iso_group=iso_group)
    await state.set_state(ToolWizard.entering_parameters)
    await callback.message.edit_text(
        f"<b>Материал:</b> {html.escape(material_name)}\n\n" + tool_parameter_prompt(operation)
    )
    await callback.answer()


@router.message(ToolWizard.entering_parameters, F.text)
async def tool_enter_parameters(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    machine = await get_machine_or_error(message.from_user.id, data["machine_id"], message)
    if machine is None:
        return
    try:
        selection = select_tool(
            data["operation"],
            data["iso_group"],
            message.text,
            machine,
        )
    except ValueError as exc:
        await message.answer(
            f"⚠️ {html.escape(str(exc))}\n\n" + tool_parameter_prompt(data["operation"])
        )
        return
    result = format_tool_selection(
        selection,
        data["operation"],
        html.escape(data["material_name"]),
        html.escape(data["iso_group"]),
    )
    await state.clear()
    await message.answer(result[:4000], reply_markup=main_menu())


@router.callback_query(ModeWizard.choosing_mode, F.data.startswith("calc:"))
async def calc_choose(callback: CallbackQuery, state: FSMContext) -> None:
    mode = callback.data.split(":", 1)[1]
    await state.update_data(calc_mode=mode)
    await state.set_state(ModeWizard.entering_values)
    if mode == "turning":
        text = (
            "Введите через пробел: <code>диаметр Vc подача_мм/об</code>\n"
            "Пример: <code>90 180 0.20</code>"
        )
    else:
        text = (
            "Введите: <code>диаметр_фрезы Vc число_зубьев fz</code>\n"
            "Пример: <code>10 120 4 0.05</code>"
        )
    await callback.message.edit_text(text)
    await callback.answer()


@router.message(ModeWizard.entering_values, F.text)
async def calc_values(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    raw = message.text.replace(",", ".").split()
    try:
        if data["calc_mode"] == "turning":
            if len(raw) != 3:
                raise ValueError("Нужно три числа")
            d, vc, feed = map(float, raw)
            result = calculate_turning(d, vc, feed)
            details = (
                f"Диаметр: {d:g} мм\nVc: {vc:g} м/мин\nПодача: {feed:g} мм/об\n\n"
                f"Обороты: <b>{result['rpm']:.0f} об/мин</b>\n"
                f"Минутная подача: <b>{result['feed_mm_min']:.0f} мм/мин</b>"
            )
        else:
            if len(raw) != 4:
                raise ValueError("Нужно четыре числа")
            d, vc, teeth_raw, fz = map(float, raw)
            teeth = int(teeth_raw)
            result = calculate_milling(d, vc, teeth, fz)
            details = (
                f"Диаметр: {d:g} мм\nVc: {vc:g} м/мин\nЗубья: {teeth}\nfz: {fz:g} мм/зуб\n\n"
                f"Обороты: <b>{result['rpm']:.0f} об/мин</b>\n"
                f"Минутная подача: <b>{result['feed_mm_min']:.0f} мм/мин</b>"
            )
    except (ValueError, KeyError):
        await message.answer("Неверный формат или нулевое значение. Попробуйте ещё раз либо /cancel.")
        return
    await state.clear()
    await message.answer(
        f"<b>🧮 Расчёт режимов</b>\n\n{details}\n\n"
        "⚠️ Ограничьте результат паспортом станка и каталогом конкретного инструмента.",
        reply_markup=main_menu(),
    )


@router.callback_query(OperationWizard.choosing_operation, F.data.startswith("opcreate:"))
async def operation_choose(callback: CallbackQuery, state: FSMContext) -> None:
    operation = callback.data.split(":", 1)[1]
    await state.update_data(operation=operation)
    materials = await api.materials()
    await state.set_state(OperationWizard.choosing_material)
    await callback.message.edit_text("Выберите материал:", reply_markup=material_choices(materials, "opmat"))
    await callback.answer()


@router.callback_query(OperationWizard.choosing_material, F.data.startswith("opmat:"))
async def operation_material(callback: CallbackQuery, state: FSMContext) -> None:
    material_id = int(callback.data.split(":", 1)[1])
    materials = await api.materials()
    material = next((item for item in materials if item["id"] == material_id), None)
    if material is None:
        await callback.message.answer("Материал не найден.")
        await callback.answer()
        return
    await state.update_data(material_code=material["code"])
    await state.set_state(OperationWizard.entering_details)
    await callback.message.edit_text(
        "Опишите операцию и размеры.\n"
        "Пример: <code>Расточить отверстие с Ø85 до Ø90, глубина 12 мм, оставить 0,2 мм на чистовой</code>"
    )
    await callback.answer()


@router.message(OperationWizard.entering_details, F.text)
async def operation_details(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    details = message.text.strip()
    try:
        item = await api.create_operation({
            "telegram_id": message.from_user.id,
            "machine_id": data["machine_id"],
            "operation_type": data["operation"],
            "title": OPERATION_LABELS.get(data["operation"], data["operation"]),
            "material_code": data.get("material_code"),
            "details": details,
            "parameters": {},
        })
    except CNCAPIError as exc:
        await message.answer(f"⚠️ Не удалось сохранить: {html.escape(str(exc))}")
        return
    await state.clear()
    await message.answer(
        f"✅ Операция сохранена в техпроцесс: <b>{html.escape(item['title'])}</b>",
        reply_markup=main_menu(),
    )


@router.message(GCodeCheck.waiting_code, F.text)
async def gcode_check(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    findings = analyze_gcode(message.text, data.get("controller_name", ""))
    icons = {"ok": "🟢", "warning": "🟡", "error": "🔴"}
    parts = ["<b>🛡 Проверка G-кода</b>"]
    for item in findings:
        parts.append(
            f"\n{icons.get(item.severity, '•')} <b>{html.escape(item.title)}</b>\n"
            f"{html.escape(item.details)}"
        )
    parts.append(
        "\n\nПроверка статическая и не заменяет симуляцию, Single Block, Dry Run и контроль коррекций."
    )
    await state.clear()
    await message.answer("\n".join(parts)[:4000], reply_markup=main_menu())


@router.message(AlarmCheck.waiting_alarm, F.text)
async def alarm_check(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    result = diagnose_alarm(message.text, data.get("controller_name", ""))
    await state.clear()
    await message.answer(
        f"<b>❗ Диагностика ошибки</b>\n\n{html.escape(result)}\n\n"
        "⚠️ Не обходите цепи безопасности и не сбрасывайте аварии до устранения причины.",
        reply_markup=main_menu(),
    )


@router.message(F.text == "📚 G/M-коды")
async def code_search_start(message: Message, state: FSMContext) -> None:
    await state.set_state(CodeSearch.waiting_query)
    await message.answer(
        "Введите код или название команды. Примеры: <code>G96</code>, <code>M30</code>."
    )


@router.message(CodeSearch.waiting_query, F.text)
async def code_search_result(message: Message, state: FSMContext) -> None:
    try:
        items = await api.codes(message.text.strip())
    except CNCAPIError as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}")
        return
    await state.clear()
    if not items:
        await message.answer("Ничего не найдено.", reply_markup=main_menu())
        return
    parts = [f"<b>Результаты: {html.escape(message.text.strip())}</b>"]
    for item in items:
        controller, manufacturer = controller_parts({"controller": item.get("controller")})
        marker = "🟢" if item.get("verification_status") == "verified" else "🟡"
        parts.append(
            f"\n{marker} <b>{html.escape(item['code'])} — {html.escape(item['title'])}</b>\n"
            f"{html.escape(manufacturer.get('name', ''))} / {html.escape(controller.get('name', ''))}\n"
            f"{html.escape(item['description'])}\n"
            f"<code>{html.escape(item.get('syntax') or 'Синтаксис не указан')}</code>"
        )
    await message.answer("\n".join(parts)[:4000], reply_markup=main_menu())


@router.message(F.text == "🧱 Материалы")
async def materials_list(message: Message) -> None:
    try:
        items = await api.materials()
    except CNCAPIError as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}")
        return
    parts = ["<b>🧱 Материалы</b>"]
    for item in items:
        vc = "—"
        if item.get("vc_min") is not None and item.get("vc_max") is not None:
            vc = f"{item['vc_min']:g}–{item['vc_max']:g} м/мин"
        parts.append(
            f"\n<b>{html.escape(item['code'])}: {html.escape(item['name'])}</b>\n"
            f"ISO: {html.escape(item.get('iso_group') or '—')}; Vc: {vc}"
        )
    await message.answer("\n".join(parts)[:4000])


@router.message(F.text == "⚙️ Стойки ЧПУ")
async def controllers_list(message: Message) -> None:
    try:
        items = await api.controllers()
    except CNCAPIError as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}")
        return
    grouped: dict[str, list[str]] = {}
    for item in items:
        manufacturer = (item.get("manufacturer") or {}).get("name", "Другое")
        grouped.setdefault(manufacturer, []).append(item["name"])
    parts = ["<b>⚙️ Стойки в онлайн-базе</b>"]
    for manufacturer, names in sorted(grouped.items()):
        parts.append(f"\n<b>{html.escape(manufacturer)}</b>\n" + "\n".join(f"• {html.escape(name)}" for name in names))
    await message.answer("\n".join(parts)[:4000])


@router.message(F.text == "ℹ️ О проекте")
async def about(message: Message) -> None:
    await message.answer(
        "<b>CNC Master Cloud v0.3.0</b>\n\n"
        "Модуль «Мой станок»: характеристики, возможности осей, инструмент, режимы, операции, G-код, ошибки и техпроцесс.\n\n"
        "Создатель: <b>Єрошов Іван</b>"
    )


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Используйте кнопки меню или /cancel.", reply_markup=main_menu())


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty")
    storage = RedisStorage.from_url(settings.redis_url) if settings.redis_url else MemoryStorage()
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    await api.start()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await api.close()
        await storage.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
