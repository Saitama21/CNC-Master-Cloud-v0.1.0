from app.catalog_data import catalog_count, search_catalog


def test_market_catalog_has_30k_positions():
    assert catalog_count() >= 30000


def test_drill_inserts_are_separate_and_searchable():
    items = search_catalog(category="drill_insert", query="SUMOCHAM")
    assert items
    assert all(i.category == "drill_insert" for i in items)


def test_legacy_ui_category_aliases_work():
    assert search_catalog(category="turning_holders", query="PCLNR")
    assert search_catalog(category="toolholding", query="ER32")
