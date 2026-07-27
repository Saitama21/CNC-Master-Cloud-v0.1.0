from app.cnc_client import generate_engineering_plan, normalize_contour, spindle_rpm


def base_payload():
    return {
        "telegram_id": 123,
        "machine_id": 1,
        "title": "Test shaft",
        "machine": {"controller": "Siemens SINUMERIK 828D", "max_rpm": 3000},
        "stock": {"outer_diameter": 80, "inner_diameter": 0, "length": 60},
        "contour": {
            "mode": "outer",
            "points": [
                {"z": 0, "x": 70},
                {"z": -20, "x": 70},
                {"z": -25, "x": 50},
                {"z": -55, "x": 50},
            ],
        },
        "operations": [
            {
                "type": "turn_rough",
                "tool_no": 1,
                "tool": {"code": "PCLNR 2525M12", "name": "Наружная державка"},
                "params": {"vc": 120, "feed": 0.25, "ap": 2, "allow_x": 0.5},
            },
            {
                "type": "turn_finish",
                "tool_no": 2,
                "tool": {"code": "SVJBR 2020K16", "name": "Чистовая державка"},
                "params": {"vc": 160, "feed": 0.1, "ap": 0.3},
            },
        ],
    }


def test_contour_is_sorted_from_front_to_back():
    points = normalize_contour([{"z": -20, "x": 40}, {"z": 0, "x": 60}])
    assert points[0].z == 0
    assert points[-1].z == -20


def test_spindle_rpm_respects_limit():
    assert spindle_rpm(300, 10, 2500) == 2500


def test_generate_plan_has_stock_removal_and_gcode():
    result = generate_engineering_plan(base_payload())
    assert result["summary"]["operations"] == 2
    assert result["summary"]["stock_removal_cycles"] == 1
    assert "G18 G40 G90 G95" in result["gcode"]
    assert "PCLNR 2525M12" in result["gcode"]
    assert result["toolpaths"]


def test_finish_path_matches_final_contour():
    result = generate_engineering_plan(base_payload())
    finish = [p for p in result["toolpaths"] if p["operation"] == "turn_finish"][0]
    assert finish["points"] == result["final_contour"]
