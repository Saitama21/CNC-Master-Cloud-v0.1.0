from pathlib import Path


def test_required_files_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    required = [
        "app/api_main.py",
        "app/bot_main.py",
        "app/models.py",
        "app/catalog_data.py",
        "app/calculators.py",
        "app/usage_limits.py",
        "docker-compose.yml",
        ".env.example",
    ]
    for relative in required:
        assert (root / relative).exists(), relative
