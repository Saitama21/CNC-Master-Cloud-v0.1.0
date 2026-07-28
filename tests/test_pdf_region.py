from app.cnc_client import analyze_pdf_bytes


def test_pdf_analyzer_accepts_crop_and_rotation(monkeypatch):
    # Contract-level guard: public callable exposes the new safe-region arguments.
    import inspect
    params = inspect.signature(analyze_pdf_bytes).parameters
    assert {"crop", "rotation", "profile_type"}.issubset(params)
