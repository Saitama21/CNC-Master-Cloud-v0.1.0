import pytest

from app.tool_catalog import format_tool_selection, select_tool, tool_parameter_prompt


MACHINE = {
    "name": "Tengyue CK52PT-Y",
    "machine_type": "multitasking",
    "axes": "X/Z/Y/C",
    "driven_tools": True,
}


def test_rough_turning_selects_real_iso_holder() -> None:
    result = select_tool("turn_rough", "M", "100 2.0 25", MACHINE)
    assert "PCLNR 2525M12" in result.holder
    assert "CNMG 120408" in result.cutting_part
    assert "об/мин" in result.cutting_data


def test_boring_uses_requested_bar() -> None:
    result = select_tool("bore", "M", "90 45 25", MACHINE)
    assert result.holder == "S25S-SCLCR09"
    assert "CCMT" in result.cutting_part


def test_thread_parses_external_mode() -> None:
    result = select_tool("thread", "M", "16 1.5 25 ext", MACHINE)
    assert "SER 2525M16" in result.holder
    assert "16ER 1.5ISO" in result.cutting_part


def test_milling_checks_machine_and_calculates_feed() -> None:
    result = select_tool("mill", "M", "10 3 4", MACHINE)
    assert "концевая фреза Ø10" in result.cutting_part
    assert "мм/мин" in result.cutting_data
    assert not any("ось C" in warning for warning in result.warnings)


def test_invalid_parameters_raise_clear_error() -> None:
    with pytest.raises(ValueError):
        select_tool("drill", "P", "14.8", MACHINE)


def test_output_contains_safety_block() -> None:
    result = select_tool("turn_finish", "P", "80 0.3 25", MACHINE)
    text = format_tool_selection(result, "turn_finish", "C45", "P")
    assert "Single Block" in text
    assert "Стартовые режимы" in text


def test_prompt_is_operation_specific() -> None:
    assert "шаг" in tool_parameter_prompt("thread")
    assert "число_зубьев" in tool_parameter_prompt("mill")
