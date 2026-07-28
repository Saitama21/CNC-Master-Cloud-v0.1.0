from app.client_ui import CLIENT_HTML

def test_stainless_logo_embedded():
    assert "data:image/png;base64," in CLIENT_HTML
    assert "brandPlate:before" in CLIENT_HTML
    assert "Stainless" in CLIENT_HTML
