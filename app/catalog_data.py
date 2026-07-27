from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Iterable


@dataclass(frozen=True)
class CatalogItem:
    key: str
    category: str
    subcategory: str
    name: str
    code: str
    operation_tags: tuple[str, ...]
    iso_groups: tuple[str, ...]
    dimensions: str
    description: str
    compatibility: str
    grade_hint: str
    source: str = "Стандартное семейство ISO/DIN; точный SKU сверять с каталогом производителя"

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["operation_tags"] = list(self.operation_tags)
        payload["iso_groups"] = list(self.iso_groups)
        return payload


CATEGORY_LABELS = {
    "turn_holder": "Токарные державки",
    "boring_bar": "Расточные державки",
    "turn_insert": "Токарные пластины",
    "groove": "Канавки и отрезка",
    "thread": "Резьбовой инструмент",
    "drill": "Сверла",
    "mill": "Фрезы",
    "holder": "Патроны и оснастка",
}

ISO_ALL = ("P", "M", "K", "N", "S", "H")


def _add(items: list[CatalogItem], **kwargs) -> None:
    items.append(CatalogItem(**kwargs))


def _turning_holders(items: list[CatalogItem]) -> None:
    families = [
        ("PCLNR", "CNMG", "Черновое/получистовое наружное точение", ("turn_rough", "face")),
        ("PCLNL", "CNMG", "Левое исполнение для наружного точения", ("turn_rough", "face")),
        ("MCLNR", "CNMG", "Универсальное наружное точение с отрицательной пластиной", ("turn_rough", "face")),
        ("DCLNR", "CNMG", "Профильное наружное точение", ("turn_rough", "turn_finish")),
        ("MWLNR", "WNMG", "Черновая обработка пластиной WNMG", ("turn_rough", "face")),
        ("PDJNR", "DNMG", "Профилирование и чистовое точение", ("turn_finish", "face")),
        ("MTJNR", "TNMG", "Универсальное точение пластиной TNMG", ("turn_rough", "turn_finish")),
        ("MVJNR", "VNMG", "Контурное и чистовое точение", ("turn_finish",)),
        ("PSBNR", "SNMG", "Жёсткая черновая обработка", ("turn_rough", "face")),
        ("PTGNR", "TNMG", "Торцевание и продольное точение", ("turn_rough", "face")),
        ("SCLCR", "CCMT", "Положительная пластина для чистового точения", ("turn_finish", "face")),
        ("SCLCL", "CCMT", "Левое исполнение с положительной пластиной", ("turn_finish", "face")),
        ("SDJCR", "DCMT", "Чистовое профилирование", ("turn_finish",)),
        ("SVJCR", "VCMT/VBMT", "Тонкое контурное точение", ("turn_finish",)),
        ("STGCR", "TCMT", "Лёгкое точение и фаски", ("turn_finish", "face")),
    ]
    sizes = [(16, "H"), (20, "K"), (25, "M"), (32, "P")]
    insert_size = {
        "CNMG": "12", "WNMG": "08", "DNMG": "15", "TNMG": "16", "VNMG": "16",
        "SNMG": "12", "CCMT": "09", "DCMT": "11", "VCMT/VBMT": "16", "TCMT": "16",
    }
    counter = 1
    for family, insert, desc, tags in families:
        for shank, length in sizes:
            code = f"{family} {shank}{shank}{length}{insert_size[insert]}"
            _add(
                items,
                key=f"TH{counter:04d}", category="turn_holder", subcategory=family,
                name=f"Державка {family} {shank}×{shank}", code=code,
                operation_tags=tags, iso_groups=ISO_ALL,
                dimensions=f"Хвостовик {shank}×{shank} мм",
                description=desc,
                compatibility=f"Пластины семейства {insert}; правое/левое исполнение проверять по коду",
                grade_hint="Жёсткость, высоту центра и направление подачи сверить на станке",
            )
            counter += 1


def _boring_bars(items: list[CatalogItem]) -> None:
    bars = [
        (8, "H", "SCLCR06", "CCMT 0602"), (10, "K", "SCLCR06", "CCMT 0602"),
        (12, "M", "SCLCR06", "CCMT 0602"), (16, "Q", "SCLCR09", "CCMT 09T3"),
        (20, "R", "SCLCR09", "CCMT 09T3"), (25, "S", "SCLCR09", "CCMT 09T3"),
        (32, "T", "SCLCR12", "CCMT 1204"),
    ]
    families = [
        ("S", "Стальная расточная державка", "до 3–4D"),
        ("A", "Твердосплавная расточная державка", "до 5–6D"),
    ]
    counter = 1
    for prefix, label, reach in families:
        for diameter, length, tail, insert in bars:
            code = f"{prefix}{diameter:02d}{length}-{tail}"
            _add(
                items,
                key=f"BB{counter:04d}", category="boring_bar", subcategory=prefix,
                name=f"{label} Ø{diameter}", code=code,
                operation_tags=("bore",), iso_groups=ISO_ALL,
                dimensions=f"Диаметр хвостовика Ø{diameter} мм; рекомендуемый вылет {reach}",
                description="Внутреннее точение, расточка и чистовая обработка отверстий",
                compatibility=f"Пластина {insert}",
                grade_hint="Выбирать максимально толстую державку, проходящую в отверстие",
            )
            counter += 1


def _turning_inserts(items: list[CatalogItem]) -> None:
    negative = {
        "CNMG": ["120404", "120408", "120412"],
        "WNMG": ["080404", "080408"],
        "DNMG": ["150404", "150408"],
        "TNMG": ["160404", "160408"],
        "VNMG": ["160404", "160408"],
        "SNMG": ["120404", "120408"],
    }
    positive = {
        "CCMT": ["060202", "060204", "09T302", "09T304", "09T308"],
        "DCMT": ["070202", "070204", "11T302", "11T304"],
        "TCMT": ["110202", "110204", "16T304"],
        "VBMT": ["110202", "160404"],
        "VCMT": ["110304", "160404"],
        "RCMT": ["0803", "1003", "1204"],
        "SCMT": ["09T304", "120408"],
    }
    geos = [
        ("F", ("turn_finish", "face"), "Чистовая геометрия, малая подача"),
        ("M", ("turn_rough", "turn_finish", "face", "bore"), "Получистовая универсальная геометрия"),
        ("R", ("turn_rough", "face"), "Прочная черновая геометрия"),
    ]
    counter = 1
    for family_map, polarity in ((negative, "отрицательная"), (positive, "положительная")):
        for family, sizes in family_map.items():
            for size in sizes:
                for geo, tags, geo_desc in geos:
                    for group in ISO_ALL:
                        code = f"{family} {size}-{geo}{group}"
                        _add(
                            items,
                            key=f"TI{counter:05d}", category="turn_insert", subcategory=family,
                            name=f"Пластина {family} {size} ISO {group}", code=code,
                            operation_tags=tags, iso_groups=(group,),
                            dimensions=f"Типоразмер {size}; геометрия {geo}",
                            description=f"{polarity.capitalize()} сменная пластина. {geo_desc}",
                            compatibility=f"Державка под {family}",
                            grade_hint=f"Марку сплава/покрытие выбирать у производителя для ISO {group}",
                        )
                        counter += 1


def _grooving(items: list[CatalogItem]) -> None:
    widths = (1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0)
    counter = 1
    for shank in (16, 20, 25, 32):
        for width in widths:
            code = f"MGEHR {shank}{shank}-{width:g}"
            _add(
                items,
                key=f"GR{counter:04d}", category="groove", subcategory="holder",
                name=f"Канавочная державка {shank}×{shank}, {width:g} мм", code=code,
                operation_tags=("groove",), iso_groups=ISO_ALL,
                dimensions=f"Хвостовик {shank}×{shank}; ширина пластины {width:g} мм",
                description="Наружные канавки и отрезка",
                compatibility=f"MGMN{int(round(width * 100)):03d}",
                grade_hint="Глубину реза корпуса сверять по каталогу",
            )
            counter += 1
    for family in ("MGMN", "GTN", "DGN"):
        for width in widths:
            code = f"{family}{int(round(width * 100)):03d}"
            _add(
                items,
                key=f"GI{counter:04d}", category="groove", subcategory="insert",
                name=f"Канавочная пластина {family} {width:g} мм", code=code,
                operation_tags=("groove",), iso_groups=ISO_ALL,
                dimensions=f"Ширина {width:g} мм",
                description="Сменная пластина для канавки/отрезки",
                compatibility=f"Державка семейства {family}/совместимый блок",
                grade_hint="Стружколом и покрытие под ISO-группу материала",
            )
            counter += 1


def _threading(items: list[CatalogItem]) -> None:
    pitches = (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0)
    counter = 1
    for shank, length in ((16, "H"), (20, "K"), (25, "M"), (32, "P")):
        for side in ("ER", "EL"):
            _add(
                items,
                key=f"TR{counter:04d}", category="thread", subcategory="holder_ext",
                name=f"Наружная резьбовая державка {side} {shank}×{shank}",
                code=f"S{side} {shank}{shank}{length}16",
                operation_tags=("thread",), iso_groups=ISO_ALL,
                dimensions=f"Хвостовик {shank}×{shank}; пластина 16{side}",
                description="Наружная резьба правого/левого исполнения",
                compatibility=f"16{side} ISO/AG60/UN",
                grade_hint="Проверить направление резьбы и подачу к патрону/от патрона",
            )
            counter += 1
    for bar in (12, 16, 20, 25, 32):
        _add(
            items,
            key=f"TR{counter:04d}", category="thread", subcategory="holder_int",
            name=f"Внутренняя резьбовая державка Ø{bar}", code=f"S{bar}R-SIR16",
            operation_tags=("thread",), iso_groups=ISO_ALL,
            dimensions=f"Хвостовик Ø{bar}; пластина 16IR",
            description="Внутренняя метрическая/дюймовая резьба",
            compatibility="16IR ISO/AG60/UN",
            grade_hint="Минимальный диаметр отверстия сверять по корпусу и пластине",
        )
        counter += 1
    for mode in ("ER", "IR"):
        for pitch in pitches:
            for profile in ("ISO", "AG60"):
                code = f"16{mode} {pitch:g}{profile}"
                _add(
                    items,
                    key=f"TP{counter:05d}", category="thread", subcategory="insert",
                    name=f"Резьбовая пластина 16{mode}, шаг {pitch:g}", code=code,
                    operation_tags=("thread",), iso_groups=ISO_ALL,
                    dimensions=f"Профиль 60°; шаг {pitch:g} мм",
                    description="Полный профиль ISO или универсальный частичный профиль AG60",
                    compatibility=f"Державка под 16{mode}",
                    grade_hint="Полный профиль предпочтителен для серийной обработки одного шага",
                )
                counter += 1


def _drills(items: list[CatalogItem]) -> None:
    counter = 1
    diameters_half = [x / 2 for x in range(2, 41)]
    for diameter in diameters_half:
        _add(
            items,
            key=f"DR{counter:05d}", category="drill", subcategory="hss",
            name=f"Спиральное сверло HSS Ø{diameter:g}", code=f"DIN338-HSS-{diameter:g}",
            operation_tags=("drill",), iso_groups=("P", "M", "K", "N"),
            dimensions=f"Ø{diameter:g} мм; стандартная длина",
            description="Универсальное спиральное сверло HSS",
            compatibility="Цанговый/сверлильный патрон",
            grade_hint="Для нержавейки предпочтительно HSS-Co и стабильная подача",
        )
        counter += 1
    for diameter in range(3, 21):
        for length_d in (3, 5, 8):
            _add(
                items,
                key=f"DR{counter:05d}", category="drill", subcategory="carbide",
                name=f"Твердосплавное сверло Ø{diameter}, {length_d}D",
                code=f"CARBIDE-{diameter}-{length_d}D",
                operation_tags=("drill",), iso_groups=("P", "M", "K", "N", "S"),
                dimensions=f"Ø{diameter} мм; рабочая длина {length_d}D",
                description="Монолитное твердосплавное сверло; вариант с внутренней СОЖ предпочтителен",
                compatibility="Гидропатрон/термопатрон/высокоточная цанга",
                grade_hint="Геометрию и покрытие выбирать по ISO-группе",
            )
            counter += 1
    for diameter in range(14, 51, 2):
        for length_d in (2, 3, 4):
            _add(
                items,
                key=f"DR{counter:05d}", category="drill", subcategory="indexable",
                name=f"Корпусное U-сверло Ø{diameter}, {length_d}D",
                code=f"UDRILL-{diameter}-{length_d}D",
                operation_tags=("drill",), iso_groups=ISO_ALL,
                dimensions=f"Ø{diameter} мм; глубина до {length_d}D",
                description="Сверло со сменными пластинами и внутренней СОЖ",
                compatibility="Пластины центральная + периферийная соответствующего семейства",
                grade_hint="Обязательна проверка мощности, давления СОЖ и биения",
            )
            counter += 1
    for diameter in (1, 1.5, 2, 2.5, 3, 4, 5, 6):
        _add(
            items,
            key=f"DR{counter:05d}", category="drill", subcategory="center",
            name=f"Центровочное сверло Ø{diameter}", code=f"DIN333-A-{diameter:g}",
            operation_tags=("drill",), iso_groups=("P", "M", "K", "N"),
            dimensions=f"Рабочий диаметр Ø{diameter:g}",
            description="Центровка перед сверлением или поддержка центром",
            compatibility="Сверлильный/цанговый патрон",
            grade_hint="Не использовать чрезмерную глубину тонкой направляющей части",
        )
        counter += 1


def _mills(items: list[CatalogItem]) -> None:
    counter = 1
    for diameter in range(2, 21):
        for flutes in (2, 3, 4):
            iso = ("N",) if flutes == 2 else ("P", "M", "K", "S")
            _add(
                items,
                key=f"ML{counter:05d}", category="mill", subcategory="endmill",
                name=f"Концевая твердосплавная фреза Ø{diameter}, Z{flutes}",
                code=f"EM-CARBIDE-{diameter}-Z{flutes}",
                operation_tags=("mill",), iso_groups=iso,
                dimensions=f"Ø{diameter} мм; {flutes} зуба",
                description="Пазы, уступы, контуры и карманы",
                compatibility="Цанговый/гидро/термопатрон соответствующего диаметра",
                grade_hint="Z2 обычно для алюминия, Z4 для стали; нержавейка требует острой геометрии",
            )
            counter += 1
    for diameter in range(2, 17, 2):
        _add(
            items,
            key=f"ML{counter:05d}", category="mill", subcategory="ball",
            name=f"Сферическая фреза Ø{diameter}", code=f"BALL-{diameter}-Z2",
            operation_tags=("mill",), iso_groups=("P", "M", "K", "N", "S"),
            dimensions=f"Ø{diameter} мм; R{diameter/2:g}",
            description="3D-профили, радиусы и чистовая обработка поверхностей",
            compatibility="Высокоточный патрон с минимальным биением",
            grade_hint="Шаг по строке выбирать по требуемой шероховатости",
        )
        counter += 1
    for diameter in (6, 8, 10, 12, 16, 20):
        for angle in (45, 60, 90):
            _add(
                items,
                key=f"ML{counter:05d}", category="mill", subcategory="chamfer",
                name=f"Фасочная фреза Ø{diameter}, {angle}°", code=f"CHAMFER-{diameter}-{angle}",
                operation_tags=("mill",), iso_groups=ISO_ALL,
                dimensions=f"Ø{diameter}; угол {angle}°",
                description="Фаски, зенкование и снятие заусенцев",
                compatibility="Цанговый патрон",
                grade_hint="Уточнить: угол фрезы полный или половинный по каталогу",
            )
            counter += 1
    for diameter in (16, 20, 25, 32, 40, 50):
        for family, label in (("SHOULDER", "Фреза 90°"), ("HIGHFEED", "Высокоподачная фреза")):
            _add(
                items,
                key=f"ML{counter:05d}", category="mill", subcategory="indexable",
                name=f"{label} Ø{diameter}", code=f"{family}-{diameter}",
                operation_tags=("mill",), iso_groups=ISO_ALL,
                dimensions=f"Ø{diameter} мм; сменные пластины",
                description="Корпусная фреза для уступов/черновой выборки",
                compatibility="Оправка/цанга/приводной блок по хвостовику корпуса",
                grade_hint="Проверить число зубьев и допустимую мощность приводного инструмента",
            )
            counter += 1
    for diameter in (40, 50, 63, 80, 100, 125):
        _add(
            items,
            key=f"ML{counter:05d}", category="mill", subcategory="face",
            name=f"Торцевая фреза Ø{diameter}", code=f"FACEMILL-{diameter}-45",
            operation_tags=("mill",), iso_groups=("P", "M", "K", "N"),
            dimensions=f"Ø{diameter}; угол в плане 45°",
            description="Торцевое фрезерование плоскостей",
            compatibility="Оправка под посадку корпуса",
            grade_hint="Для токарного приводного блока проверить допустимый диаметр и момент",
        )
        counter += 1
    for diameter in (8, 10, 12, 16, 20, 25, 32):
        _add(
            items,
            key=f"ML{counter:05d}", category="mill", subcategory="threadmill",
            name=f"Резьбофреза Ø{diameter}", code=f"THREADMILL-{diameter}",
            operation_tags=("mill", "thread"), iso_groups=("P", "M", "K", "N", "S"),
            dimensions=f"Ø{diameter} мм",
            description="Фрезерование внутренней/наружной резьбы по винтовой интерполяции",
            compatibility="Стойка должна поддерживать круговую/винтовую интерполяцию",
            grade_hint="Шаг и диапазон диаметров сверять по конкретной резьбофрезе",
        )
        counter += 1


def _holders(items: list[CatalogItem]) -> None:
    counter = 1
    for system, desc in (
        ("ER16", "Цанговый патрон для малых диаметров"),
        ("ER20", "Универсальный компактный цанговый патрон"),
        ("ER25", "Универсальный цанговый патрон"),
        ("ER32", "Цанговый патрон повышенного диапазона"),
        ("ER40", "Цанговый патрон большого диапазона"),
        ("WELDON", "Боковой зажим фрезы с лыской"),
        ("HYDRO", "Гидропатрон с низким биением"),
        ("SHRINK", "Термоусадочный патрон"),
        ("DRILL_CHUCK", "Сверлильный патрон"),
    ):
        _add(
            items,
            key=f"HD{counter:04d}", category="holder", subcategory=system,
            name=desc, code=system,
            operation_tags=("drill", "mill"), iso_groups=ISO_ALL,
            dimensions="Размер хвостовика/цанги выбирается по инструменту",
            description=desc,
            compatibility="Приводной блок или шпиндель с соответствующим интерфейсом",
            grade_hint="Проверить биение, балансировку, допустимые обороты и длину зажима",
        )
        counter += 1


@lru_cache(maxsize=1)
def catalog() -> tuple[CatalogItem, ...]:
    items: list[CatalogItem] = []
    _turning_holders(items)
    _boring_bars(items)
    _turning_inserts(items)
    _grooving(items)
    _threading(items)
    _drills(items)
    _mills(items)
    _holders(items)
    return tuple(items)


def catalog_count() -> int:
    return len(catalog())


def get_item(key: str) -> CatalogItem | None:
    normalized = key.upper()
    return next((item for item in catalog() if item.key == normalized), None)


def search_catalog(
    *,
    category: str | None = None,
    operation: str | None = None,
    iso_group: str | None = None,
    query: str | None = None,
) -> list[CatalogItem]:
    items: Iterable[CatalogItem] = catalog()
    if category:
        items = (item for item in items if item.category == category)
    if operation:
        items = (item for item in items if operation in item.operation_tags)
    if iso_group:
        group = iso_group.upper()
        items = (item for item in items if group in item.iso_groups)
    if query:
        q = query.casefold()
        items = (
            item for item in items
            if q in item.name.casefold() or q in item.code.casefold() or q in item.description.casefold()
        )
    return list(items)
