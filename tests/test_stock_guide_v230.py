from app.client_ui import CLIENT_HTML

def test_version_and_guide_tab():
    assert 'v2.3.0' in CLIENT_HTML
    assert 'Ввод в стойку' in CLIENT_HTML
    assert 'controllerGuide' in CLIENT_HTML

def test_stock_guide_controls():
    for token in ('stockOriginZ','stockXMode','allowX','allowZ','operatorConfirmed','buildStockGuide'):
        assert token in CLIENT_HTML

def test_safety_warning():
    assert 'Rapid Override' in CLIENT_HTML
    assert 'графической симуляции' in CLIENT_HTML
