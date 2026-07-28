from app.client_ui import CLIENT_HTML


def test_v220_engineering_geometry_controls_present():
    assert "v2.3.0" in CLIENT_HTML
    assert 'id="workMode"' in CLIENT_HTML
    assert 'value="turn"' in CLIENT_HTML
    assert 'value="mill"' in CLIENT_HTML
    assert 'id="buildGeometry"' in CLIENT_HTML
    assert 'id="geoWidth"' in CLIENT_HTML
    assert 'id="geoFlat"' in CLIENT_HTML
    assert 'id="geoRadius"' in CLIENT_HTML


def test_v220_prevents_turning_gcode_for_xy_mode():
    assert "state.workMode==='mill'" in CLIENT_HTML
    assert "токарный MPF не создаётся" in CLIENT_HTML
