from __future__ import annotations

import base64
import io
import math
import re
from dataclasses import dataclass
from typing import Any, Iterable


class ClientValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Point:
    z: float
    x: float

    def to_dict(self) -> dict[str, float]:
        return {"z": round(self.z, 4), "x": round(self.x, 4)}


OPERATION_LABELS = {
    "face": "Торцевание",
    "turn_rough": "Черновое наружное точение",
    "turn_finish": "Чистовое наружное точение",
    "bore_rough": "Черновая расточка",
    "bore_finish": "Чистовая расточка",
    "drill": "Сверление",
    "groove": "Канавка",
    "part": "Отрезка",
    "thread_od": "Наружная резьба",
    "thread_id": "Внутренняя резьба",
    "mill": "Фрезерование приводным инструментом",
}


def _f(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(result):
        return default
    return result


def normalize_contour(raw: Iterable[dict[str, Any]], *, minimum: int = 2) -> list[Point]:
    points: list[Point] = []
    for item in raw:
        z = _f(item.get("z"), math.nan)
        x = _f(item.get("x"), math.nan)
        if math.isfinite(z) and math.isfinite(x) and x >= 0:
            points.append(Point(z=z, x=x))
    if len(points) < minimum:
        raise ClientValidationError(f"Контур должен содержать минимум {minimum} точки.")

    # Keep equal-Z point pairs: they are vertical shoulders in an X/Z turning
    # contour, not duplicates. Remove only consecutive identical points.
    result: list[Point] = []
    for point in points:
        if not result or abs(result[-1].z - point.z) > 1e-6 or abs(result[-1].x - point.x) > 1e-6:
            result.append(point)
    if len(result) < minimum:
        raise ClientValidationError("После удаления повторов в контуре осталось слишком мало точек.")

    # The client convention is front face first (largest Z, normally Z0), then
    # movement into the part with non-increasing Z. Reverse a completely
    # backwards path; for a mixed order, use a stable Z sort while retaining
    # the operator/AI order of shoulder pairs at the same Z.
    if result[-1].z > result[0].z + 1e-6:
        result.reverse()
    if any(result[i + 1].z > result[i].z + 1e-6 for i in range(len(result) - 1)):
        result.sort(key=lambda point: point.z, reverse=True)
    return result


def interpolate_x(points: list[Point], z: float) -> float:
    if z >= points[0].z:
        return points[0].x
    if z <= points[-1].z:
        return points[-1].x
    for left, right in zip(points, points[1:]):
        if left.z >= z >= right.z:
            dz = right.z - left.z
            if abs(dz) < 1e-12:
                return right.x
            t = (z - left.z) / dz
            return left.x + (right.x - left.x) * t
    return points[-1].x


def spindle_rpm(vc_m_min: float, diameter_mm: float, max_rpm: int | None = None) -> int:
    if vc_m_min <= 0 or diameter_mm <= 0:
        return 0
    rpm = int(round((1000.0 * vc_m_min) / (math.pi * diameter_mm)))
    if max_rpm and max_rpm > 0:
        rpm = min(rpm, int(max_rpm))
    return max(1, rpm)


def _operation_defaults(operation_type: str) -> dict[str, float]:
    defaults = {
        "face": {"vc": 120, "feed": 0.18, "ap": 1.5},
        "turn_rough": {"vc": 130, "feed": 0.25, "ap": 2.0, "allow_x": 0.5, "allow_z": 0.2},
        "turn_finish": {"vc": 170, "feed": 0.10, "ap": 0.3},
        "bore_rough": {"vc": 100, "feed": 0.18, "ap": 1.0, "allow_x": 0.4, "allow_z": 0.2},
        "bore_finish": {"vc": 140, "feed": 0.08, "ap": 0.25},
        "drill": {"vc": 70, "feed": 0.12, "ap": 0.0},
        "groove": {"vc": 90, "feed": 0.08, "ap": 0.0},
        "part": {"vc": 75, "feed": 0.06, "ap": 0.0},
        "thread_od": {"vc": 45, "feed": 1.5, "ap": 0.0},
        "thread_id": {"vc": 35, "feed": 1.5, "ap": 0.0},
        "mill": {"vc": 120, "feed": 300, "ap": 1.0},
    }
    return defaults.get(operation_type, {"vc": 100, "feed": 0.15, "ap": 1.0}).copy()


def _merge_parameters(operation: dict[str, Any]) -> dict[str, float]:
    operation_type = str(operation.get("type") or operation.get("operation_type") or "")
    result = _operation_defaults(operation_type)
    params = operation.get("params") or {}
    for key in list(result):
        if key in params:
            result[key] = _f(params[key], result[key])
    for key in ("depth", "diameter", "width", "z", "pitch", "teeth", "rpm", "clearance"):
        if key in params:
            result[key] = _f(params[key], 0.0)
    return result


def _tool_snapshot(operation: dict[str, Any], index: int) -> dict[str, Any]:
    tool = operation.get("tool") or {}
    tool_no = int(_f(operation.get("tool_no") or tool.get("tool_no"), index + 1))
    return {
        "tool_no": max(1, tool_no),
        "name": str(tool.get("name") or operation.get("tool_name") or f"Инструмент {tool_no}"),
        "code": str(tool.get("code") or operation.get("tool_code") or "НЕ ЗАДАН"),
        "insert": str(tool.get("insert") or operation.get("insert") or ""),
        "nose_radius": _f(tool.get("nose_radius") or operation.get("nose_radius"), 0.0),
    }


def _rough_outer_paths(
    contour: list[Point], stock_diameter: float, params: dict[str, float]
) -> list[list[Point]]:
    ap = max(0.05, params.get("ap", 2.0))
    allowance = max(0.0, params.get("allow_x", 0.5))
    target_min = min(point.x for point in contour) + allowance
    if target_min >= stock_diameter:
        return []
    diameter_step = 2.0 * ap
    passes = max(1, math.ceil((stock_diameter - target_min) / diameter_step))
    paths: list[list[Point]] = []
    for pass_no in range(1, passes + 1):
        level = max(target_min, stock_diameter - diameter_step * pass_no)
        path = [Point(z=p.z, x=max(level, p.x + allowance)) for p in contour]
        paths.append(_dedupe_path(path))
    return paths


def _rough_inner_paths(
    contour: list[Point], stock_inner_diameter: float, params: dict[str, float]
) -> list[list[Point]]:
    ap = max(0.05, params.get("ap", 1.0))
    allowance = max(0.0, params.get("allow_x", 0.4))
    target_max = max(point.x for point in contour) - allowance
    if target_max <= stock_inner_diameter:
        return []
    diameter_step = 2.0 * ap
    passes = max(1, math.ceil((target_max - stock_inner_diameter) / diameter_step))
    paths: list[list[Point]] = []
    for pass_no in range(1, passes + 1):
        level = min(target_max, stock_inner_diameter + diameter_step * pass_no)
        path = [Point(z=p.z, x=min(level, max(0.0, p.x - allowance))) for p in contour]
        paths.append(_dedupe_path(path))
    return paths


def _dedupe_path(points: list[Point]) -> list[Point]:
    result: list[Point] = []
    for point in points:
        if not result or abs(result[-1].z - point.z) > 1e-6 or abs(result[-1].x - point.x) > 1e-6:
            result.append(point)
    return result


def _safe_comment(value: str) -> str:
    value = value.replace(";", ",").replace("\n", " ").strip()
    return value[:80]


def _motion_lines(path: list[Point], feed: float, clearance: float = 2.0) -> list[str]:
    if not path:
        return []
    first = path[0]
    lines = [f"G0 X{first.x + clearance:.3f} Z{first.z + clearance:.3f}", f"G1 X{first.x:.3f} Z{first.z:.3f} F{feed:.4f}"]
    lines.extend(f"G1 X{point.x:.3f} Z{point.z:.3f}" for point in path[1:])
    lines.append(f"G0 X{path[-1].x + clearance:.3f}")
    return lines


def _stock_removal_card(
    *, operation: dict[str, Any], tool: dict[str, Any], params: dict[str, float],
    stock: dict[str, Any], contour: list[Point], path_count: int,
) -> dict[str, Any]:
    op_type = str(operation.get("type") or operation.get("operation_type"))
    outer = not op_type.startswith("bore") and op_type != "thread_id"
    return {
        "operation": OPERATION_LABELS.get(op_type, op_type),
        "tool": f"T{tool['tool_no']} — {tool['code']}",
        "screen": "ShopTurn → Точение → Снятие припуска (Stock Removal)",
        "fields": {
            "Обработка": "Наружная" if outer else "Внутренняя",
            "Направление": "Продольная, по оси Z",
            "Контур": "CLIENT_CONTOUR",
            "Заготовка Ø": round(_f(stock.get("outer_diameter")), 3),
            "Длина заготовки": round(_f(stock.get("length")), 3),
            "Глубина резания ap, рад.": round(params.get("ap", 0), 3),
            "Припуск X (диаметр)": round(params.get("allow_x", 0), 3),
            "Припуск Z": round(params.get("allow_z", 0), 3),
            "Подача, мм/об": round(params.get("feed", 0), 4),
            "Скорость резания, м/мин": round(params.get("vc", 0), 1),
            "Количество проходов": path_count,
        },
        "contour_points": [point.to_dict() for point in contour],
        "notes": [
            "X задаётся в диаметрах.",
            "Перед запуском проверить направление оси Z, точку G54 и безопасный подвод.",
            "Сначала выполнить графическую симуляцию стойки и сухой прогон с малым override.",
        ],
    }


def generate_engineering_plan(payload: dict[str, Any]) -> dict[str, Any]:
    stock = payload.get("stock") or {}
    stock_diameter = _f(stock.get("outer_diameter"))
    stock_length = _f(stock.get("length"))
    stock_inner = max(0.0, _f(stock.get("inner_diameter")))
    if stock_diameter <= 0 or stock_length <= 0:
        raise ClientValidationError("Укажите фактический диаметр и длину заготовки.")

    contour_data = payload.get("contour") or {}
    contour = normalize_contour(contour_data.get("points") or [])
    contour_mode = str(contour_data.get("mode") or "outer")
    operations = payload.get("operations") or []
    if not operations:
        raise ClientValidationError("Добавьте хотя бы одну операцию.")

    machine = payload.get("machine") or {}
    max_rpm = int(_f(machine.get("max_rpm"), 0)) or None
    controller = str(machine.get("controller") or payload.get("controller") or "SINUMERIK 828D")
    title = str(payload.get("title") or "CNC_CLIENT_PROJECT")

    gcode: list[str] = [
        f"; {_safe_comment(title)}",
        f"; GENERATED BY CNC MASTER CLOUD ENGINEERING CLIENT",
        f"; CONTROLLER: {_safe_comment(controller)}",
        "; ВНИМАНИЕ: ПРОЕКТНЫЙ КОД. ОБЯЗАТЕЛЬНО ПРОВЕРИТЬ В СИМУЛЯЦИИ.",
        "G18 G40 G90 G95",
        "G54",
    ]
    toolpaths: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []
    stock_removal: list[dict[str, Any]] = []
    warnings: list[str] = [
        "Автоматически созданный G-код нельзя запускать без проверки траектории, нулей, коррекций и зажимов.",
        "Распознавание PDF является полуавтоматическим: размер и контур должен подтвердить оператор.",
    ]

    for index, operation in enumerate(operations):
        op_type = str(operation.get("type") or operation.get("operation_type") or "")
        if op_type not in OPERATION_LABELS:
            warnings.append(f"Операция {op_type or index + 1} не распознана и пропущена.")
            continue
        params = _merge_parameters(operation)
        tool = _tool_snapshot(operation, index)
        representative_diameter = max(1.0, stock_diameter if not op_type.startswith("bore") else max(stock_inner, 1.0))
        rpm = int(params.get("rpm") or spindle_rpm(params.get("vc", 100), representative_diameter, max_rpm))
        feed = max(0.0001, params.get("feed", 0.15))
        clearance = max(0.5, params.get("clearance", 2.0))
        op_paths: list[list[Point]] = []

        if op_type == "turn_rough":
            op_paths = _rough_outer_paths(contour, stock_diameter, params)
        elif op_type == "turn_finish":
            op_paths = [contour]
        elif op_type == "bore_rough":
            op_paths = _rough_inner_paths(contour, stock_inner, params)
        elif op_type == "bore_finish":
            op_paths = [contour]
        elif op_type == "face":
            z = max(point.z for point in contour)
            op_paths = [[Point(z=z, x=stock_diameter), Point(z=z, x=max(0.0, stock_inner))]]
        elif op_type == "drill":
            depth = abs(params.get("depth", stock_length))
            op_paths = [[Point(z=2.0, x=0.0), Point(z=-depth, x=0.0)]]
        elif op_type in {"groove", "part"}:
            z = params.get("z", min(point.z for point in contour))
            final_x = params.get("diameter", 0.0 if op_type == "part" else min(point.x for point in contour))
            op_paths = [[Point(z=z, x=stock_diameter + clearance), Point(z=z, x=max(0.0, final_x))]]
        elif op_type in {"thread_od", "thread_id"}:
            op_paths = [contour]
            warnings.append(f"{OPERATION_LABELS[op_type]}: цикл резьбы оставлен как шаблон; профиль и число проходов уточнить на стойке.")
        elif op_type == "mill":
            warnings.append("Фрезерование: 2D токарный контур не определяет траекторию по Y/C. Сформирована только карта операции.")

        gcode.extend([
            "",
            f"; --- {OPERATION_LABELS[op_type]} ---",
            f"T{tool['tool_no']} D1 ; {_safe_comment(tool['code'])}",
            f"G97 S{rpm} M3",
            "M8",
        ])
        if op_type in {"thread_od", "thread_id"}:
            pitch = max(0.1, params.get("pitch", feed))
            start = contour[0]
            end = contour[-1]
            gcode.extend([
                f"G0 X{start.x + clearance:.3f} Z{start.z + clearance:.3f}",
                f"; SINUMERIK: настройте CYCLE99/CYCLE97 под шаг {pitch:.3f} мм",
                f"G1 X{start.x:.3f} Z{start.z:.3f} F{pitch:.4f}",
                f"G33 Z{end.z:.3f} K{pitch:.4f}",
                f"G0 X{start.x + clearance:.3f}",
            ])
        elif op_type == "mill":
            gcode.extend([
                "; Приводной инструмент: задать ориентацию C, плоскость и координаты Y/X/Z.",
                "; Траектория не создаётся без геометрии кармана/отверстий.",
            ])
        else:
            for path in op_paths:
                gcode.extend(_motion_lines(path, feed, clearance))
        gcode.extend(["M9", "M5"])

        for path_no, path in enumerate(op_paths, 1):
            toolpaths.append({
                "operation": op_type,
                "operation_label": OPERATION_LABELS[op_type],
                "tool": tool,
                "pass": path_no,
                "points": [point.to_dict() for point in path],
            })

        if op_type in {"turn_rough", "bore_rough"}:
            stock_removal.append(_stock_removal_card(
                operation=operation,
                tool=tool,
                params=params,
                stock=stock,
                contour=contour,
                path_count=len(op_paths),
            ))

        steps.append({
            "number": len(steps) + 1,
            "operation": op_type,
            "title": OPERATION_LABELS[op_type],
            "tool": tool,
            "settings": {
                "rpm": rpm,
                "vc_m_min": round(params.get("vc", 0), 1),
                "feed": round(feed, 4),
                "ap_radial": round(params.get("ap", 0), 3),
                "allowance_x_diameter": round(params.get("allow_x", 0), 3),
                "allowance_z": round(params.get("allow_z", 0), 3),
            },
            "instructions": [
                f"Установить T{tool['tool_no']}: {tool['code']}.",
                "Проверить вылет, ориентацию пластины и коррекцию D1.",
                f"Задать S={rpm}, F={feed:.4f}.",
                "Выполнить графическую симуляцию и проверить отсутствие пересечений.",
                "Первый проход выполнить с уменьшенным override и контролем СОЖ/стружки.",
            ],
        })

    safe_x = stock_diameter + 10.0
    safe_z = max(point.z for point in contour) + 10.0
    gcode.extend(["", f"G0 X{safe_x:.3f} Z{safe_z:.3f}", "M30"])
    if not toolpaths and not steps:
        raise ClientValidationError("Не удалось сформировать ни одной операции.")

    return {
        "title": title,
        "controller": controller,
        "stock": {
            "outer_diameter": stock_diameter,
            "inner_diameter": stock_inner,
            "length": stock_length,
        },
        "contour_mode": contour_mode,
        "final_contour": [point.to_dict() for point in contour],
        "toolpaths": toolpaths,
        "stock_removal": stock_removal,
        "steps": steps,
        "gcode": "\n".join(gcode),
        "warnings": warnings,
        "summary": {
            "operations": len(steps),
            "tools": len({step["tool"]["tool_no"] for step in steps}),
            "passes": len(toolpaths),
            "stock_removal_cycles": len(stock_removal),
        },
    }


def analyze_pdf_bytes(
    data: bytes,
    page_number: int = 1,
    crop: tuple[float, float, float, float] | None = None,
    rotation: int = 0,
    profile_type: str = "outer",
) -> dict[str, Any]:
    if not data:
        raise ClientValidationError("PDF-файл пустой.")
    if len(data) > 20 * 1024 * 1024:
        raise ClientValidationError("PDF больше 20 МБ. Уменьшите разрешение или число страниц.")
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise ClientValidationError("На сервере не установлен PyMuPDF.") from exc

    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # pragma: no cover - depends on fitz internals
        raise ClientValidationError(f"Не удалось открыть PDF: {exc}") from exc
    if document.page_count < 1:
        raise ClientValidationError("В PDF нет страниц.")
    page_index = min(max(0, page_number - 1), document.page_count - 1)
    page = document.load_page(page_index)
    rotation = int(rotation or 0) % 360
    if rotation not in {0, 90, 180, 270}:
        rotation = 0
    zoom = 2.2
    matrix = fitz.Matrix(zoom, zoom).prerotate(rotation)
    clip = None
    if crop:
        x, y, w, h = crop
        if w > 0.01 and h > 0.01:
            rect = page.rect
            x0 = max(0.0, min(1.0, x)) * rect.width
            y0 = max(0.0, min(1.0, y)) * rect.height
            x1 = max(0.0, min(1.0, x + w)) * rect.width
            y1 = max(0.0, min(1.0, y + h)) * rect.height
            if x1 - x0 > rect.width * 0.02 and y1 - y0 > rect.height * 0.02:
                clip = fitz.Rect(x0, y0, x1, y1)
    pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)
    png = pix.tobytes("png")
    text = page.get_text("text", clip=clip) or ""
    dimensions = sorted(set(re.findall(r"(?<!\d)(\d{1,4}(?:[.,]\d{1,3})?)(?:\s*(?:mm|мм))?", text, flags=re.I)))[:80]
    dimension_entities: list[dict[str, Any]] = []
    patterns = [
        ("diameter", r"(?:Ø|⌀|\bD)\s*(\d{1,4}(?:[.,]\d{1,3})?)"),
        ("radius", r"\bR\s*(\d{1,4}(?:[.,]\d{1,3})?)"),
        ("angle", r"(\d{1,3}(?:[.,]\d+)?)\s*[°º]"),
        ("linear", r"(?<![A-Za-zА-Яа-яØ⌀R])(?<!\d)(\d{1,4}(?:[.,]\d{1,3})?)(?:\s*(?:mm|мм))?(?!\d)"),
    ]
    seen_entities: set[tuple[str, float]] = set()
    for kind, pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            raw = match.group(0).strip()
            try:
                value = float(match.group(1).replace(",", "."))
            except (ValueError, IndexError):
                continue
            if value <= 0 or value > 100000:
                continue
            key = (kind, round(value, 4))
            if key in seen_entities:
                continue
            seen_entities.add(key)
            confidence = 0.94 if kind in {"diameter", "radius", "angle"} else 0.72
            dimension_entities.append({"raw": raw, "value": value, "kind": kind, "confidence": confidence})
    dimension_entities = dimension_entities[:120]

    candidate: list[dict[str, float]] = []
    confidence = "low"
    diagnostics: dict[str, Any] = {"algorithm": "profile-v3-quality-gated", "candidates": 0}
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        if image is not None:
            height, width = image.shape[:2]
            # Normalize contrast and build several edge maps. Technical drawings vary
            # wildly: vector PDFs have razor-thin lines, scans have grey paper and noise.
            norm = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
            blur = cv2.GaussianBlur(norm, (3, 3), 0)
            edge_maps = [
                cv2.Canny(blur, 45, 135),
                cv2.Canny(blur, 80, 210),
            ]
            adaptive = cv2.adaptiveThreshold(
                blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 31, 9,
            )
            # Close small gaps in outlines but avoid merging dimensions/text into one blob.
            adaptive = cv2.morphologyEx(
                adaptive, cv2.MORPH_CLOSE,
                cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=1,
            )
            edge_maps.append(adaptive)

            scored: list[tuple[float, Any, str]] = []
            for source_index, edges in enumerate(edge_maps):
                contours, hierarchy = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    area = abs(cv2.contourArea(contour))
                    perimeter = cv2.arcLength(contour, True)
                    aspect = w / max(1.0, float(h))
                    center_y = y + h / 2.0
                    point_count = len(contour)

                    if w < width * (0.14 if crop else 0.20) or h < height * 0.008:
                        continue
                    if w > width * 0.985 and h > height * 0.985:
                        continue
                    if aspect < (1.15 if profile_type == "free" else 1.45):
                        continue
                    if point_count < 20 or perimeter < width * 0.12:
                        continue

                    circularity = (4.0 * math.pi * area / (perimeter * perimeter)) if perimeter > 0 else 0.0
                    if profile_type != "free" and aspect < 2.0 and circularity > 0.42:
                        continue

                    # Reward long, horizontally oriented outlines with real vertical
                    # variation. Penalize page borders, dimension lines and text rows.
                    width_ratio = w / width
                    height_ratio = h / height
                    fill_ratio = area / max(1.0, float(w * h))
                    line_like_penalty = 9.0 if height_ratio < 0.018 else 0.0
                    border_penalty = 10.0 if x < 3 and y < 3 and w > width * 0.9 else 0.0
                    text_penalty = 5.0 if aspect > 18 and height_ratio < 0.06 else 0.0
                    position_bonus = 1.2 if center_y < height * 0.72 else 0.0
                    score = (
                        18.0 * width_ratio
                        + min(aspect, 12.0)
                        + min(perimeter / max(width, 1), 8.0)
                        + 4.0 * min(height_ratio, 0.25)
                        + 2.0 * min(fill_ratio, 0.35)
                        + position_bonus
                        - line_like_penalty - border_penalty - text_penalty
                    )
                    scored.append((score, contour, f"map-{source_index}"))

            diagnostics["candidates"] = len(scored)
            if scored:
                scored.sort(key=lambda item: item[0], reverse=True)
                selected_score, selected_contour, selected_source = scored[0]
                selected = selected_contour.reshape(-1, 2)
                diagnostics.update({"selected_score": round(float(selected_score), 3), "source": selected_source})

                # Split a closed outline into the two paths between its extreme X points.
                # Outer profile follows the upper silhouette; inner follows the lower one.
                left_i = int(np.argmin(selected[:, 0]))
                right_i = int(np.argmax(selected[:, 0]))

                def contour_path(start: int, end: int) -> Any:
                    if start <= end:
                        return selected[start : end + 1]
                    return np.vstack((selected[start:], selected[: end + 1]))

                path_a = contour_path(left_i, right_i)
                path_b = contour_path(right_i, left_i)[::-1]
                mean_a = float(np.mean(path_a[:, 1]))
                mean_b = float(np.mean(path_b[:, 1]))
                if profile_type == "inner":
                    chosen = path_a if mean_a >= mean_b else path_b
                elif profile_type == "free":
                    chosen = path_a if len(path_a) >= len(path_b) else path_b
                else:
                    chosen = path_a if mean_a <= mean_b else path_b

                # Build a stable left-to-right envelope. Median sampling suppresses
                # arrowheads, hatching and isolated characters better than min/max alone.
                buckets: dict[int, list[float]] = {}
                for px, py in chosen:
                    buckets.setdefault(int(round(float(px))), []).append(float(py))
                ordered: list[tuple[float, float]] = []
                for key in sorted(buckets):
                    values = sorted(buckets[key])
                    if profile_type == "inner":
                        py = float(np.percentile(values, 75))
                    elif profile_type == "outer":
                        py = float(np.percentile(values, 25))
                    else:
                        py = float(np.median(values))
                    ordered.append((float(key), py))

                # Remove isolated spikes with a small median filter.
                if len(ordered) >= 7:
                    ys = np.array([p[1] for p in ordered], dtype=np.float32)
                    smooth = ys.copy()
                    for i in range(2, len(ys) - 2):
                        smooth[i] = float(np.median(ys[i-2:i+3]))
                    ordered = [(ordered[i][0], float(smooth[i])) for i in range(len(ordered))]

                if len(ordered) >= 2:
                    curve = np.array(ordered, dtype=np.float32).reshape(-1, 1, 2)
                    epsilon = max(0.8, 0.0018 * cv2.arcLength(curve, False))
                    approx = cv2.approxPolyDP(curve, epsilon, False)
                    simplified = [tuple(map(float, point[0])) for point in approx]
                else:
                    simplified = ordered

                clean: list[tuple[float, float]] = []
                for point in simplified:
                    if not clean or abs(point[0] - clean[-1][0]) >= 1.0 or abs(point[1] - clean[-1][1]) >= 1.0:
                        clean.append(point)
                if len(clean) > 180:
                    indexes = np.linspace(0, len(clean) - 1, 180).astype(int)
                    clean = [clean[int(i)] for i in indexes]

                candidate = [{"px": round(px, 2), "py": round(py, 2)} for px, py in clean]
                if len(candidate) >= 3:
                    xs = [p["px"] for p in candidate]
                    ys = [p["py"] for p in candidate]
                    x_span = max(xs) - min(xs)
                    y_span = max(ys) - min(ys)
                    monotonic = all(xs[i] <= xs[i + 1] + 1.5 for i in range(len(xs) - 1))
                    jump_limit = max(7.0, y_span * 0.55)
                    huge_jumps = sum(abs(ys[i + 1] - ys[i]) > jump_limit for i in range(len(ys) - 1))
                    flat_ratio = y_span / max(x_span, 1.0)
                    diagnostics.update({"points": len(candidate), "x_span": round(x_span, 2), "y_span": round(y_span, 2), "huge_jumps": huge_jumps})
                    vertical_ratio = y_span / max(float(height), 1.0)
                    diagnostics["vertical_ratio"] = round(vertical_ratio, 4)
                    if x_span < width * (0.14 if crop else 0.19) or not monotonic or huge_jumps > 1 or flat_ratio < 0.004:
                        candidate = []
                        confidence = "low"
                        diagnostics["quality_reason"] = "геометрия кандидата нестабильна"
                    else:
                        # A nearly flat line in a technical drawing is frequently a dimension
                        # or extension line. Keep it as a visible hint but never mark it high.
                        if vertical_ratio < 0.028:
                            confidence = "medium" if selected_score >= 6.0 else "low"
                            diagnostics["quality_reason"] = "слишком плоский кандидат; возможна размерная линия"
                        elif crop and selected_score >= 8.0 and huge_jumps == 0:
                            confidence = "high"
                            diagnostics["quality_reason"] = "контур прошёл геометрическую проверку"
                        elif selected_score >= 6.0:
                            confidence = "medium"
                            diagnostics["quality_reason"] = "нужна проверка оператором"
                        else:
                            confidence = "low"
                            diagnostics["quality_reason"] = "низкая оценка контура"
                else:
                    candidate = []
                    confidence = "low"
    except Exception:
        # The manual tracing path remains available even if OpenCV cannot parse the drawing.
        candidate = []
        confidence = "low"

    return {
        "page": page_index + 1,
        "page_count": document.page_count,
        "width_px": pix.width,
        "height_px": pix.height,
        "image_data_url": "data:image/png;base64," + base64.b64encode(png).decode("ascii"),
        "text_preview": text[:5000],
        "dimension_hints": dimensions,
        "dimension_entities": dimension_entities,
        "candidate_pixels": candidate,
        "candidate_confidence": confidence,
        "crop_applied": bool(crop),
        "rotation": rotation,
        "profile_type": profile_type,
        "autocontour_diagnostics": diagnostics,
        "warnings": [
            "Автоконтур является подсказкой, а не измерительным результатом.",
            "Обязательно задайте масштаб по известному размеру и вручную проверьте все точки.",
        ],
    }


def gcode_filename(title: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9А-Яа-я_-]+", "_", title).strip("_")
    return (normalized or "cnc_project")[:80] + ".mpf"


def analyze_image_bytes(data: bytes, rotation: int = 0, profile_type: str = "outer") -> dict[str, Any]:
    """Prepare a raster drawing/photo for operator-guided recognition.

    Raster images do not contain a trustworthy text layer, so this function never
    invents dimensions. It returns the normalized preview and leaves dimensions
    empty for manual confirmation or a future OCR provider.
    """
    if not data:
        raise ClientValidationError("Файл изображения пустой.")
    if len(data) > 20 * 1024 * 1024:
        raise ClientValidationError("Изображение больше 20 МБ.")
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError as exc:
        raise ClientValidationError("На сервере не установлен OpenCV.") from exc
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ClientValidationError("Не удалось прочитать изображение.")
    rotation = int(rotation or 0) % 360
    if rotation == 90:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif rotation == 180:
        image = cv2.rotate(image, cv2.ROTATE_180)
    elif rotation == 270:
        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise ClientValidationError("Не удалось подготовить изображение.")
    h, w = image.shape[:2]
    diagnostics: dict[str, Any] = {
        "algorithm": "raster-preview-v1",
        "candidates": 0,
        "quality_reason": "для фотографии нужен AI-анализ или ручная обводка",
    }
    return {
        "page": 1,
        "page_count": 1,
        "width_px": w,
        "height_px": h,
        "image_data_url": "data:image/png;base64," + base64.b64encode(encoded.tobytes()).decode("ascii"),
        "text_preview": "",
        "dimension_hints": [],
        "dimension_entities": [],
        "candidate_pixels": [],
        "candidate_confidence": "low",
        "crop_applied": False,
        "rotation": rotation,
        "profile_type": profile_type,
        "autocontour_diagnostics": diagnostics,
        "warnings": [
            "Фото не содержит текстового слоя: размеры необходимо подтвердить вручную.",
            "Перед построением задайте масштаб по известному размеру.",
        ],
    }
