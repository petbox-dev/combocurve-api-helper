"""From 3.0.0 the type-curve methods use the v2 routes and do not warn; the deprecated v1 wrappers live in
type_curves_v1_compatibility.py and are tested in tests/type_curves/test_v1_compatibility.py."""

import warnings
from collections.abc import Callable
from typing import Any

import pytest
import requests
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.typecurves import TypeCurves
from tests.http_fakes import FakeResponse, make_offline_api

PROJECT_ID = '000000000000000000000001'
TYPE_CURVE_ID = '000000000000000000000002'
WRITE_ITEM: dict[str, Any] = {'name': 'Sample Type Curve 1'}
WRITE_DATA: list[dict[str, Any]] = [WRITE_ITEM]

ENDPOINT_CALLS: dict[str, Callable[[ComboCurveAPI], object]] = {
    'get_type_curves': lambda api: api.get_type_curves(PROJECT_ID),
    'count_type_curves': lambda api: api.count_type_curves(PROJECT_ID),
    'get_type_curve_by_id': lambda api: api.get_type_curve_by_id(PROJECT_ID, TYPE_CURVE_ID),
    'post_type_curve': lambda api: api.post_type_curve(PROJECT_ID, WRITE_ITEM),
    'post_type_curves': lambda api: api.post_type_curves(PROJECT_ID, WRITE_DATA),
    'patch_type_curve': lambda api: api.patch_type_curve(PROJECT_ID, TYPE_CURVE_ID, WRITE_ITEM),
    'patch_type_curves': lambda api: api.patch_type_curves(PROJECT_ID, WRITE_DATA),
    'delete_type_curves': lambda api: api.delete_type_curves(PROJECT_ID, id=TYPE_CURVE_ID),
    'delete_type_curve_by_id': lambda api: api.delete_type_curve_by_id(PROJECT_ID, TYPE_CURVE_ID),
    'get_type_curve_fits': lambda api: api.get_type_curve_fits(PROJECT_ID, TYPE_CURVE_ID),
    'put_type_curve_fits': lambda api: api.put_type_curve_fits(PROJECT_ID, TYPE_CURVE_ID, WRITE_ITEM),
    'get_type_curve_normalization': lambda api: api.get_type_curve_normalization(PROJECT_ID, TYPE_CURVE_ID),
    'put_type_curve_normalization': lambda api: api.put_type_curve_normalization(PROJECT_ID, TYPE_CURVE_ID, WRITE_ITEM),
    'get_type_curve_volumes': lambda api: api.get_type_curve_volumes(PROJECT_ID, TYPE_CURVE_ID, 'daily'),
    'get_type_curve_wells': lambda api: api.get_type_curve_wells(PROJECT_ID, TYPE_CURVE_ID),
    'count_type_curve_wells': lambda api: api.count_type_curve_wells(PROJECT_ID, TYPE_CURVE_ID),
}


def _answer_every_request(monkeypatch: MonkeyPatch) -> None:
    """Answer every request with a 200 and a count header, so each method runs to completion."""

    def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
        return FakeResponse(200, [{'id': TYPE_CURVE_ID}], headers={'X-Query-Count': '1'})

    monkeypatch.setattr(requests, 'request', fake_request)


def test_every_public_endpoint_method_is_listed() -> None:
    """An endpoint method added later must be added here, so that it is checked not to warn."""
    public_endpoint_methods = {
        name
        for name, member in TypeCurves.__dict__.items()
        if not name.startswith('_') and not name.endswith('_url') and callable(member)
    }
    assert public_endpoint_methods == set(ENDPOINT_CALLS)


@pytest.mark.parametrize('method_name', sorted(ENDPOINT_CALLS))
def test_endpoint_method_does_not_warn(monkeypatch: MonkeyPatch, method_name: str) -> None:
    _answer_every_request(monkeypatch)
    with warnings.catch_warnings():
        warnings.simplefilter('error', DeprecationWarning)
        ENDPOINT_CALLS[method_name](make_offline_api())
