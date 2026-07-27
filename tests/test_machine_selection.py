from pathlib import Path


def test_single_machine_is_not_auto_opened() -> None:
    source = (Path(__file__).resolve().parents[1] / "app/bot_main.py").read_text(encoding="utf-8")
    assert "if len(items) == 1" not in source
    assert "Выберите станок, с которым хотите работать" in source
    assert "machine:add" in source
