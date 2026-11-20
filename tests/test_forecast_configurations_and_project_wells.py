"""Offline checks for the forecast-configurations bulk DELETE and the project company-wells PATCH."""

from typing import Any

import pytest

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.forecast_configurations import ForecastConfigurations
from combocurve_api_helper.wells import POST_PATCH_PUT_LIMIT, Wells

BASE = ComboCurveAPI.API_BASE_URL


def test_bulk_delete_sends_each_id_as_a_repeated_query_parameter(monkeypatch: pytest.MonkeyPatch) -> None:
    api = ForecastConfigurations.__new__(ForecastConfigurations)
    calls: list[tuple[str, Any]] = []

    def record_delete(url: str, data: Any, chunksize: Any = None) -> list[Any]:
        calls.append((url, data))
        return [{'results': []}]

    monkeypatch.setattr(api, '_delete_items', record_delete)
    result: Any = api.delete_forecast_configurations(['c1', 'c2'])
    assert result == [{'results': []}]
    assert calls == [(f'{BASE}/forecast-configurations?id=c1&id=c2', [])]


@pytest.mark.parametrize('ids', [[], 'c1', ['c1', '']])
def test_bulk_delete_refuses_bad_ids_before_sending(monkeypatch: pytest.MonkeyPatch, ids: Any) -> None:
    api = ForecastConfigurations.__new__(ForecastConfigurations)
    calls: list[str] = []

    def refuse_delete(url: str, data: Any, chunksize: Any = None) -> list[Any]:
        calls.append(url)
        return []

    monkeypatch.setattr(api, '_delete_items', refuse_delete)
    with pytest.raises(ValueError):
        api.delete_forecast_configurations(ids)
    assert calls == []


def test_project_company_wells_patch_goes_to_the_project_route(monkeypatch: pytest.MonkeyPatch) -> None:
    api = Wells.__new__(Wells)
    calls: list[tuple[str, int, Any]] = []

    def record_patch(url: str, data: Any, chunksize: Any = None) -> list[Any]:
        calls.append((url, len(data), chunksize))
        return [{'results': []}]

    monkeypatch.setattr(api, '_patch_items', record_patch)
    body: Any = [{'id': 'w1', 'projectCustomHeader': 'x'}]
    result: Any = api.patch_project_company_wells('p1', body)
    assert result == [{'results': []}]
    assert calls == [(f'{BASE}/projects/p1/company-wells', 1, POST_PATCH_PUT_LIMIT)]
