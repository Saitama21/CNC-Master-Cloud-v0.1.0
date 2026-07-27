from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any


MACHINE_TYPE_LABELS = {
    "turning": "Токарный",
    "milling": "Фрезерный",
    "multitasking": "Токарно-фрезерный",
    "5-axis": "5-осевой центр",
    "other": "Другое",
}

OPERATION_LABELS = {
    "turn_rough": "Наружное черновое точение",
    "turn_finish": "Наружное чистовое точение",
    "face": "Торцевание",
    "bore": "Расточка",
    "groove": "Канавка / отрезка",
    "thread": "Резьба",
    "drill": "Сверление",
    "mill": "Фрезерование приводным инструментом",
}

KNOWN_MACHINE_SPECS = {
    "CK52PT-Y": {
        "manufacturer": "Tengyue CNC",
        "model": "CK52PT-Y",
        "class": "Токарно-фрезерный станок с ЧПУ",
        "power": "18 кВт",
        "max_bar": "51 мм",
        "weight": "4600 кг",
        "power_supply": "380 В, 3 фазы, 50 Гц",
        "source": "Шильдик станка, предоставленный владельцем",
    }
}


@dataclass(frozen=True)
class CheckFinding:
    severity: str
    title: str
    details: str


def known_specs(machine_name: str) -> dict[str, str] | None:
    upper = machine_name.upper()
    for marker, specs in KNOWN_MACHINE_SPECS.items():
        if marker.upper() in upper:
            return specs
    return None


def normalize_axes(raw_axes: str | None) -> set[str]:
    if not raw_axes:
        return set()
    return {
        token.strip().upper()
        for token in re.split(r"[/,;\\\s]+", raw_axes)
        if token.strip()
    }


def capability_lines(machine: dict[str, Any]) -> list[str]:
    axes = normalize_axes(machine.get("axes"))
    machine_type = machine.get("machine_type") or "other"
    lines: list[str] = []

    if {"X", "Z"}.issubset(axes):
        lines.append("Токарная обработка наружных и внутренних поверхностей по X/Z.")
    if "C" in axes:
        lines.append("Индексирование шпинделя и угловое позиционирование по оси C.")
    if "Y" in axes:
        lines.append("Смещение приводного инструмента по Y для внецентровых отверстий и фрезерования.")
    if "C" in axes and machine_type == "multitasking":
        lines.append("Сверление и фрезерование приводным инструментом при подтверждённой комплектации револьвера.")
    if {"X", "Y", "Z", "C"}.issubset(axes):
        lines.append("Комплексная обработка детали за один установ: точение + сверление + лёгкое фрезерование.")
    if "A" in axes or "B" in axes:
        lines.append("Наклонная/поворотная обработка по дополнительной оси A или B.")
    if not lines:
        lines.append("Возможности пока нельзя определить: в профиле не указаны оси.")

    lines.append(
        "Фактические функции зависят от опций станка, приводных блоков, постпроцессора и параметров стойки."
    )
    return lines


def _material_advice(iso_group: str | None) -> str:
    group = (iso_group or "").upper()
    return {
        "P": "Для сталей: универсальная прочная геометрия, покрытие для ISO P.",
        "M": "Для нержавейки: острая положительная геометрия, стабильная подача, не допускать трения без резания.",
        "K": "Для чугуна: износостойкая марка, обычно сухая обработка или по рекомендации изготовителя.",
        "N": "Для алюминия/цветных: полированная острая кромка и свободный отвод стружки.",
        "S": "Для жаропрочных/титана: вязкая марка, умеренная скорость, обильная СОЖ.",
        "H": "Для закалённых: CBN/керамика или специализированный твёрдый сплав по твёрдости детали.",
    }.get(group, "Проверьте ISO-группу материала и каталог конкретного производителя инструмента.")


def tool_recommendation(operation: str, iso_group: str | None) -> dict[str, str]:
    base = {
        "turn_rough": {
            "tool": "Наружная державка PCLNR/MWLNR или совместимая",
            "insert": "CNMG или WNMG, радиус 0,8 мм",
            "use": "Черновое снятие припуска, жёсткая установка, стабильное стружколомание.",
        },
        "turn_finish": {
            "tool": "Державка для положительной или чистовой геометрии",
            "insert": "CCMT/DCMT/VNMG, радиус 0,4 мм",
            "use": "Чистовой проход с небольшим припуском и стабильной подачей.",
        },
        "face": {
            "tool": "Наружная токарная державка с подходящим углом подхода",
            "insert": "CNMG/WNMG для чернового или CCMT/DCMT для чистового торца",
            "use": "Проверить прерывистый рез, отверстия и выход пластины через центр.",
        },
        "bore": {
            "tool": "Расточная державка максимального допустимого диаметра и минимального вылета",
            "insert": "CCMT/TCMT/DCMT по диаметру расточки",
            "use": "Снизить вылет, обеспечить жёсткость, контролировать вибрацию и отвод стружки.",
        },
        "groove": {
            "tool": "Канавочная/отрезная державка нужной ширины",
            "insert": "Сменная канавочная пластина по ширине и глубине",
            "use": "Точная установка по центру, достаточная СОЖ, не занижать подачу до трения.",
        },
        "thread": {
            "tool": "Наружная 16ER или внутренняя 16IR державка подходящего размера",
            "insert": "Полный или частичный профиль под шаг резьбы",
            "use": "Сверить шаг, направление, вершину профиля и цикл конкретной стойки.",
        },
        "drill": {
            "tool": "Твердосплавное сверло или корпусное U-сверло",
            "insert": "Геометрия по материалу и диаметру отверстия",
            "use": "Проверить биение, длину вылета, давление СОЖ и цикл удаления стружки.",
        },
        "mill": {
            "tool": "Приводной блок + концевая/корпусная фреза",
            "insert": "Фреза или пластины по ISO-группе материала",
            "use": "Проверить направление блока, ограничение оборотов, фиксацию оси C и нагрузку привода.",
        },
    }.get(operation)
    if base is None:
        base = {
            "tool": "Инструмент не определён",
            "insert": "Нужны данные операции",
            "use": "Уточните тип обработки.",
        }
    return {**base, "material": _material_advice(iso_group)}


def calculate_turning(diameter_mm: float, vc_m_min: float, feed_mm_rev: float) -> dict[str, float]:
    if diameter_mm <= 0 or vc_m_min <= 0 or feed_mm_rev <= 0:
        raise ValueError("Все значения должны быть больше нуля")
    rpm = 1000.0 * vc_m_min / (math.pi * diameter_mm)
    feed_mm_min = rpm * feed_mm_rev
    return {"rpm": rpm, "feed_mm_min": feed_mm_min}


def calculate_milling(
    diameter_mm: float,
    vc_m_min: float,
    teeth: int,
    feed_per_tooth_mm: float,
) -> dict[str, float]:
    if diameter_mm <= 0 or vc_m_min <= 0 or teeth <= 0 or feed_per_tooth_mm <= 0:
        raise ValueError("Все значения должны быть больше нуля")
    rpm = 1000.0 * vc_m_min / (math.pi * diameter_mm)
    feed_mm_min = rpm * teeth * feed_per_tooth_mm
    return {"rpm": rpm, "feed_mm_min": feed_mm_min}


def _strip_comments(program: str) -> str:
    without_parentheses = re.sub(r"\([^)]*\)", " ", program)
    lines = []
    for line in without_parentheses.splitlines():
        line = line.split(";", 1)[0]
        lines.append(line)
    return "\n".join(lines).upper()


def analyze_gcode(program: str, controller_name: str = "") -> list[CheckFinding]:
    code = _strip_comments(program)
    findings: list[CheckFinding] = []
    controller = controller_name.upper()

    if not code.strip():
        return [CheckFinding("error", "Пустая программа", "В сообщении нет анализируемого G-кода.")]

    if re.search(r"\bG96\b", code):
        has_limit = bool(re.search(r"\bLIMS\s*=", code)) if "SINUMERIK" in controller else bool(re.search(r"\bG50\s+S\d+", code))
        if not has_limit:
            expected = "LIMS=..." if "SINUMERIK" in controller else "G50 S..."
            findings.append(CheckFinding(
                "error",
                "Нет ограничения оборотов при G96",
                f"Перед G96 задайте безопасный предел оборотов ({expected}) по паспорту станка.",
            ))

    if not re.search(r"\bM0?3\b|\bM0?4\b", code):
        findings.append(CheckFinding("warning", "Не найден запуск шпинделя", "Проверьте наличие M3/M4 и команды скорости S."))

    if re.search(r"\bM0?3\b|\bM0?4\b", code) and not re.search(r"\bS\s*\d+", code):
        findings.append(CheckFinding("warning", "Не найдена скорость шпинделя", "Есть M3/M4, но не обнаружено числовое S."))

    if not re.search(r"\bT\s*\d+", code):
        findings.append(CheckFinding("warning", "Не найден вызов инструмента", "Проверьте T-команду и корректоры инструмента."))

    if not re.search(r"\bG54\b|\bG55\b|\bG56\b|\bG57\b|\bG58\b|\bG59\b", code):
        findings.append(CheckFinding("warning", "Не найдена рабочая система координат", "Проверьте G54–G59 или эквивалент стойки."))

    if re.search(r"\bG41\b|\bG42\b", code) and not re.search(r"\bG40\b", code):
        findings.append(CheckFinding("error", "Коррекция радиуса не отменена", "После G41/G42 не найден G40."))

    if re.search(r"\bG8[1-9]\b", code) and not re.search(r"\bG80\b", code):
        findings.append(CheckFinding("warning", "Цикл сверления может остаться активным", "После G81–G89 не найден G80."))

    if not re.search(r"\bM0?5\b", code):
        findings.append(CheckFinding("warning", "Не найден останов шпинделя", "Перед завершением программы обычно нужен M5."))

    if not re.search(r"\bM30\b|\bM02\b|\bM2\b", code):
        findings.append(CheckFinding("warning", "Не найден конец программы", "Проверьте M30/M2 или эквивалент стойки."))

    if re.search(r"\bG0\b[^\n]*(?:X\s*0(?:\.0+)?\b|Z\s*-\d)", code):
        findings.append(CheckFinding(
            "warning",
            "Потенциально опасный ускоренный ход",
            "Обнаружен G0 к центру X0 или в отрицательный Z. Проверьте траекторию в графике.",
        ))

    if not findings:
        findings.append(CheckFinding(
            "ok",
            "Явных типовых ошибок не найдено",
            "Это не доказывает безопасность программы: выполните графику, Single Block и холостой прогон.",
        ))
    return findings


def diagnose_alarm(text: str, controller_name: str = "") -> str:
    query = text.strip().lower()
    controller = controller_name or "выбранной стойки"

    categories = [
        (("emergency", "аварийн", "e-stop", "стоп"), "Цепь аварийного останова", "Проверьте кнопки E-STOP, двери, внешние блокировки и цепь безопасности."),
        (("encoder", "энкод", "датчик положения"), "Обратная связь оси/шпинделя", "Не перемещайте ось вслепую. Проверьте кабель, разъёмы, питание датчика и механическое заклинивание."),
        (("overheat", "перегрев", "temperature"), "Перегрев", "Остановите нагрузку, проверьте вентиляторы, фильтры, охлаждение шкафа и температуру двигателя/шпинделя."),
        (("pressure", "давлен", "гидрав"), "Давление гидравлики/пневматики", "Проверьте уровень масла, насос, фильтр, датчик давления и утечки."),
        (("spindle", "шпиндел"), "Шпиндель", "Проверьте зажим, привод, частотник, ориентацию, датчик и отсутствие механического заклинивания."),
        (("axis", "ось", "servo", "привод"), "Сервопривод оси", "Проверьте, какая ось указана, не упёрлась ли она в предел, и нет ли механической перегрузки."),
        (("door", "двер"), "Блокировка двери", "Проверьте закрытие двери, замок, концевик и разрешение режима наладки."),
    ]

    for keys, title, advice in categories:
        if any(key in query for key in keys):
            return (
                f"Категория: {title}.\n"
                f"Стойка: {controller}.\n\n"
                f"Что проверить сначала:\n• {advice}\n"
                "• Запишите полный номер и дословный текст сообщения.\n"
                "• Не сбрасывайте аварию многократно, если причина не устранена."
            )

    number = re.search(r"\b\d{3,8}\b", query)
    prefix = f"Получен номер {number.group(0)}. " if number else ""
    return (
        f"{prefix}Без полного текста и OEM-документации точную расшифровку гарантировать нельзя.\n"
        f"Стойка: {controller}.\n\n"
        "Пришлите номер вместе с текстом с экрана и укажите, после какого действия появилась ошибка."
    )
