from pathlib import Path


def test_ai_region_files_and_route_exist():
    root = Path(__file__).resolve().parents[1]
    api = (root / "app/api_main.py").read_text()
    ui = (root / "app/client_ui.py").read_text()
    provider = (root / "app/openai_drawing.py").read_text()
    assert '/api/v1/client/ai/region' in api
    assert 'aiBuildRegion' in ui
    assert 'OPENAI_API_KEY' in provider
    assert 'input_image' in provider
    assert 'contour_xz_mm' in provider


def test_operator_confirmation_remains_required():
    root = Path(__file__).resolve().parents[1]
    ui = (root / "app/client_ui.py").read_text()
    assert "$('operatorConfirmed').checked=false" in ui
    assert "if(!$('operatorConfirmed').checked)" in ui
