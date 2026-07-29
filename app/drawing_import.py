from __future__ import annotations

import io
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.cnc_client import ClientValidationError, analyze_image_bytes, analyze_pdf_bytes


@dataclass(frozen=True)
class ImportDecision:
    format: str
    route: str
    precision: str
    automatic_geometry: bool
    requires_confirmation: bool
    notes: tuple[str, ...] = ()


_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}
_SOLIDWORKS_EXTENSIONS = {'.sldprt', '.sldasm', '.slddrw'}


def detect_drawing_format(filename: str, content_type: str | None, data: bytes) -> str:
    ext = Path(filename or '').suffix.lower()
    head = data[:256].lstrip()
    if data.startswith(b'%PDF-') or ext == '.pdf':
        return 'pdf'
    if ext in _IMAGE_EXTENSIONS or (content_type or '').startswith('image/'):
        return 'image'
    if ext == '.dxf' or b'AC10' in data[:128] or head.startswith(b'0\nSECTION'):
        return 'dxf'
    if ext in {'.step', '.stp'} or b'ISO-10303-21' in data[:256]:
        return 'step'
    if ext in {'.iges', '.igs'}:
        return 'iges'
    if ext == '.svg' or b'<svg' in data[:1024].lower():
        return 'svg'
    if ext in _SOLIDWORKS_EXTENSIONS:
        return 'solidworks-native'
    if ext == '.stl' or head.startswith(b'solid '):
        return 'stl'
    return 'unknown'


def choose_import_route(fmt: str) -> ImportDecision:
    routes = {
        'step': ImportDecision('step', 'cad-brep', 'very_high', True, False, ('Лучший источник для 3D-геометрии.',)),
        'iges': ImportDecision('iges', 'cad-brep', 'high', True, True, ('Проверить единицы и качество поверхностей.',)),
        'dxf': ImportDecision('dxf', 'vector-2d', 'very_high', True, True, ('Лучший источник для точного 2D-контура X/Z.',)),
        'svg': ImportDecision('svg', 'vector-2d', 'high', True, True),
        'pdf': ImportDecision('pdf', 'pdf-vector-or-vision', 'medium_to_high', True, True, ('Векторный PDF точнее скана.',)),
        'image': ImportDecision('image', 'opencv-ai-vision', 'medium', False, True, ('Нужен известный размер для калибровки.',)),
        'stl': ImportDecision('stl', 'mesh', 'medium', True, True, ('Сетка не содержит размеров и допусков.',)),
        'solidworks-native': ImportDecision('solidworks-native', 'conversion-required', 'unknown', False, True, ('Экспортируйте SLDPRT/SLDASM в STEP и SLDRAW в DXF/PDF.',)),
        'unknown': ImportDecision('unknown', 'unsupported', 'unknown', False, True),
    }
    return routes[fmt]


def _parse_ascii_dxf(data: bytes) -> dict[str, Any]:
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = data.decode('cp1251', errors='ignore')
    lines = [line.strip() for line in text.replace('\r', '').split('\n')]
    pairs: list[tuple[str, str]] = []
    for i in range(0, len(lines) - 1, 2):
        pairs.append((lines[i], lines[i + 1]))

    entities: list[dict[str, Any]] = []
    i = 0
    while i < len(pairs):
        code, value = pairs[i]
        if code == '0' and value in {'LINE', 'LWPOLYLINE'}:
            kind = value
            i += 1
            block: list[tuple[str, str]] = []
            while i < len(pairs) and pairs[i][0] != '0':
                block.append(pairs[i]); i += 1
            if kind == 'LINE':
                vals = {c: v for c, v in block}
                try:
                    entities.append({'type':'LINE','points':[{'z':float(vals['10']),'x':float(vals['20'])},{'z':float(vals['11']),'x':float(vals['21'])}]})
                except (KeyError, ValueError):
                    pass
            else:
                pts=[]; current=None
                for c,v in block:
                    if c == '10':
                        current={'z':float(v),'x':0.0}; pts.append(current)
                    elif c == '20' and current is not None:
                        current['x']=float(v)
                if len(pts) >= 2:
                    entities.append({'type':'LWPOLYLINE','points':pts})
            continue
        i += 1
    candidates=[e for e in entities if len(e['points']) >= 2]
    if not candidates:
        raise ClientValidationError('В DXF не найден LINE/LWPOLYLINE-контур. Экспортируйте профиль как полилинию без размеров и рамки.')
    best=max(candidates,key=lambda e: len(e['points']))
    return {'entities_found':len(entities),'contour_xz_mm':best['points'],'source_entity':best['type'],'confidence':'high' if best['type']=='LWPOLYLINE' else 'medium'}


def import_drawing_bytes(*, filename: str, content_type: str | None, data: bytes, page_number: int = 1, rotation: int = 0, profile_type: str = 'outer') -> dict[str, Any]:
    if not data:
        raise ClientValidationError('Файл пуст.')
    fmt=detect_drawing_format(filename, content_type, data)
    decision=choose_import_route(fmt)
    base={'filename':filename,'detected_format':fmt,'route':decision.route,'precision':decision.precision,'automatic_geometry':decision.automatic_geometry,'requires_confirmation':decision.requires_confirmation,'route_notes':list(decision.notes)}
    if fmt == 'pdf':
        return {**base,'analysis':analyze_pdf_bytes(data,page_number,rotation=rotation,profile_type=profile_type)}
    if fmt == 'image':
        return {**base,'analysis':analyze_image_bytes(data,rotation=rotation,profile_type=profile_type)}
    if fmt == 'dxf':
        return {**base,'analysis':_parse_ascii_dxf(data)}
    if fmt == 'solidworks-native':
        raise ClientValidationError('Нативный SolidWorks-файл нельзя надёжно читать без SolidWorks/Parasolid. Экспортируйте деталь в STEP, а чертёж или профиль в DXF. Это точнее, чем притворяться, будто бинарник magically понятен.')
    if fmt in {'step','iges'}:
        text=data[:4096].decode('latin1',errors='ignore')
        units='mm' if re.search(r'MILLI|\.MILLI\.',text,re.I) else 'unknown'
        return {**base,'analysis':{'cad_header_valid':fmt=='iges' or 'ISO-10303-21' in text,'units':units,'confidence':'high','status':'accepted_for_cad_kernel','message':'Файл распознан. Для извлечения B-Rep и токарного силуэта в production нужен OpenCascade/FreeCAD worker.'}}
    raise ClientValidationError(f'Формат {fmt} пока не поддерживается. Используйте STEP, DXF, PDF или изображение.')
