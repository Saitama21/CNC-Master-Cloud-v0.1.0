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
from app.config import settings
from app.keyboards import (
    controllers as controllers_keyboard,
    machine_types,
    main_menu,
    manufacturers as manufacturers_keyboard,
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


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        await api.upsert_user(message.from_user)
    except CNCAPIError:
        logger.exception("Unable to upsert Telegram user")
        await message.answer(
            "⚠️ Сервер базы временно недоступен. Проверь запуск API и базы."
        )
        return

    await message.answer(
        "<b>⚙️ CNC Master Cloud</b>\n\n"
        "Облачная база стоек ЧПУ, профилей станков, G/M-кодов и материалов.\n\n"
        "Начните с добавления своего станка.",
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
    await message.answer(
        "<b>1/4. Выберите тип оборудования:</b>",
        reply_markup=machine_types(),
    )


@router.callback_query(MachineWizard.choosing_type, F.data.startswith("type:"))
async def choose_type(callback: CallbackQuery, state: FSMContext) -> None:
    machine_type = callback.data.split(":", 1)[1]
    await state.update_data(machine_type=machine_type)
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


@router.callback_query(
    MachineWizard.choosing_manufacturer,
    F.data.startswith("mfr:"),
)
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


@router.callback_query(
    MachineWizard.choosing_controller,
    F.data.startswith("ctl:"),
)
async def choose_controller(callback: CallbackQuery, state: FSMContext) -> None:
    controller_id = int(callback.data.split(":", 1)[1])
    await state.update_data(controller_id=controller_id)
    await state.set_state(MachineWizard.entering_name)
    await callback.message.edit_text(
        "<b>4/4. Напишите название профиля станка.</b>\n\n"
        "Например: <code>Токарный №1</code> или <code>Doosan Lynx</code>"
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
        "Укажите оси станка, например <code>X/Z</code>, "
        "<code>X/Z/C</code> или <code>X/Y/Z/A/B</code>.\n"
        "Чтобы пропустить, отправьте <code>-</code>."
    )


@router.message(MachineWizard.entering_axes, F.text)
async def enter_machine_axes(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    axes = message.text.strip()
    if axes == "-":
        axes = None

    try:
        item = await api.create_machine({
            "telegram_id": message.from_user.id,
            "controller_id": data["controller_id"],
            "name": data["name"],
            "machine_type": data["machine_type"],
            "axes": axes,
            "driven_tools": False,
        })
    except CNCAPIError as exc:
        await message.answer(f"⚠️ Не удалось сохранить: {html.escape(str(exc))}")
        return

    await state.clear()
    controller = item.get("controller") or {}
    manufacturer = controller.get("manufacturer") or {}
    await message.answer(
        "✅ <b>Станок сохранён</b>\n\n"
        f"Профиль: <b>{html.escape(item['name'])}</b>\n"
        f"Стойка: {html.escape(manufacturer.get('name', ''))} "
        f"{html.escape(controller.get('name', ''))}\n"
        f"Оси: {html.escape(item.get('axes') or 'не указаны')}",
        reply_markup=main_menu(),
    )


@router.message(F.text == "🖥 Мои станки")
async def my_machines(message: Message) -> None:
    try:
        items = await api.machines(message.from_user.id)
    except CNCAPIError as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}")
        return

    if not items:
        await message.answer(
            "У вас пока нет сохранённых станков.\n"
            "Нажмите «➕ Добавить станок»."
        )
        return

    parts = ["<b>🖥 Мои станки</b>"]
    for index, item in enumerate(items, 1):
        controller = item.get("controller") or {}
        manufacturer = controller.get("manufacturer") or {}
        parts.append(
            f"\n<b>{index}. {html.escape(item['name'])}</b>\n"
            f"{html.escape(manufacturer.get('name', ''))} — "
            f"{html.escape(controller.get('name', ''))}\n"
            f"Тип: {html.escape(item['machine_type'])}; "
            f"оси: {html.escape(item.get('axes') or '—')}"
        )
    await message.answer("\n".join(parts))


@router.message(F.text == "📚 G/M-коды")
async def code_search_start(message: Message, state: FSMContext) -> None:
    await state.set_state(CodeSearch.waiting_query)
    await message.answer(
        "Введите код или название команды.\n"
        "Примеры: <code>G96</code>, <code>M30</code>, "
        "<code>линейная интерполяция</code>."
    )


@router.message(CodeSearch.waiting_query, F.text)
async def code_search_result(message: Message, state: FSMContext) -> None:
    query = message.text.strip()
    try:
        items = await api.codes(query)
    except CNCAPIError as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}")
        return

    await state.clear()
    if not items:
        await message.answer(
            "Ничего не найдено. Через админку можно добавить новую запись.",
            reply_markup=main_menu(),
        )
        return

    parts = [f"<b>Результаты по запросу «{html.escape(query)}»</b>"]
    for item in items:
        controller = item.get("controller") or {}
        manufacturer = controller.get("manufacturer") or {}
        status = item.get("verification_status", "needs_review")
        marker = "🟢" if status == "verified" else "🟡"
        parts.append(
            f"\n{marker} <b>{html.escape(item['code'])} — "
            f"{html.escape(item['title'])}</b>\n"
            f"{html.escape(manufacturer.get('name', ''))} / "
            f"{html.escape(controller.get('name', ''))}\n"
            f"{html.escape(item['description'])}\n"
            f"<code>{html.escape(item.get('syntax') or 'Синтаксис не указан')}</code>"
        )
    parts.append(
        "\n⚠️ Перед запуском сверяйте код с руководством именно вашего станка."
    )
    text = "\n".join(parts)
    await message.answer(text[:4000], reply_markup=main_menu())


@router.message(F.text == "🧱 Материалы")
async def materials(message: Message) -> None:
    try:
        items = await api.materials()
    except CNCAPIError as exc:
        await message.answer(f"⚠️ {html.escape(str(exc))}")
        return

    parts = ["<b>🧱 Материалы стартовой базы</b>"]
    for item in items:
        vc = "—"
        if item.get("vc_min") is not None and item.get("vc_max") is not None:
            vc = f"{item['vc_min']:g}–{item['vc_max']:g} м/мин"
        parts.append(
            f"\n<b>{html.escape(item['code'])}: "
            f"{html.escape(item['name'])}</b>\n"
            f"ISO: {html.escape(item.get('iso_group') or '—')}; "
            f"ориентир Vc: {vc}\n"
            f"{html.escape(item.get('notes') or '')}"
        )
    parts.append(
        "\n⚠️ Это стартовые ориентиры, не готовое разрешение на запуск. "
        "Финальные режимы берутся из каталога конкретной пластины."
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
        parts.append(
            f"\n<b>{html.escape(manufacturer)}</b>\n"
            + "\n".join(f"• {html.escape(name)}" for name in names)
        )
    await message.answer("\n".join(parts)[:4000])


@router.message(F.text == "ℹ️ О проекте")
async def about(message: Message) -> None:
    await message.answer(
        "<b>CNC Master Cloud v0.1.0</b>\n\n"
        "Облачный рабочий инструмент для операторов, наладчиков и технологов ЧПУ.\n\n"
        "Создатель: <b>Єрошов Іван</b>\n"
        "Статус: рабочее ядро MVP."
    )


@router.message()
async def fallback(message: Message) -> None:
    await message.answer(
        "Используйте кнопки меню или команду /cancel.",
        reply_markup=main_menu(),
    )


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Copy .env.example to .env and set it.")

    storage = (
        RedisStorage.from_url(settings.redis_url)
        if settings.redis_url
        else MemoryStorage()
    )
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    await api.start()
    try:
        await dp.start_polling(bot)
    finally:
        await api.close()
        await storage.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
