from app.client_ui import CLIENT_HTML
from app.cnc_client import analyze_pdf_bytes


def test_drawing_intelligence_ui_present():
    assert "v2.4.0 Drawing Intelligence" in CLIENT_HTML
    assert "dimensionReviewBody" in CLIENT_HTML
    assert "applyRecognizedDimensions" in CLIENT_HTML
    assert "application/pdf,image/png,image/jpeg,image/webp" in CLIENT_HTML


def test_dimension_review_is_operator_confirmed():
    assert "Подставить подтверждённые" in CLIENT_HTML
    assert "Ассистент не будет выдумывать" in CLIENT_HTML
