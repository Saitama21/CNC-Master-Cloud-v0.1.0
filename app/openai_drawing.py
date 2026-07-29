from __future__ import annotations

import json
import os
import re
from typing import Any

import aiohttp

from app.cnc_client import ClientValidationError


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise ClientValidationError("OpenAI не вернул корректный JSON.")
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ClientValidationError("Ответ OpenAI имеет неверный формат.")
    return value


def _validate_result(data: dict[str, Any]) -> dict[str, Any]:
    points = data.get("contour_xz_mm") or []
    clean: list[dict[str, float]] = []
    if isinstance(points, list):
        for item in points[:240]:
            if not isinstance(item, dict):
                continue
            try:
                x = float(item["x"])
                z = float(item["z"])
            except (KeyError, TypeError, ValueError):
                continue
            if not (-100000 <= x <= 100000 and -100000 <= z <= 100000):
                continue
            clean.append({"x": round(x, 4), "z": round(z, 4)})
    if len(clean) < 2:
        raise ClientValidationError(
            "OpenAI не смог построить надёжный размерный контур. Проверьте, что в области видны профиль и размеры."
        )
    # Remove immediate duplicates, which models occasionally produce for vertical steps.
    deduped: list[dict[str, float]] = []
    for p in clean:
        if not deduped or abs(p["x"] - deduped[-1]["x"]) > 1e-6 or abs(p["z"] - deduped[-1]["z"]) > 1e-6:
            deduped.append(p)
    confidence = str(data.get("confidence", "low")).lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"
    return {
        "contour_xz_mm": deduped,
        "stock_diameter_mm": _safe_positive(data.get("stock_diameter_mm")),
        "stock_length_mm": _safe_positive(data.get("stock_length_mm")),
        "profile_type": str(data.get("profile_type", "outer")),
        "confidence": confidence,
        "dimensions": data.get("dimensions") if isinstance(data.get("dimensions"), list) else [],
        "warnings": data.get("warnings") if isinstance(data.get("warnings"), list) else [],
        "questions": data.get("questions") if isinstance(data.get("questions"), list) else [],
        "summary": str(data.get("summary", ""))[:1200],
        "model": os.getenv("OPENAI_DRAWING_MODEL", "gpt-5"),
    }


def _safe_positive(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 4) if 0 < number <= 100000 else None


async def analyze_drawing_region_with_openai(
    image_data_url: str,
    *,
    profile_type: str = "outer",
    x_mode: str = "diameter",
) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ClientValidationError("На Railway не задана переменная OPENAI_API_KEY.")
    model = os.getenv("OPENAI_DRAWING_MODEL", "gpt-5").strip() or "gpt-5"
    prompt = f"""
Ты инженер по токарной обработке и читаешь только выделенную область машиностроительного чертежа.
Нужно восстановить профиль для SINUMERIK Stock Removal.
Режим профиля: {profile_type}. Координата X должна быть в режиме: {x_mode}.

Правила:
1. Не учитывай размерные линии, стрелки, штриховку, осевые, текст, рамку и скрытые линии как профиль детали.
2. Начальная точка контура должна быть на торце Z=0. Вглубь детали Z идёт в минус.
3. Для токарного профиля X является диаметром, если x_mode=diameter, иначе радиусом.
4. Используй только явно читаемые размеры. Ничего не выдумывай.
5. Сохраняй ступени двумя точками с одинаковым Z, фаски и конусы отдельными конечными точками.
6. Если размерный масштаб определить нельзя, не создавай ложный контур: укажи вопрос в questions.
7. Верни только JSON без markdown.

Формат:
{{
  "profile_type":"outer|inner",
  "confidence":"high|medium|low",
  "stock_diameter_mm": number|null,
  "stock_length_mm": number|null,
  "contour_xz_mm":[{{"x":number,"z":number}}],
  "dimensions":[{{"raw":"Ø130","kind":"diameter","value":130,"confidence":0.95}}],
  "summary":"краткое описание",
  "warnings":["что проверить"],
  "questions":["какого размера не хватает"]
}}
""".strip()
    payload = {
        "model": model,
        "input": [{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": image_data_url, "detail": "high"},
            ],
        }],
    }
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        ) as response:
            body = await response.text()
            if response.status >= 400:
                try:
                    detail = json.loads(body).get("error", {}).get("message", body)
                except Exception:
                    detail = body
                raise ClientValidationError(f"Ошибка OpenAI API: {str(detail)[:500]}")
    raw = json.loads(body)
    output_text = raw.get("output_text")
    if not output_text:
        chunks: list[str] = []
        for item in raw.get("output", []):
            for content in item.get("content", []) if isinstance(item, dict) else []:
                if isinstance(content, dict) and content.get("type") == "output_text":
                    chunks.append(str(content.get("text", "")))
        output_text = "".join(chunks)
    return _validate_result(_extract_json(str(output_text or "")))
