from app.calculators import calculate
from app.catalog_data import CATEGORY_LABELS, catalog_count, get_item, search_catalog


def test_catalog_is_large_and_has_all_major_categories() -> None:
    assert catalog_count() >= 1000
    assert set(CATEGORY_LABELS) == {
        "turn_holder", "boring_bar", "turn_insert", "groove",
        "thread", "drill", "mill", "holder",
    }


def test_catalog_has_common_turning_insert() -> None:
    items = search_catalog(category="turn_insert", query="CNMG 120408")
    assert items
    assert any("CNMG" in item.code for item in items)


def test_catalog_item_keys_are_resolvable() -> None:
    item = search_catalog(category="drill")[0]
    assert get_item(item.key) == item


def test_calculators_cover_rpm_and_bolt_circle() -> None:
    assert "об/мин" in calculate("rpm", [180, 100])
    result = calculate("bolt_circle", [100, 8, 0])
    assert "08:" in result
    assert "X=50.000" in result


