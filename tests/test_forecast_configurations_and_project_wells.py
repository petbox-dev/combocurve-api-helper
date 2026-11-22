"""Offline checks for the forecast-configurations bulk DELETE and the project company-wells PATCH."""

from typing import Any

import pytest

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.wells import POST_PATCH_PUT_LIMIT
from tests.http_fakes import FakeResponse, install_recording_transport, make_offline_api

BASE = ComboCurveAPI.API_BASE_URL


def test_bulk_delete_sends_each_id_as_a_repeated_query_parameter(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(200, [{'results': []}]))
    result: Any = make_offline_api().delete_forecast_configurations(['c1', 'c2'])
    assert result == [{'results': []}]
    assert [(call.method, call.url, call.body) for call in transport.calls] == [
        ('DELETE', f'{BASE}/forecast-configurations?id=c1&id=c2', None)
    ]


@pytest.mark.parametrize('ids', [[], 'c1', ['c1', '']])
def test_bulk_delete_refuses_bad_ids_before_sending(monkeypatch: pytest.MonkeyPatch, ids: Any) -> None:
    transport = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError):
        make_offline_api().delete_forecast_configurations(ids)
    assert transport.calls == []


def test_project_company_wells_patch_goes_to_the_project_route(monkeypatch: pytest.MonkeyPatch) -> None:
    """A body longer than `POST_PATCH_PUT_LIMIT` goes in requests of at most that many records."""
    transport = install_recording_transport(
        monkeypatch, FakeResponse(207, [{'results': ['first']}]), FakeResponse(207, [{'results': ['second']}])
    )
    body: Any = [{'id': f'w{i}', 'projectCustomHeader': 'x'} for i in range(POST_PATCH_PUT_LIMIT + 1)]
    result: Any = make_offline_api().patch_project_company_wells('p1', body)
    assert result == [{'results': ['first']}, {'results': ['second']}]
    assert [(call.method, call.url, len(call.body)) for call in transport.calls] == [
        ('PATCH', f'{BASE}/projects/p1/company-wells', POST_PATCH_PUT_LIMIT),
        ('PATCH', f'{BASE}/projects/p1/company-wells', 1),
    ]
    assert [record for call in transport.calls for record in call.body] == body


def test_bulk_delete_splits_more_than_100_ids_into_requests_of_100(monkeypatch: pytest.MonkeyPatch) -> None:
    """The route answers 500 for 101 ids (dev, 2026-11-21), so a longer list goes in batches of 100."""
    transport = install_recording_transport(
        monkeypatch, FakeResponse(200, [{'results': []}]), FakeResponse(200, [{'results': []}])
    )
    ids = [f'c{i}' for i in range(150)] + ['c0']
    result: Any = make_offline_api().delete_forecast_configurations(ids)
    assert [call.url.count('id=') for call in transport.calls] == [100, 50]
    assert len(result) == 2


def test_project_company_wells_patch_refuses_empty_data(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError, match='at least one well record'):
        make_offline_api().patch_project_company_wells('p1', [])
    assert transport.calls == []
