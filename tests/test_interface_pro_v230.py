from app.client_ui import CLIENT_HTML


def test_v230_pro_interface_components():
    assert "v2.3.0 PRO" in CLIENT_HTML
    assert "brandPlate" in CLIENT_HTML
    assert "ROZFOOD" in CLIENT_HTML
    assert 'id="contourTableBody"' in CLIENT_HTML
    assert 'id="contourStats"' in CLIENT_HTML
    assert "renderContourTable" in CLIENT_HTML
    assert 'data-jump="contour"' in CLIENT_HTML
