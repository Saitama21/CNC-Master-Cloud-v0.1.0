import pytest
from app.openai_drawing import _validate_result, validate_turning_contour
from app.cnc_client import ClientValidationError


def test_rejects_end_view_for_xz():
    with pytest.raises(ClientValidationError, match='торцевой вид'):
        _validate_result({'view_type':'end_view','is_valid_turning_view':False,'contour_xz_mm':[]})


def test_geometry_rejects_reverse_z():
    result=validate_turning_contour([{'x':90.0,'z':0.0},{'x':75.0,'z':-10.0},{'x':75.0,'z':-5.0}])
    assert result['valid'] is False
    assert any('обратно' in item for item in result['errors'])


def test_dual_pipeline_accepts_valid_profile():
    result=_validate_result({'view_type':'axial_section','is_valid_turning_view':True,'profile_type':'outer','confidence':'high','contour_xz_mm':[{'x':90,'z':0},{'x':90,'z':-16},{'x':75.05,'z':-16},{'x':75.05,'z':-33}]})
    assert result['geometry_validation']['valid'] is True
    assert result['view_type']=='axial_section'
