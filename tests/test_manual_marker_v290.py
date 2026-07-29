from app.client_ui import CLIENT_HTML
from app.cnc_client import generate_engineering_plan


def manual_payload() -> dict:
    return {
        "telegram_id": 0,
        "machine_id": 0,
        "title": "Manual marker test",
        "machine": {"controller": "Siemens SINUMERIK 828D", "max_rpm": 3500},
        "stock": {"outer_diameter": 100, "inner_diameter": 0, "length": 60},
        "contour": {
            "mode": "outer",
            "source": "manual_marker",
            "points": [
                {"x": 80, "z": 0},
                {"x": 80, "z": -20},
                {"x": 60, "z": -20},
                {"x": 60, "z": -50},
            ],
        },
        "operations": [
            {
                "type": "turn_rough",
                "tool_no": 1,
                "tool": {"code": "MANUAL", "name": "Manual contour tool"},
                "params": {"vc": 120, "feed": 0.25, "ap": 2.0, "allow_x": 0.5},
            }
        ],
    }


def test_manual_marker_controls_are_primary_workflow() -> None:
    assert "Ручной маркер-контур" in CLIENT_HTML
    assert 'id="manualMarkerStart"' in CLIENT_HTML
    assert 'id="manualCalculate"' in CLIENT_HTML
    assert "manualXZ" in CLIENT_HTML
    assert "source:'manual_marker'" in CLIENT_HTML


def test_manual_stock_summary_is_calculated() -> None:
    result = generate_engineering_plan(manual_payload())
    summary = result["manual_stock_summary"]
    assert result["contour_source"] == "manual_marker"
    assert summary["axial_span_mm"] == 50
    assert summary["max_radial_removal_mm"] == 20
    assert summary["removal_volume_cm3"] > 0
    assert summary["rough_passes"] > 0


def test_manual_contour_keeps_vertical_shoulder() -> None:
    result = generate_engineering_plan(manual_payload())
    assert result["final_contour"][1] == {"z": -20.0, "x": 80.0}
    assert result["final_contour"][2] == {"z": -20.0, "x": 60.0}
