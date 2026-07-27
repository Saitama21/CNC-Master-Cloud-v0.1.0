from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CalculatorSpec:
    key: str
    label: str
    prompt: str


CALCULATORS = (
    CalculatorSpec("rpm", "Обороты n по Vc и D", "Введите: Vc_м/мин диаметр_мм\nПример: 180 100"),
    CalculatorSpec("vc", "Скорость Vc по n и D", "Введите: обороты диаметр_мм\nПример: 600 100"),
    CalculatorSpec("turn_feed", "Подача мм/мин при точении", "Введите: обороты подача_мм/об\nПример: 600 0.2"),
    CalculatorSpec("feed_rev", "Подача мм/об", "Введите: подача_мм/мин обороты\nПример: 120 600"),
    CalculatorSpec("mill_feed", "Подача фрезы", "Введите: обороты число_зубьев fz_мм/зуб\nПример: 3000 4 0.04"),
    CalculatorSpec("turn_time", "Время точения", "Введите: длина_мм обороты подача_мм/об число_проходов\nПример: 100 600 0.2 3"),
    CalculatorSpec("drill_time", "Время сверления", "Введите: глубина_мм обороты подача_мм/об число_отверстий\nПример: 30 800 0.12 4"),
    CalculatorSpec("mill_time", "Время фрезерования", "Введите: путь_мм подача_мм/мин число_проходов\nПример: 400 300 2"),
    CalculatorSpec("taper", "Конус и угол", "Введите: D_большой D_малый длина\nПример: 50 40 100"),
    CalculatorSpec("thread_feed", "Подача резьбы", "Введите: шаг_мм обороты\nПример: 1.5 300"),
    CalculatorSpec("turn_mrr", "Съём металла при точении", "Введите: Vc_м/мин ap_мм f_мм/об\nПример: 180 2 0.25"),
    CalculatorSpec("roughness", "Теоретическая Ra", "Введите: подача_мм/об радиус_вершины_мм\nПример: 0.12 0.4"),
    CalculatorSpec("bolt_circle", "Координаты отверстий по окружности", "Введите: диаметр_окружности число_отверстий начальный_угол\nПример: 100 8 0"),
)


def _positive(*values: float) -> None:
    if any(value <= 0 for value in values):
        raise ValueError("Все значения должны быть больше нуля")


def calculate(key: str, values: list[float]) -> str:
    if key == "rpm":
        vc, diameter = values
        _positive(vc, diameter)
        rpm = 1000 * vc / (math.pi * diameter)
        return f"n = {rpm:.0f} об/мин"
    if key == "vc":
        rpm, diameter = values
        _positive(rpm, diameter)
        vc = math.pi * diameter * rpm / 1000
        return f"Vc = {vc:.1f} м/мин"
    if key == "turn_feed":
        rpm, feed_rev = values
        _positive(rpm, feed_rev)
        return f"Vf = {rpm * feed_rev:.1f} мм/мин"
    if key == "feed_rev":
        feed_min, rpm = values
        _positive(feed_min, rpm)
        return f"f = {feed_min / rpm:.4f} мм/об"
    if key == "mill_feed":
        rpm, teeth, fz = values
        _positive(rpm, teeth, fz)
        return f"Vf = {rpm * teeth * fz:.1f} мм/мин"
    if key == "turn_time":
        length, rpm, feed_rev, passes = values
        _positive(length, rpm, feed_rev, passes)
        minutes = length / (rpm * feed_rev) * passes
        return f"Время ≈ {minutes:.2f} мин ({minutes * 60:.0f} с)"
    if key == "drill_time":
        depth, rpm, feed_rev, holes = values
        _positive(depth, rpm, feed_rev, holes)
        minutes = depth / (rpm * feed_rev) * holes
        return f"Чистое время подачи ≈ {minutes:.2f} мин ({minutes * 60:.0f} с)"
    if key == "mill_time":
        path, feed_min, passes = values
        _positive(path, feed_min, passes)
        minutes = path / feed_min * passes
        return f"Время ≈ {minutes:.2f} мин ({minutes * 60:.0f} с)"
    if key == "taper":
        d_big, d_small, length = values
        _positive(d_big, d_small, length)
        delta = abs(d_big - d_small)
        half_angle = math.degrees(math.atan(delta / (2 * length)))
        full_angle = half_angle * 2
        taper = delta / length
        return (
            f"Конусность (D−d)/L = {taper:.5f}\n"
            f"Полуугол α = {half_angle:.4f}°\nПолный угол = {full_angle:.4f}°"
        )
    if key == "thread_feed":
        pitch, rpm = values
        _positive(pitch, rpm)
        return f"Подача = {pitch:g} мм/об; Vf = {pitch * rpm:.1f} мм/мин"
    if key == "turn_mrr":
        vc, ap, feed_rev = values
        _positive(vc, ap, feed_rev)
        return f"Q ≈ {vc * ap * feed_rev:.1f} см³/мин"
    if key == "roughness":
        feed_rev, radius = values
        _positive(feed_rev, radius)
        ra_microns = (feed_rev ** 2 / (32 * radius)) * 1000
        return f"Теоретическая Ra ≈ {ra_microns:.2f} мкм (без учёта вибраций и геометрии кромки)"
    if key == "bolt_circle":
        diameter, holes, start_angle = values
        _positive(diameter, holes)
        count = int(round(holes))
        if count < 2 or count > 100:
            raise ValueError("Число отверстий должно быть от 2 до 100")
        radius = diameter / 2
        lines = [f"Координаты для Ø{diameter:g}, отверстий: {count}"]
        for index in range(count):
            angle = start_angle + index * 360 / count
            rad = math.radians(angle)
            x = radius * math.cos(rad)
            y = radius * math.sin(rad)
            lines.append(f"{index + 1:02d}: A={angle:.3f}°  X={x:.3f}  Y={y:.3f}")
        return "\n".join(lines)
    raise ValueError("Неизвестный калькулятор")


def expected_count(key: str) -> int:
    return {
        "rpm": 2, "vc": 2, "turn_feed": 2, "feed_rev": 2, "mill_feed": 3,
        "turn_time": 4, "drill_time": 4, "mill_time": 3, "taper": 3,
        "thread_feed": 2, "turn_mrr": 3, "roughness": 2, "bolt_circle": 3,
    }[key]
