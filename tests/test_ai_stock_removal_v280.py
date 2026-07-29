from __future__ import annotations

import base64
import io

import fitz
import numpy as np
import cv2

from app.client_ui import CLIENT_HTML
from app.cnc_client import analyze_image_bytes, analyze_pdf_bytes
from app.openai_drawing import _validate_result


def test_region_workflow_is_retained_for_ai():
    assert "regionApplied" in CLIENT_HTML
    assert "state.cropRect=state.regionApplied?{x:0,y:0,w:img.width,h:img.height}:null" in CLIENT_HTML
    assert "слишком плоский кандидат" not in CLIENT_HTML  # server diagnostic, not hard-coded UI logic
    assert "cropRect.w/state.cropRect.h<1.35" not in CLIENT_HTML


def test_raster_analysis_has_diagnostics():
    image = np.full((120, 200, 3), 255, dtype=np.uint8)
    cv2.line(image, (20, 60), (180, 60), (0, 0, 0), 2)
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    result = analyze_image_bytes(encoded.tobytes())
    assert result["autocontour_diagnostics"]["algorithm"] == "raster-preview-v1"


def test_pdf_crop_uses_only_text_in_region():
    document = fitz.open()
    page = document.new_page(width=400, height=200)
    page.insert_text((30, 50), "LEFT 125")
    page.insert_text((260, 50), "RIGHT 90")
    data = document.tobytes()
    result = analyze_pdf_bytes(data, 1, crop=(0.0, 0.0, 0.5, 1.0))
    assert "125" in result["text_preview"]
    assert "90" not in result["text_preview"]


def test_ai_contour_normalizes_front_face_and_direction():
    result = _validate_result({
        "profile_type": "outer",
        "confidence": "high",
        "contour_xz_mm": [
            {"x": 125, "z": -33},
            {"x": 125, "z": -16},
            {"x": 90, "z": -16},
            {"x": 90, "z": 0},
        ],
    })
    assert result["contour_xz_mm"] == [
        {"x": 90.0, "z": 0.0},
        {"x": 90.0, "z": -16.0},
        {"x": 125.0, "z": -16.0},
        {"x": 125.0, "z": -33.0},
    ]
    assert result["confidence"] == "high"
