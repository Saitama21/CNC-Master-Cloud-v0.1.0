from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CNCCode, ControllerModel, Manufacturer, Material


MANUFACTURERS = [
    ("Siemens", "siemens", "https://www.siemens.com/"),
    ("FANUC", "fanuc", "https://www.fanuc.eu/"),
    ("HEIDENHAIN", "heidenhain", "https://www.heidenhain.com/"),
    ("Haas", "haas", "https://www.haascnc.com/"),
    ("Mitsubishi Electric", "mitsubishi", "https://www.mitsubishielectric.com/"),
    ("Mazak", "mazak", "https://www.mazak.com/"),
    ("Okuma", "okuma", "https://www.okuma.com/"),
    ("Fagor Automation", "fagor", "https://www.fagorautomation.com/"),
]

CONTROLLERS = {
    "siemens": [
        ("SINUMERIK 828D", "SINUMERIK", ["turning", "milling"], ["4.x"]),
        ("SINUMERIK 840D sl", "SINUMERIK", ["turning", "milling", "multitasking"], []),
        ("SINUMERIK ONE", "SINUMERIK", ["turning", "milling", "multitasking"], []),
    ],
    "fanuc": [
        ("0i-F Plus", "0i", ["turning", "milling"], []),
        ("30i/31i/32i-B Plus", "30i/31i/32i", ["turning", "milling", "multitasking"], []),
    ],
    "heidenhain": [
        ("TNC 640", "TNC", ["milling", "5-axis"], []),
        ("TNC7", "TNC", ["milling", "5-axis"], []),
        ("CNC PILOT 640", "CNC PILOT", ["turning", "multitasking"], []),
    ],
    "haas": [
        ("Next Generation Control", "NGC", ["turning", "milling", "5-axis"], []),
    ],
    "mitsubishi": [
        ("M80V", "M8V", ["turning", "milling"], []),
        ("M800V", "M8V", ["turning", "milling", "multitasking"], []),
    ],
    "mazak": [
        ("MAZATROL SmoothG", "Smooth", ["turning", "milling", "multitasking"], []),
        ("MAZATROL SmoothAi", "Smooth", ["turning", "milling", "multitasking", "5-axis"], []),
    ],
    "okuma": [
        ("OSP-P300A", "OSP", ["turning", "milling", "multitasking"], []),
        ("OSP-P500", "OSP", ["turning", "milling", "multitasking"], []),
    ],
    "fagor": [
        ("CNC 8060", "8060", ["turning", "milling"], []),
        ("CNC 8065", "8065", ["turning", "milling", "5-axis"], []),
        ("CNC 8070", "8070", ["turning", "milling", "multitasking"], []),
    ],
}

MATERIALS = [
    ("AISI304", "Нержавеющая сталь AISI 304", "M", 120.0, 220.0,
     "Диапазон ориентировочный. Итоговые режимы зависят от пластины, покрытия, жёсткости и СОЖ."),
    ("AISI316", "Нержавеющая сталь AISI 316", "M", 100.0, 190.0,
     "Склонна к наклёпу. Не допускать длительного трения инструмента без резания."),
    ("C45", "Конструкционная сталь C45", "P", 160.0, 280.0,
     "Уточняйте режим по твёрдости заготовки и каталогу изготовителя инструмента."),
    ("AL6061", "Алюминий 6061", "N", 300.0, 800.0,
     "Нужна острая геометрия и хороший отвод стружки."),
    ("PA6", "Полиамид PA6", "N", 150.0, 500.0,
     "Следить за нагревом и деформацией; применять острый инструмент."),
]

COMMON_CODES = [
    ("G", "G0", "Ускоренное позиционирование",
     "Перемещение осей на ускоренной подаче. Точная траектория и модальность зависят от стойки.",
     "G0 X... Z...", "G0 X100 Z5",
     "Перед запуском проверьте безопасные координаты и Rapid Override."),
    ("G", "G1", "Линейная интерполяция",
     "Рабочее линейное перемещение с заданной подачей.",
     "G1 X... Z... F...", "G1 X80 Z-20 F0.2",
     "Проверьте режим подачи: мм/об, мм/мин или дюймы."),
    ("G", "G96", "Постоянная скорость резания",
     "Поддержание приблизительно постоянной скорости резания изменением оборотов шпинделя.",
     "G96 S...", "G96 S180",
     "Обязательно задайте безопасное ограничение максимальных оборотов согласно стойке."),
    ("G", "G97", "Постоянные обороты шпинделя",
     "Переход к работе с фиксированной частотой вращения шпинделя.",
     "G97 S...", "G97 S800",
     "Убедитесь, что направление вращения и диапазон шпинделя выбраны верно."),
    ("M", "M3", "Шпиндель по часовой стрелке",
     "Запуск шпинделя в направлении, определённом изготовителем станка как M3.",
     "M3 S...", "M3 S800",
     "Проверьте ориентацию инструмента и фактическое направление вращения."),
    ("M", "M4", "Шпиндель против часовой стрелки",
     "Запуск шпинделя в направлении, определённом изготовителем станка как M4.",
     "M4 S...", "M4 S800",
     "Проверьте ориентацию инструмента и фактическое направление вращения."),
    ("M", "M5", "Останов шпинделя",
     "Команда остановки шпинделя.",
     "M5", "M5", None),
    ("M", "M30", "Конец программы",
     "Завершение программы с возвратом/сбросом, точное поведение зависит от стойки.",
     "M30", "M30", "Проверьте документацию конкретного станка."),
]


async def seed_database(session: AsyncSession) -> None:
    existing = await session.scalar(select(Manufacturer.id).limit(1))
    if existing is not None:
        return

    manufacturers_by_slug: dict[str, Manufacturer] = {}
    for name, slug, url in MANUFACTURERS:
        item = Manufacturer(name=name, slug=slug, website_url=url)
        session.add(item)
        manufacturers_by_slug[slug] = item
    await session.flush()

    controllers: list[ControllerModel] = []
    for slug, controller_rows in CONTROLLERS.items():
        manufacturer = manufacturers_by_slug[slug]
        for name, family, machine_types, versions in controller_rows:
            controller = ControllerModel(
                manufacturer_id=manufacturer.id,
                name=name,
                family=family,
                machine_types=machine_types,
                software_versions=versions,
                description="Стартовая карточка. Дополняется через онлайн-админку.",
            )
            session.add(controller)
            controllers.append(controller)
    await session.flush()

    for code, name, iso_group, vc_min, vc_max, notes in MATERIALS:
        session.add(Material(
            code=code,
            name=name,
            iso_group=iso_group,
            vc_min=vc_min,
            vc_max=vc_max,
            notes=notes,
        ))

    # Базовые команды добавляются для каждой стойки как стартовый справочник.
    # Статус needs_review напоминает проверить синтаксис по руководству конкретного станка.
    now = datetime.now(timezone.utc)
    for controller in controllers:
        for code_type, code, title, description, syntax, example, safety in COMMON_CODES:
            session.add(CNCCode(
                controller_id=controller.id,
                code_type=code_type,
                code=code,
                title=title,
                description=description,
                syntax=syntax,
                example=example,
                safety_notes=safety,
                verification_status="needs_review",
                last_verified_at=now,
            ))

    await session.commit()
