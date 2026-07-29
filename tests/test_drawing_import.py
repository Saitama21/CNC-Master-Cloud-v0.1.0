import pytest
from app.drawing_import import detect_drawing_format, choose_import_route, import_drawing_bytes
from app.cnc_client import ClientValidationError


def test_detects_major_formats():
    assert detect_drawing_format('a.pdf','application/pdf',b'%PDF-1.7') == 'pdf'
    assert detect_drawing_format('a.step',None,b'ISO-10303-21;') == 'step'
    assert detect_drawing_format('a.sldprt',None,b'binary') == 'solidworks-native'


def test_route_prefers_step_and_dxf():
    assert choose_import_route('step').precision == 'very_high'
    assert choose_import_route('dxf').automatic_geometry is True


def test_simple_dxf_polyline():
    dxf=b'''0\nSECTION\n2\nENTITIES\n0\nLWPOLYLINE\n90\n4\n10\n0\n20\n90\n10\n-16\n20\n90\n10\n-16\n20\n125\n10\n-33\n20\n125\n0\nENDSEC\n0\nEOF\n'''
    result=import_drawing_bytes(filename='part.dxf',content_type='application/dxf',data=dxf)
    assert result['analysis']['confidence']=='high'
    assert len(result['analysis']['contour_xz_mm'])==4


def test_native_solidworks_requires_export():
    with pytest.raises(ClientValidationError, match='Экспортируйте'):
        import_drawing_bytes(filename='part.sldprt',content_type=None,data=b'binary')
