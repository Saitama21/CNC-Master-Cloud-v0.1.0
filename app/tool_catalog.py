from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from app.cnc_logic import OPERATION_LABELS, normalize_axes


ISO_LABELS = {
    "P": "сталь",
    "M": "нержавеющая сталь",
    "K": "чугун",
    "N": "алюминий / цветные / полимеры",
    "S": "жаропрочные сплавы / титан",
    "H": "закалённые материалы",
}


@dataclass(frozen=True)
class ToolSelection:
    title: str
    holder: str
    cutting_part: str
    geometry: str
    cutting_data: str
    setup: tuple[str, ...]
    alternatives: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


_HOLDER_LENGTH = {16: "H", 20: "K", 25: "M", 32: "P", 40: "R"}
_BORING_BAR_CODE = {
    8: "S08H-SCLCR06",
    10: "S10K-SCLCR06",
    12: "S12M-SCLCR06",
    16: "S16Q-SCLCR09",
    20: "S20R-SCLCR09",
    25: "S25S-SCLCR09",
    32: "S32T-SCLCR12",
}
_STANDARD_SHANKS = (16, 20, 25, 32, 40)
_STANDARD_BARS = (8, 10, 12, 16, 20, 25, 32)


def tool_material_keyboard_rows() -> list[tuple[str, str]]:
    return [
        ("ISO P — стали", "P"),
        ("ISO M — нержавейка", "M"),
        ("ISO K — чугун", "K"),
        ("ISO N — алюминий / цветные / пластик", "N"),
        ("ISO S — титан / жаропрочные", "S"),
        ("ISO H — закалённые", "H"),
    ]


def tool_parameter_prompt(operation: str) -> str:
    prompts = {
        "turn_rough": (
            "Введите: <code>диаметр_детали глубина_резания размер_державки</code>\n"
            "Пример: <code>100 2.0 25</code>"
        ),
        "turn_finish": (
            "Введите: <code>диаметр_детали припуск_на_радиус размер_державки</code>\n"
            "Пример: <code>100 0.4 25</code>"
        ),
        "face": (
            "Введите: <code>наружный_диаметр глубина_прохода размер_державки</code>\n"
            "Пример: <code>185 1.0 25</code>"
        ),
        "bore": (
            "Введите: <code>диаметр_отверстия глубина_расточки диаметр_расточной_державки</code>\n"
            "Пример: <code>90 45 25</code>"
        ),
        "groove": (
            "Введите: <code>ширина_канавки глубина размер_державки</code>\n"
            "Пример: <code>3 8 25</code>"
        ),
        "thread": (
            "Введите: <code>диаметр шаг размер_державки тип</code>\n"
            "Тип: <code>ext</code> — наружная, <code>int</code> — внутренняя.\n"
            "Пример: <code>16 1.5 25 ext</code>"
        ),
        "drill": (
            "Введите: <code>диаметр_сверла глубина_отверстия</code>\n"
            "Пример: <code>14.8 30</code>"
        ),
        "mill": (
            "Введите: <code>диаметр_фрезы глубина_резания число_зубьев</code>\n"
            "Пример: <code>10 3 4</code>"
        ),
    }
    return prompts.get(operation, "Введите параметры операции числами через пробел.") + "\n\nДля отмены: /cancel"


def _numbers(text: str) -> list[float]:
    values = re.findall(r"[-+]?\d+(?:[.,]\d+)?", text)
    return [float(item.replace(",", ".")) for item in values]


def _nearest_standard(value: float, standards: tuple[int, ...]) -> int:
    return min(standards, key=lambda item: abs(item - value))


def _holder_code(prefix: str, shank: int, insert_size: str) -> str:
    length = _HOLDER_LENGTH.get(shank, "M")
    return f"{prefix} {shank}{shank}{length}{insert_size}"


def _rpm_range(diameter_mm: float, vc_min: float, vc_max: float) -> tuple[int, int]:
    low = round(1000.0 * vc_min / (math.pi * diameter_mm))
    high = round(1000.0 * vc_max / (math.pi * diameter_mm))
    return low, high


def _turning_ranges(iso_group: str, finish: bool = False) -> tuple[float, float, float, float, float, float]:
    rough = {
        "P": (160, 230, 0.20, 0.38, 1.5, 4.0),
        "M": (110, 170, 0.18, 0.32, 1.2, 3.5),
        "K": (170, 250, 0.20, 0.40, 1.5, 4.0),
        "N": (250, 550, 0.18, 0.40, 1.0, 4.0),
        "S": (35, 75, 0.12, 0.25, 0.8, 2.5),
        "H": (70, 140, 0.08, 0.20, 0.2, 1.0),
    }
    finishing = {
        "P": (190, 280, 0.08, 0.18, 0.2, 0.8),
        "M": (130, 200, 0.08, 0.16, 0.2, 0.7),
        "K": (200, 300, 0.08, 0.20, 0.2, 0.8),
        "N": (350, 700, 0.06, 0.20, 0.1, 0.8),
        "S": (45, 90, 0.06, 0.14, 0.15, 0.6),
        "H": (90, 180, 0.04, 0.12, 0.1, 0.4),
    }
    return (finishing if finish else rough).get(iso_group, rough["P"])


def _chipbreaker(iso_group: str, finish: bool) -> str:
    if iso_group == "M":
        return "острая положительная геометрия M-F/M-M; не допускать трения и наклёпа"
    if iso_group == "N":
        return "полированная острая геометрия N, большой положительный передний угол"
    if iso_group == "S":
        return "вязкая PVD-марка, острая кромка, стабильная подача и обильная СОЖ"
    if iso_group == "H":
        return "специализированный твёрдый сплав/CBN по фактической твёрдости"
    return "геометрия F для чистовой или M/R для получистовой/черновой обработки" if finish else "прочная геометрия M/R со стабильным стружколоманием"


def _machine_warning(operation: str, machine: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    axes = normalize_axes(machine.get("axes"))
    machine_type = machine.get("machine_type") or "other"
    if operation == "mill":
        if "C" not in axes:
            warnings.append("В профиле не указана ось C: позиционное фрезерование может быть недоступно.")
        if machine_type != "multitasking" and not machine.get("driven_tools"):
            warnings.append("В профиле не подтверждён приводной инструмент. Проверьте револьвер и приводной блок.")
    if operation in {"turn_rough", "turn_finish", "face", "bore", "groove", "thread"} and not {"X", "Z"}.issubset(axes):
        warnings.append("В профиле не указаны X/Z; совместимость с токарной операцией не подтверждена.")
    return warnings


def select_tool(operation: str, iso_group: str, raw_parameters: str, machine: dict[str, Any]) -> ToolSelection:
    iso_group = (iso_group or "P").upper()
    if iso_group not in ISO_LABELS:
        iso_group = "P"
    nums = _numbers(raw_parameters)
    warnings = _machine_warning(operation, machine)

    if operation in {"turn_rough", "turn_finish", "face"}:
        if len(nums) < 3:
            raise ValueError("Нужно 3 числа: диаметр, глубина/припуск и размер державки.")
        diameter, requested_ap, shank_raw = nums[:3]
        if min(diameter, requested_ap, shank_raw) <= 0:
            raise ValueError("Все размеры должны быть больше нуля.")
        shank = _nearest_standard(shank_raw, _STANDARD_SHANKS)
        if abs(shank - shank_raw) > 0.1:
            warnings.append(f"Размер {shank_raw:g} мм не стандартный; показан ближайший вариант {shank}×{shank} мм.")
        finish = operation == "turn_finish"
        vc_min, vc_max, f_min, f_max, ap_min, ap_max = _turning_ranges(iso_group, finish=finish)
        rpm_min, rpm_max = _rpm_range(diameter, vc_min, vc_max)
        if requested_ap > ap_max:
            warnings.append(f"Указанная глубина {requested_ap:g} мм выше стартового диапазона {ap_min:g}–{ap_max:g} мм.")
        if operation == "turn_finish":
            holder = _holder_code("SCLCR", shank, "09")
            cutting = "CCMT 09T304 (rε 0,4); для профилирования — DCMT 11T304"
            alternatives = (_holder_code("SDJCR", shank, "11") + " + DCMT 11T304",)
            title = "Чистовой токарный комплект"
        else:
            holder = _holder_code("PCLNR", shank, "12")
            cutting = "CNMG 120408 (rε 0,8)"
            alternatives = (_holder_code("MWLNR", shank, "08") + " + WNMG 080408",)
            title = "Торцевой комплект" if operation == "face" else "Черновой токарный комплект"
        if operation == "face":
            warnings.append("При торцевании через центр уменьшайте скорость в зоне X≈0 и проверяйте направление вершины пластины.")
        return ToolSelection(
            title=title,
            holder=holder,
            cutting_part=cutting,
            geometry=_chipbreaker(iso_group, finish),
            cutting_data=(
                f"Старт: Vc {vc_min:g}–{vc_max:g} м/мин; f {f_min:g}–{f_max:g} мм/об; "
                f"ap {ap_min:g}–{ap_max:g} мм. Для Ø{diameter:g}: примерно {rpm_min}–{rpm_max} об/мин."
            ),
            setup=(
                f"Посадка державки: {shank}×{shank} мм — обязательно сверить с револьвером.",
                "Вылет минимальный; вершина строго по центру шпинделя.",
                "Для SINUMERIK при G96 задайте безопасный LIMS по паспорту станка.",
            ),
            alternatives=alternatives,
            warnings=tuple(warnings),
        )

    if operation == "bore":
        if len(nums) < 2:
            raise ValueError("Нужно минимум 2 числа: диаметр отверстия и глубина расточки.")
        hole_d, depth = nums[:2]
        if min(hole_d, depth) <= 0:
            raise ValueError("Диаметр и глубина должны быть больше нуля.")
        if len(nums) >= 3:
            bar = _nearest_standard(nums[2], _STANDARD_BARS)
        else:
            available = [item for item in _STANDARD_BARS if item <= hole_d * 0.55]
            bar = max(available or [8])
            warnings.append(f"Диаметр расточной державки не указан; предварительно выбран Ø{bar} мм.")
        if bar >= hole_d * 0.75:
            warnings.append("Державка занимает большую часть отверстия: проверьте проход корпуса, винта и отвод стружки.")
        ratio = depth / bar
        if ratio > 4:
            warnings.append(f"Вылет ≈{ratio:.1f}D. Для стальной державки это зона повышенного риска вибраций; рассмотрите твердосплавную/демпфированную.")
        code = _BORING_BAR_CODE[bar]
        insert = "CCMT 09T304" if bar >= 16 else "CCMT 060204"
        vc_min, vc_max, f_min, f_max, ap_min, ap_max = _turning_ranges(iso_group, finish=True)
        vc_min *= 0.8
        vc_max *= 0.9
        rpm_min, rpm_max = _rpm_range(hole_d, vc_min, vc_max)
        return ToolSelection(
            title="Расточной комплект",
            holder=code,
            cutting_part=f"{insert}; rε 0,2–0,4 мм",
            geometry=_chipbreaker(iso_group, True),
            cutting_data=(
                f"Старт: Vc {vc_min:.0f}–{vc_max:.0f} м/мин; f {f_min:g}–{f_max:g} мм/об; "
                f"ap {ap_min:g}–{ap_max:g} мм. Для Ø{hole_d:g}: примерно {rpm_min}–{rpm_max} об/мин."
            ),
            setup=(
                f"Державка Ø{bar} мм, глубина {depth:g} мм, отношение вылета ≈{ratio:.1f}D.",
                "Выбирать максимально толстую державку, которая проходит в отверстие, и минимальный вылет.",
                "Проверить направление отвода стружки и подачу СОЖ внутрь отверстия.",
            ),
            alternatives=("Для вибраций: твердосплавная или демпфированная расточная державка того же посадочного семейства.",),
            warnings=tuple(warnings),
        )

    if operation == "groove":
        if len(nums) < 3:
            raise ValueError("Нужно 3 числа: ширина, глубина и размер державки.")
        width, depth, shank_raw = nums[:3]
        if min(width, depth, shank_raw) <= 0:
            raise ValueError("Все размеры должны быть больше нуля.")
        shank = _nearest_standard(shank_raw, _STANDARD_SHANKS)
        standard_widths = (1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0)
        blade = min(standard_widths, key=lambda item: abs(item - width))
        if abs(blade - width) > 0.05:
            warnings.append(f"Для ширины {width:g} мм выбран ближайший стандарт {blade:g} мм; точный профиль требует проверки.")
        insert_code = f"MGMN{int(round(blade * 100)):03d}"
        vc_by_iso = {"P": (100, 170), "M": (70, 120), "K": (100, 170), "N": (180, 350), "S": (25, 55), "H": (50, 100)}
        vc_min, vc_max = vc_by_iso[iso_group]
        return ToolSelection(
            title="Канавочный / отрезной комплект",
            holder=f"MGEHR {shank}{shank}-{blade:g}",
            cutting_part=f"{insert_code}, ширина {blade:g} мм",
            geometry=_chipbreaker(iso_group, False),
            cutting_data=f"Старт: Vc {vc_min}–{vc_max} м/мин; f 0,05–0,14 мм/об. Глубину {depth:g} мм выполнять без остановки в резе.",
            setup=(
                "Лезвие выставить строго перпендикулярно оси и точно по центру.",
                "Минимальный вылет; проверить боковой зазор корпуса на полной глубине.",
                "СОЖ направить в зону режущей кромки; для отрезки предпочтительна внутренняя подача.",
            ),
            alternatives=("Для глубокой отрезки использовать усиленный лезвийный блок соответствующей глубины реза.",),
            warnings=tuple(warnings),
        )

    if operation == "thread":
        if len(nums) < 3:
            raise ValueError("Нужно минимум 3 числа: диаметр, шаг и размер державки; затем ext или int.")
        diameter, pitch, shank_raw = nums[:3]
        if min(diameter, pitch, shank_raw) <= 0:
            raise ValueError("Диаметр, шаг и размер должны быть больше нуля.")
        mode = "int" if re.search(r"\b(int|внутр)", raw_parameters.lower()) else "ext"
        shank = _nearest_standard(shank_raw, _STANDARD_SHANKS)
        length = _HOLDER_LENGTH.get(shank, "M")
        if mode == "ext":
            holder = f"SER {shank}{shank}{length}16"
            insert = f"16ER {pitch:g}ISO (полный профиль)"
        else:
            bar = _nearest_standard(shank_raw, _STANDARD_BARS)
            holder = f"S{bar}R-SIR16"
            insert = f"16IR {pitch:g}ISO (полный профиль)"
        vc_by_iso = {"P": (70, 140), "M": (45, 90), "K": (60, 120), "N": (120, 250), "S": (20, 45), "H": (35, 70)}
        vc_min, vc_max = vc_by_iso[iso_group]
        rpm_min, rpm_max = _rpm_range(diameter, vc_min, vc_max)
        return ToolSelection(
            title="Резьбовой комплект",
            holder=holder,
            cutting_part=insert,
            geometry="Полный профиль ISO 60° под точный шаг; AG60 — только как универсальная альтернатива.",
            cutting_data=f"Старт: Vc {vc_min}–{vc_max} м/мин; для Ø{diameter:g}: примерно {rpm_min}–{rpm_max} об/мин. Подача = шаг {pitch:g} мм/об.",
            setup=(
                "Пластину выставить шаблоном строго по оси детали.",
                "Сверить направление резьбы, заход, сбег и цикл именно для выбранной стойки.",
                "Первые детали выполнять в Single Block с уменьшенным override.",
            ),
            alternatives=("16ER/IR AG60 — для разных шагов, но вершина профиля формируется не полностью.",),
            warnings=tuple(warnings),
        )

    if operation == "drill":
        if len(nums) < 2:
            raise ValueError("Нужно 2 числа: диаметр сверла и глубина отверстия.")
        diameter, depth = nums[:2]
        if min(diameter, depth) <= 0:
            raise ValueError("Диаметр и глубина должны быть больше нуля.")
        depth_ratio = depth / diameter
        if diameter <= 20 and depth_ratio <= 5:
            tool = f"Твердосплавное сверло Ø{diameter:g}, длина {3 if depth_ratio <= 3 else 5}×D, желательно с внутренней СОЖ"
            alternative = "Для нестабильного станка: короткое HSS-Co сверло после центровки, но с меньшей производительностью."
        elif 14 <= diameter <= 50 and depth_ratio <= 4:
            tool = f"Корпусное U-сверло Ø{diameter:g}, длина до {math.ceil(depth_ratio)}×D, с внутренней СОЖ"
            alternative = "Твердосплавное сверло точного диаметра даст лучшую геометрию отверстия при достаточной жёсткости."
        else:
            tool = f"Сверло Ø{diameter:g} специальной длины; для {depth_ratio:.1f}D нужен цикл отвода стружки и стабильная СОЖ"
            alternative = "Пилотное сверло + длинное сверло того же семейства, если это разрешает изготовитель."
        flute = "2 канавки, полированная режущая часть" if iso_group == "N" else "2 канавки, геометрия по ISO-группе"
        vc_by_iso = {"P": (70, 130), "M": (45, 90), "K": (80, 140), "N": (150, 350), "S": (20, 45), "H": (30, 70)}
        vc_min, vc_max = vc_by_iso[iso_group]
        rpm_min, rpm_max = _rpm_range(diameter, vc_min, vc_max)
        feed = max(0.04, min(0.30, 0.012 * diameter))
        if depth_ratio > 5:
            warnings.append(f"Глубина {depth_ratio:.1f}D: стандартный короткий инструмент не подходит без специальной стратегии.")
        return ToolSelection(
            title="Сверлильный комплект",
            holder="Цанговый/гидропластичный патрон или штатный приводной блок с минимальным биением",
            cutting_part=tool,
            geometry=flute,
            cutting_data=f"Старт: Vc {vc_min}–{vc_max} м/мин; примерно {rpm_min}–{rpm_max} об/мин; подача около {feed:.2f} мм/об с корректировкой по каталогу.",
            setup=(
                f"Глубина {depth:g} мм = {depth_ratio:.1f}D.",
                "Проверить биение, длину зажима и давление СОЖ до запуска.",
                "Для глухого отверстия учитывать длину вершины сверла и безопасный недоход.",
            ),
            alternatives=(alternative,),
            warnings=tuple(warnings),
        )

    if operation == "mill":
        if len(nums) < 2:
            raise ValueError("Нужно минимум 2 числа: диаметр фрезы и глубина; число зубьев можно указать третьим.")
        diameter, depth = nums[:2]
        teeth = int(round(nums[2])) if len(nums) >= 3 else (3 if iso_group == "N" else 4)
        if min(diameter, depth, teeth) <= 0:
            raise ValueError("Диаметр, глубина и число зубьев должны быть больше нуля.")
        if iso_group == "N":
            cutter = f"Твердосплавная концевая фреза Ø{diameter:g}, {teeth} зуба, полированные канавки"
            geometry = "Большой положительный угол, 2–3 канавки и свободный отвод стружки."
        elif iso_group == "M":
            cutter = f"Твердосплавная концевая фреза Ø{diameter:g}, {teeth} зуба, неравномерный шаг/спираль"
            geometry = "Острая PVD-геометрия для нержавейки; предпочтительна трохоидальная/стабильная дуговая подача."
        else:
            cutter = f"Твердосплавная концевая фреза Ø{diameter:g}, {teeth} зуба"
            geometry = "Геометрия и покрытие по ISO-группе материала."
        vc_by_iso = {"P": (100, 180), "M": (70, 130), "K": (120, 220), "N": (250, 600), "S": (25, 60), "H": (50, 110)}
        vc_min, vc_max = vc_by_iso[iso_group]
        rpm_min, rpm_max = _rpm_range(diameter, vc_min, vc_max)
        fz_by_iso = {"P": (0.03, 0.08), "M": (0.025, 0.06), "K": (0.04, 0.10), "N": (0.04, 0.12), "S": (0.015, 0.04), "H": (0.015, 0.04)}
        fz_min, fz_max = fz_by_iso[iso_group]
        feed_min = round(rpm_min * teeth * fz_min)
        feed_max = round(rpm_max * teeth * fz_max)
        if depth > diameter:
            warnings.append("Осевая глубина больше диаметра фрезы: проверьте вылет, мощность приводного блока и стратегию обработки.")
        return ToolSelection(
            title="Фрезерный комплект для приводного инструмента",
            holder="Приводной блок + ER-цанга/гидропатрон, соответствующие хвостовику фрезы",
            cutting_part=cutter,
            geometry=geometry,
            cutting_data=(
                f"Старт: Vc {vc_min}–{vc_max} м/мин; fz {fz_min:g}–{fz_max:g} мм/зуб; "
                f"примерно {rpm_min}–{rpm_max} об/мин и {feed_min}–{feed_max} мм/мин."
            ),
            setup=(
                f"Осевая глубина {depth:g} мм; начать с малого радиального зацепления и контролировать нагрузку.",
                "Проверить фиксацию/интерполяцию оси C, ориентацию приводного блока и допустимые обороты.",
                "Вылет фрезы минимальный; биение на режущей части желательно ≤0,01 мм.",
            ),
            alternatives=("Для плоскости большой ширины — малодиаметровая корпусная фреза, если мощность приводного блока достаточна.",),
            warnings=tuple(warnings),
        )

    raise ValueError(f"Операция {OPERATION_LABELS.get(operation, operation)} пока не поддерживается.")


def format_tool_selection(selection: ToolSelection, operation: str, material_name: str, iso_group: str) -> str:
    parts = [
        f"<b>🔩 {selection.title}</b>",
        "",
        f"Операция: <b>{OPERATION_LABELS.get(operation, operation)}</b>",
        f"Материал: <b>{material_name}</b> (ISO {iso_group})",
        "",
        f"<b>Державка / патрон</b>\n<code>{selection.holder}</code>",
        f"<b>Пластина / режущая часть</b>\n<code>{selection.cutting_part}</code>",
        f"<b>Геометрия</b>\n{selection.geometry}",
        f"<b>Стартовые режимы</b>\n{selection.cutting_data}",
        "<b>Установка и проверка</b>",
    ]
    parts.extend(f"• {item}" for item in selection.setup)
    if selection.alternatives:
        parts.append("<b>Альтернативы</b>")
        parts.extend(f"• {item}" for item in selection.alternatives)
    if selection.warnings:
        parts.append("<b>⚠️ Важные замечания</b>")
        parts.extend(f"• {item}" for item in selection.warnings)
    parts.extend([
        "",
        "⚠️ Перед запуском сверьте посадку державки, допустимые обороты приводного блока и каталог конкретного производителя. Первый запуск — графика, Single Block и сниженный override.",
    ])
    return "\n".join(parts)
