from app.cnc_logic import analyze_gcode, calculate_milling, calculate_turning, capability_lines


def test_turning_calculation() -> None:
    result = calculate_turning(100, 200, 0.2)
    assert 636 < result["rpm"] < 637
    assert 127 < result["feed_mm_min"] < 128


def test_milling_calculation() -> None:
    result = calculate_milling(10, 100, 4, 0.05)
    assert 3183 < result["rpm"] < 3184
    assert 636 < result["feed_mm_min"] < 637


def test_sinumerik_g96_requires_lims() -> None:
    findings = analyze_gcode("G96 S180\nM3\nM30", "Siemens SINUMERIK 828D")
    assert any("ограничения оборотов" in item.title.lower() for item in findings)


def test_axis_capabilities() -> None:
    lines = capability_lines({"axes": "X/Z/Y/C", "machine_type": "multitasking"})
    assert any("оси C" in item for item in lines)
    assert any("по Y" in item for item in lines)
