"""Every public type-curve and type-curve lookup-table endpoint method warns that the v1 type-curve
routes stop responding on 2026-11-07. The `*_url` builders send no request and do not warn."""

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
LOOKUP_TABLE_ID = '000000000000000000000003'
WRITE_DATA: list[dict[str, Any]] = [{'name': 'Sample Type Curve 1'}]

ENDPOINT_CALLS: dict[str, Callable[[ComboCurveAPI], object]] = {
    'post_type_curves': lambda api: api.post_type_curves(PROJECT_ID, WRITE_DATA),
    'put_type_curves': lambda api: api.put_type_curves(PROJECT_ID, WRITE_DATA),
    'delete_type_curves': lambda api: api.delete_type_curves(PROJECT_ID, id=TYPE_CURVE_ID),
    'get_type_curves': lambda api: api.get_type_curves(PROJECT_ID),
    'count_type_curves': lambda api: api.count_type_curves(PROJECT_ID),
    'get_type_curve_by_id': lambda api: api.get_type_curve_by_id(PROJECT_ID, TYPE_CURVE_ID),
    'get_type_curve_representative_fits': lambda api: api.get_type_curve_representative_fits(PROJECT_ID, TYPE_CURVE_ID),
    'get_type_curve_daily_fits': lambda api: api.get_type_curve_daily_fits(PROJECT_ID, TYPE_CURVE_ID),
    'get_type_curve_monthly_fits': lambda api: api.get_type_curve_monthly_fits(PROJECT_ID, TYPE_CURVE_ID),
    'get_type_curve_lookup_tables': lambda api: api.get_type_curve_lookup_tables(PROJECT_ID),
    'count_type_curve_lookup_tables': lambda api: api.count_type_curve_lookup_tables(PROJECT_ID),
    'get_type_curve_lookup_table_by_id': lambda api: api.get_type_curve_lookup_table_by_id(PROJECT_ID, LOOKUP_TABLE_ID),
    'post_type_curve_lookup_tables': lambda api: api.post_type_curve_lookup_tables(PROJECT_ID, WRITE_DATA),
    'put_type_curve_lookup_tables': lambda api: api.put_type_curve_lookup_tables(PROJECT_ID, WRITE_DATA),
    'delete_type_curve_lookup_table_by_id': lambda api: api.delete_type_curve_lookup_table_by_id(
        PROJECT_ID, LOOKUP_TABLE_ID
    ),
}

URL_BUILDER_CALLS: dict[str, Callable[[ComboCurveAPI], object]] = {
    'get_type_curves_url': lambda api: api.get_type_curves_url(PROJECT_ID),
    'get_type_curve_by_id_url': lambda api: api.get_type_curve_by_id_url(PROJECT_ID, TYPE_CURVE_ID),
    'get_type_curve_representative_wells_url': lambda api: api.get_type_curve_representative_wells_url(
        PROJECT_ID, TYPE_CURVE_ID
    ),
    'get_type_curve_daily_fits_url': lambda api: api.get_type_curve_daily_fits_url(PROJECT_ID, TYPE_CURVE_ID),
    'get_type_curve_monthly_fits_url': lambda api: api.get_type_curve_monthly_fits_url(PROJECT_ID, TYPE_CURVE_ID),
    'get_type_curve_lookup_tables_url': lambda api: api.get_type_curve_lookup_tables_url(PROJECT_ID),
    'get_type_curve_lookup_table_by_id_url': lambda api: api.get_type_curve_lookup_table_by_id_url(
        PROJECT_ID, LOOKUP_TABLE_ID
    ),
}


def _answer_every_request(monkeypatch: MonkeyPatch) -> None:
    """Answer every request with one item and a count header, so each method runs to completion."""

    def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
        return FakeResponse(200, [{'id': TYPE_CURVE_ID}], headers={'X-Query-Count': '1'})

    monkeypatch.setattr(requests, 'request', fake_request)


def test_every_public_endpoint_method_is_listed() -> None:
    """A type-curve endpoint method added later must be added here, so that it is checked to warn."""
    public_type_curve_methods = {
        name for name, member in vars(TypeCurves).items() if not name.startswith('_') and callable(member)
    }
    assert public_type_curve_methods == set(ENDPOINT_CALLS) | set(URL_BUILDER_CALLS)


@pytest.mark.parametrize('method_name', sorted(ENDPOINT_CALLS))
def test_endpoint_method_warns_v1_type_curves_stop(monkeypatch: MonkeyPatch, method_name: str) -> None:
    _answer_every_request(monkeypatch)
    with pytest.warns(DeprecationWarning, match=r'v1 type curves stop responding on 2026-11-07') as recorded:
        ENDPOINT_CALLS[method_name](make_offline_api())
    deprecations = [warning for warning in recorded if issubclass(warning.category, DeprecationWarning)]
    assert len(deprecations) == 1
    assert 'upgrade to combocurve-api-helper 3.0.0' in str(deprecations[0].message)
    # Attributed to the caller (this file), not to a frame inside the package.
    assert deprecations[0].filename == __file__


@pytest.mark.parametrize('method_name', sorted(URL_BUILDER_CALLS))
def test_url_builder_does_not_warn(method_name: str, recwarn: pytest.WarningsRecorder) -> None:
    URL_BUILDER_CALLS[method_name](make_offline_api())
    assert not [warning for warning in recwarn if issubclass(warning.category, DeprecationWarning)]
