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
    "drill_insert": "Пластины для корпусных сверл",
    "mill": "Фрезы",
    "mill_insert": "Фрезерные пластины",
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


UKRAINE_MARKET_SOURCES = (
    "ISCAR Ukraine — https://webshop.iscartool.com.ua/",
    "ZCC-CT Ukraine — https://zccct.com.ua/",
    "TaeguTec Ukraine — https://taegutec.com.ua/",
    "KDM Group — https://kdmgroup.com.ua/",
    "Океан Трейд — https://ocean.biz.ua/",
    "Фрактальность — https://fractalnost.com.ua/",
)

def _market_source(index: int) -> str:
    return UKRAINE_MARKET_SOURCES[index % len(UKRAINE_MARKET_SOURCES)] + "; наличие и цену проверять у продавца"

def _expanded_market_catalog(items: list[CatalogItem]) -> None:
    """Расширенный справочник ISO-семейств, реально встречающихся у украинских поставщиков.

    Это не снимок складских остатков: позиции описаны на уровне стандартизованного семейства/типоразмера.
    """
    n = 1
    # Наружные державки: основные ISO-семейства, размеры и исполнения.
    holder_families = {
        "PCLNR": "CNMG", "PCLNL": "CNMG", "DCLNR": "CNMG", "DCLNL": "CNMG",
        "MCLNR": "CNMG", "MCLNL": "CNMG", "MWLNR": "WNMG", "MWLNL": "WNMG",
        "PDJNR": "DNMG", "PDJNL": "DNMG", "MDJNR": "DNMG", "MDJNL": "DNMG",
        "MTJNR": "TNMG", "MTJNL": "TNMG", "PTGNR": "TNMG", "PTGNL": "TNMG",
        "MVJNR": "VNMG", "MVJNL": "VNMG", "SVJCR": "VCMT/VBMT", "SVJCL": "VCMT/VBMT",
        "PSBNR": "SNMG", "PSBNL": "SNMG", "SCLCR": "CCMT", "SCLCL": "CCMT",
        "SDJCR": "DCMT", "SDJCL": "DCMT", "STGCR": "TCMT", "STGCL": "TCMT",
        "SRDCN": "RCMT", "SSSCR": "SCMT", "SSSCL": "SCMT",
    }
    size_suffix = {12:"F", 16:"H", 20:"K", 25:"M", 32:"P", 40:"R"}
    insert_suffix = {"CNMG":"12","WNMG":"08","DNMG":"15","TNMG":"16","VNMG":"16","VCMT/VBMT":"16","SNMG":"12","CCMT":"09","DCMT":"11","TCMT":"16","RCMT":"12","SCMT":"12"}
    for fam, ins in holder_families.items():
        for shank in size_suffix:
            code=f"{fam} {shank}{shank}{size_suffix[shank]}{insert_suffix[ins]}"
            _add(items,key=f"UAH{n:06d}",category="turn_holder",subcategory=fam,name=f"Державка {fam} {shank}×{shank}",code=code,operation_tags=("turn_rough","turn_finish","face"),iso_groups=ISO_ALL,dimensions=f"Хвостовик {shank}×{shank} мм",description="Стандартная ISO-державка для наружного точения/торцевания",compatibility=f"Пластины {ins}; направление и угол в плане определяются кодом",grade_hint="Проверить высоту центра, направление подачи и допустимый вылет",source=_market_source(n)); n+=1
    # Расточные державки: сталь, твердосплав, антивибрационные, разные головки.
    boring_heads={"SCLCR":"CCMT","SDUCR":"DCMT","STFCR":"TCMT","SVUCR":"VCMT","SWLNR":"WNMG","S16Q-SIR":"16IR","S16Q-SER":"16ER","MGIVR":"канавочная пластина"}
    for material, reach in (("S","3D"),("A","5D"),("C","7D"),("DAMP","10D")):
        for dia in (6,8,10,12,16,20,25,32,40,50):
            for head, ins in boring_heads.items():
                code=f"{material}{dia:02d}-{head}"
                _add(items,key=f"UAB{n:06d}",category="boring_bar",subcategory=material,name=f"Расточная державка {head} Ø{dia}",code=code,operation_tags=("bore", "thread" if "IR" in head else "bore"),iso_groups=ISO_ALL,dimensions=f"Хвостовик Ø{dia} мм; ориентировочный вылет до {reach}",description="Внутренняя обработка отверстий; исполнение зависит от головки",compatibility=f"{ins}",grade_hint="Минимальный диаметр отверстия и длину вылета сверять по каталогу производителя",source=_market_source(n)); n+=1
    # Токарные пластины: распространённые формы, размеры, радиусы и группы материалов.
    insert_sizes={
      "CNMG":("120402","120404","120408","120412","160608"),"WNMG":("060404","080404","080408","080412"),
      "DNMG":("110404","150404","150408","150412"),"TNMG":("160404","160408","220408"),
      "VNMG":("160402","160404","160408"),"SNMG":("090304","120404","120408","150612"),
      "CCMT":("060202","060204","09T302","09T304","09T308","120404"),
      "DCMT":("070202","070204","11T302","11T304","11T308"),
      "TCMT":("090202","110202","110204","16T304"),"VCMT":("110302","110304","160404"),
      "VBMT":("110202","110204","160404"),"SCMT":("09T304","120404","120408"),
      "RCMT":("0602","0803","1003","1204","1606"),"CPMT":("090304","120408"),
    }
    geos=("F","PF","MF","M","PM","MM","R","PR","MR")
    for fam,sizes in insert_sizes.items():
        for size in sizes:
            for geo in geos:
                for grp in ISO_ALL:
                    code=f"{fam} {size}-{geo} ({grp})"
                    _add(items,key=f"UAI{n:06d}",category="turn_insert",subcategory=fam,name=f"Пластина {fam} {size}, геометрия {geo}, ISO {grp}",code=code,operation_tags=("turn_rough","turn_finish","face","bore"),iso_groups=(grp,),dimensions=f"Типоразмер {size}; стружколом {geo}",description="ISO-семейство сменной твердосплавной пластины; конкретная марка сплава зависит от производителя",compatibility=f"Державка под {fam}",grade_hint=f"Выбирать покрытие и сплав для ISO {grp}; радиус вершины зашифрован в размере",source=_market_source(n)); n+=1
    # Канавка/отрезка: наружная, внутренняя, торцевая, лезвия и пластины.
    groove_systems=("MGEHR","MGEHL","MGIVR","MGIVL","MFGHR","MFGHL","QEHD","DGTR","TTER","TDIHR","TDIHL")
    groove_inserts=("MGMN","MGR","MGL","GTN","DGN","TAG","TDXU","TDIT","GIPI","GIPY")
    for sys in groove_systems:
        for shank in (12,16,20,25,32):
            for width in (1.0,1.5,2.0,2.5,3.0,4.0,5.0,6.0,8.0):
                _add(items,key=f"UAGH{n:06d}",category="groove",subcategory="holder",name=f"Державка {sys} {shank} мм, ширина {width:g}",code=f"{sys} {shank}{shank}-{width:g}",operation_tags=("groove",),iso_groups=ISO_ALL,dimensions=f"Хвостовик {shank} мм; ширина {width:g} мм",description="Державка для наружной, внутренней, торцевой канавки либо отрезки в зависимости от системы",compatibility="Пластина соответствующей системы и ширины",grade_hint="Проверить максимальную глубину, направление и боковой зазор",source=_market_source(n)); n+=1
    for fam in groove_inserts:
        for width in (1.0,1.5,2.0,2.5,3.0,4.0,5.0,6.0,8.0):
            for grp in ISO_ALL:
                _add(items,key=f"UAGI{n:06d}",category="groove",subcategory="insert",name=f"Пластина {fam} {width:g} мм ISO {grp}",code=f"{fam}-{int(width*100):03d}-{grp}",operation_tags=("groove",),iso_groups=(grp,),dimensions=f"Ширина {width:g} мм",description="Канавочная/отрезная пластина; геометрия зависит от системы",compatibility=f"Корпус/державка системы {fam}",grade_hint=f"Сплав под ISO {grp}; для отрезки важны подача СОЖ и жёсткость",source=_market_source(n)); n+=1
    # Резьба: ISO, UN, Whitworth, трапеция, ACME, NPT/BSP.
    profiles=(("ISO",60),("UN",60),("AG60",60),("W",55),("BSP",55),("NPT",60),("TR",30),("ACME",29))
    for side in ("ER","EL","IR","IL"):
        for size in (6,8,11,16,22,27):
            for prof,angle in profiles:
                for pitch in (0.5,0.75,1.0,1.25,1.5,1.75,2.0,2.5,3.0,3.5,4.0,5.0,6.0):
                    _add(items,key=f"UATR{n:06d}",category="thread",subcategory="insert",name=f"Резьбовая пластина {size}{side} {pitch:g}{prof}",code=f"{size}{side} {pitch:g}{prof}",operation_tags=("thread",),iso_groups=ISO_ALL,dimensions=f"Профиль {prof} {angle}°; шаг {pitch:g}",description="Полный/частичный профиль зависит от маркировки производителя",compatibility=f"Державка под пластину {size}{side}",grade_hint="Проверить шаг, направление, наружное/внутреннее исполнение",source=_market_source(n)); n+=1
    for kind in ("SER","SEL","SIR","SIL"):
        for shank in (10,12,16,20,25,32,40):
            for ins in (11,16,22,27):
                _add(items,key=f"UATH{n:06d}",category="thread",subcategory="holder",name=f"Резьбовая державка {kind} {shank}, пластина {ins}",code=f"{kind} {shank}{shank}K{ins}",operation_tags=("thread",),iso_groups=ISO_ALL,dimensions=f"Размер {shank} мм; пластина {ins}",description="Наружная/внутренняя правая/левая резьбовая державка",compatibility=f"Пластины {ins}ER/EL/IR/IL",grade_hint="Исполнение кода сверять по фактическому направлению резьбы",source=_market_source(n)); n+=1
    # Сверла и сменные головки/пластины.
    for kind,label in (("HSS","HSS-R сверло"),("HSS-G","Шлифованное HSS сверло"),("HSS-CO","Кобальтовое сверло"),("CARBIDE","Твердосплавное сверло"),("STEP","Ступенчатое сверло"),("SPOT","Центровочное/spot сверло")):
        for d10 in range(10, 501, 5):
            d=d10/10
            for ld in ((3,5,8,12) if kind=="CARBIDE" else (3,5)):
                _add(items,key=f"UADR{n:06d}",category="drill",subcategory=kind,name=f"{label} Ø{d:g}, {ld}D",code=f"{kind}-{d:g}-{ld}D",operation_tags=("drill",),iso_groups=ISO_ALL,dimensions=f"Ø{d:g} мм; длина {ld}D",description="Сверло общего/производственного назначения",compatibility="Цанговый, гидро-, термо- или сверлильный патрон",grade_hint="Выбирать геометрию, покрытие и СОЖ по материалу",source=_market_source(n)); n+=1
    drill_families=("U-DRILL","SPADE","SUMOCHAM","CHAMDRILL","CROWNLOC","MAGICDRILL","DRILLMEISTER","KSEM")
    for fam in drill_families:
        for dia in range(12,81):
            for ld in (2,3,4,5,8):
                _add(items,key=f"UACD{n:06d}",category="drill",subcategory="indexable",name=f"Корпусное сверло {fam} Ø{dia}, {ld}D",code=f"{fam}-{dia}-{ld}D",operation_tags=("drill",),iso_groups=ISO_ALL,dimensions=f"Ø{dia} мм; {ld}D",description="Корпусное сверло со сменными пластинами либо головкой",compatibility=f"Сменные элементы системы {fam}",grade_hint="Проверить хвостовик, давление внутренней СОЖ, центральную/периферийную позицию",source=_market_source(n)); n+=1
    for fam in drill_families:
        for size in range(12,81):
            for pos in ("CENTER","PERIPHERY","HEAD"):
                for grp in ISO_ALL:
                    _add(items,key=f"UADI{n:06d}",category="drill_insert",subcategory=fam,name=f"Сменный элемент {fam} {size} {pos} ISO {grp}",code=f"{fam}-{size}-{pos}-{grp}",operation_tags=("drill",),iso_groups=(grp,),dimensions=f"Для номинального Ø{size}; позиция {pos}",description="Пластина или сменная сверлильная головка; код является поисковым семейством",compatibility=f"Корпусное сверло {fam} соответствующего диаметра",grade_hint="Центральные и периферийные пластины часто имеют разные геометрии и сплавы",source=_market_source(n)); n+=1
    # Фрезы и фрезерные пластины.
    mill_fams=(("ENDMILL","Концевая"),("BALL","Сферическая"),("CORNER-R","Радиусная"),("ROUGH","Черновая"),("CHAMFER","Фасочная"),("THREADMILL","Резьбофреза"))
    for fam,label in mill_fams:
        for d10 in range(10, 321, 5):
            d=d10/10
            for z in (2,3,4,5,6):
                _add(items,key=f"UAML{n:06d}",category="mill",subcategory="solid",name=f"{label} твердосплавная фреза Ø{d:g} Z{z}",code=f"{fam}-{d:g}-Z{z}",operation_tags=("mill",),iso_groups=ISO_ALL,dimensions=f"Ø{d:g} мм; Z{z}",description="Монолитная твердосплавная фреза",compatibility="Цанга/гидропатрон/термопатрон",grade_hint="Число зубьев, угол спирали и покрытие выбирать по материалу",source=_market_source(n)); n+=1
    body_fams=("APKT","APMT","SEKT","SEHT","ADKT","R390","LNMU","ONMU","SDMT","RDMT","RCMT","XOMX","SOMT","BLMP","AXMT")
    for fam in body_fams:
        for dia in (16,20,25,32,40,50,63,80,100,125,160):
            for z in (2,3,4,5,6,8,10):
                _add(items,key=f"UAMB{n:06d}",category="mill",subcategory="indexable",name=f"Корпусная фреза под {fam} Ø{dia} Z{z}",code=f"MILL-{fam}-{dia}-Z{z}",operation_tags=("mill",),iso_groups=ISO_ALL,dimensions=f"Ø{dia} мм; Z{z}",description="Концевая/торцевая/высокоподачная корпусная фреза в зависимости от семейства",compatibility=f"Фрезерные пластины {fam}",grade_hint="Проверить посадку, максимальные обороты, момент приводного блока",source=_market_source(n)); n+=1
    for fam in body_fams:
        for size in (6,8,9,10,11,12,15,16,18,20):
            for geo in ("P","M","R","ALU","HFM"):
                for grp in ISO_ALL:
                    _add(items,key=f"UAMI{n:06d}",category="mill_insert",subcategory=fam,name=f"Фрезерная пластина {fam} {size} {geo} ISO {grp}",code=f"{fam}-{size}-{geo}-{grp}",operation_tags=("mill",),iso_groups=(grp,),dimensions=f"Семейство {fam}; размер {size}; геометрия {geo}",description="Сменная пластина для корпусной фрезы",compatibility=f"Корпус фрезы под {fam}",grade_hint=f"Марка сплава для ISO {grp}; точный размер и винт сверять по корпусу",source=_market_source(n)); n+=1
    # Оснастка: интерфейсы и типоразмеры.
    systems=("ER11","ER16","ER20","ER25","ER32","ER40","WELDON","HYDRO","SHRINK","SIDELOCK","MORSE","DRILL-CHUCK","VDI20","VDI30","VDI40","VDI50","BMT45","BMT55","BMT65","CAT40","BT30","BT40","BT50","HSK-A40","HSK-A63","CAPTO-C4","CAPTO-C5","CAPTO-C6")
    for sys in systems:
        for size in (4,6,8,10,12,16,20,25,32,40):
            _add(items,key=f"UAHD{n:06d}",category="holder",subcategory=sys,name=f"Оснастка {sys}, размер {size}",code=f"{sys}-{size}",operation_tags=("drill","mill","turn_rough","turn_finish"),iso_groups=ISO_ALL,dimensions=f"Система {sys}; размер {size}",description="Инструментальная/станочная оснастка, патрон, блок, втулка или оправка",compatibility="Интерфейс станка и хвостовик инструмента должны совпадать",grade_hint="Проверить биение, балансировку, максимальные обороты и габариты револьвера",source=_market_source(n)); n+=1


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
    _expanded_market_catalog(items)
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
        aliases = {"turning_holders":"turn_holder","boring_bars":"boring_bar","turning_inserts":"turn_insert","grooving_parting":"groove","threading":"thread","drills":"drill","drill_inserts":"drill_insert","mills":"mill","milling_inserts":"mill_insert","toolholding":"holder"}
        category = aliases.get(category, category)
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
