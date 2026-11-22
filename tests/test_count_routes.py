"""Unit tests for the HEAD `count_*` methods and the type-less econ-model by-id reads -- no live API.

Every list route has a HEAD twin that returns no body, only an `X-Query-Count` header with the
number of documents matching the url's filters (verified live 2026-09-29: `take` does not change
it, and a filter that matches nothing gives 0). These pin the verb, the url each method builds,
and that a missing header or an HTTP error raises instead of reading as a count of 0.
"""

from typing import Any

import pytest
import requests
from pytest import MonkeyPatch

from tests.http_fakes import V1, FakeResponse, RecordingTransport, install_recording_transport, make_offline_api


def _capture(monkeypatch: MonkeyPatch, response: FakeResponse, request_count: int = 1) -> RecordingTransport:
    """Answer exactly `request_count` requests with `response` (one more raises `IndexError`)."""
    return install_recording_transport(monkeypatch, *[response] * request_count)


def _sent(transport: RecordingTransport) -> list[tuple[str, str, Any]]:
    """(method, url, params) of every request the transport sent."""
    return [(call.method, call.url, call.params) for call in transport.calls]


def test_count_sends_head_and_returns_the_query_count_header(monkeypatch: MonkeyPatch) -> None:
    transport = _capture(monkeypatch, FakeResponse(headers={'X-Query-Count': '202'}))
    count = make_offline_api().count_projects({'name': 'Sample Project A'})
    assert count == 202
    assert _sent(transport) == [('HEAD', f'{V1}/projects?name=Sample%20Project%20A', None)]


def test_count_of_zero_is_returned_as_zero(monkeypatch: MonkeyPatch) -> None:
    _capture(monkeypatch, FakeResponse(headers={'X-Query-Count': '0'}))
    assert make_offline_api().count_tags() == 0


def test_missing_query_count_header_raises_instead_of_reading_as_zero(monkeypatch: MonkeyPatch) -> None:
    _capture(monkeypatch, FakeResponse(headers={}))
    with pytest.raises(ValueError, match='X-Query-Count'):
        make_offline_api().count_projects()


def test_http_error_raises(monkeypatch: MonkeyPatch) -> None:
    _capture(monkeypatch, FakeResponse(status_code=404, headers={'X-Query-Count': '5'}))
    with pytest.raises(requests.HTTPError):
        make_offline_api().count_projects()


def test_econ_run_counts_pass_filters_through_the_url_builder(monkeypatch: MonkeyPatch) -> None:
    transport = _capture(monkeypatch, FakeResponse(headers={'X-Query-Count': '3'}), request_count=3)
    api = make_offline_api()
    api.count_econ_runs('P', 'S')
    api.count_econ_runs('P', 'S', {'tags': 'a,b'})
    api.count_econ_run_monthly_exports('P', 'S', 'R', {'comboName': 'Combo 1'})
    assert [url for _, url, _ in _sent(transport)] == [
        f'{V1}/projects/P/scenarios/S/econ-runs',
        f'{V1}/projects/P/scenarios/S/econ-runs?tags=a,b',
        f'{V1}/projects/P/scenarios/S/econ-runs/R/monthly-exports?comboName=Combo%201',
    ]


def test_project_wells_list_and_count_send_the_same_filters(monkeypatch: MonkeyPatch) -> None:
    # `get_project_wells` used to accept `filters` and drop them, so it returned every well.
    transport = _capture(monkeypatch, FakeResponse(headers={'X-Query-Count': '1'}, body=[]), request_count=2)
    api = make_offline_api()
    api.get_project_wells('P', {'chosenID': 'X'})
    api.count_project_wells('P', {'chosenID': 'X'})
    assert transport.methods_and_urls == [
        ('GET', f'{V1}/projects/P/wells?chosenID=X'),
        ('HEAD', f'{V1}/projects/P/wells?chosenID=X'),
    ]


def test_generated_counts_use_the_kebab_route_for_fluid_models(monkeypatch: MonkeyPatch) -> None:
    # FluidModel is the canary: its PascalCase form is rejected on the assignment route.
    transport = _capture(monkeypatch, FakeResponse(headers={'X-Query-Count': '1'}), request_count=2)
    api = make_offline_api()
    api.count_fluid_models('P')
    api.count_fluid_assignments_by_id('P', 'M', {'scenarios': 'S'})
    assert transport.methods_and_urls == [
        ('HEAD', f'{V1}/projects/P/econ-models/fluid-models'),
        ('HEAD', f'{V1}/projects/P/econ-models/fluid-models/M/assignments?scenarios=S'),
    ]


def test_typeless_econ_model_by_id_urls() -> None:
    api = make_offline_api()
    assert api.get_econ_model_by_id_url('P', 'M') == f'{V1}/projects/P/econ-models/M'
    assert api.get_company_econ_model_by_id_url('M') == f'{V1}/econ-models/M'


def test_typeless_econ_model_by_id_returns_the_single_document(monkeypatch: MonkeyPatch) -> None:
    transport = _capture(monkeypatch, FakeResponse(body={'id': 'M', 'econModelType': 'Capex'}), request_count=2)
    api = make_offline_api()
    assert api.get_econ_model_by_id('P', 'M') == {'id': 'M', 'econModelType': 'Capex'}
    assert api.get_company_econ_model_by_id('M') == {'id': 'M', 'econModelType': 'Capex'}
    assert transport.methods_and_urls == [
        ('GET', f'{V1}/projects/P/econ-models/M'),
        ('GET', f'{V1}/econ-models/M'),
    ]
