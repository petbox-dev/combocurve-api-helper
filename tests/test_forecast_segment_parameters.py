"""Offline tests for the forecast segment-parameter writes and the forecast deletes (live findings 2026-11-22)."""

import pytest

from combocurve_api_helper.base import Item
from combocurve_api_helper.forecasts import Forecasts
from tests.http_fakes import FakeResponse, StubAuth, install_recording_transport

BASE = Forecasts.API_BASE_URL
SEGMENT_URL = f'{BASE}/projects/p1/forecasts/f1/parameters/w1/oil/best'

# A linear segment as the route takes it: `slope` is the VALUE in rate units per day, and
# qEnd = qStart + slope * (endDate - startDate in days). 100 + 10 * 30 = 400.
LINEAR_SEGMENT: Item = {
    'segmentType': 'linear',
    'startDate': '2025-01-01',
    'endDate': '2025-01-31',
    'qStart': 100.0,
    'qEnd': 400.0,
    'slope': 10.0,
}


@pytest.mark.parametrize('method_name', ['post_forecast_segment_parameters', 'put_forecast_segment_parameters'])
def test_segment_parameter_write_sends_the_slope_value_unchanged(
    monkeypatch: pytest.MonkeyPatch, method_name: str
) -> None:
    # The route reads `slope` as the value and rejects `slopeValue` (verified live 2026-11-22 on dev), so the
    # helper must not turn the value into the sign that the output read carries in `slope`.
    transport = install_recording_transport(
        monkeypatch, FakeResponse(201, {'status': 'Created', 'segmentsCount': 1, 'id': 'o1'})
    )

    method = getattr(Forecasts(auth=StubAuth()), method_name)
    responses = method('p1', 'f1', 'w1', 'oil', 'best', [LINEAR_SEGMENT])

    assert responses == [{'status': 'Created', 'segmentsCount': 1, 'id': 'o1'}]
    assert [(call.method, call.url, call.body) for call in transport.calls] == [
        (method_name.split('_')[0].upper(), SEGMENT_URL, [LINEAR_SEGMENT])
    ]


def test_segment_parameter_delete_returns_the_headers_of_an_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    # The route answers a success with 204 and an empty body (verified live 2026-11-22 on dev); reading that
    # body as JSON raised after the segments were already deleted.
    transport = install_recording_transport(monkeypatch, FakeResponse(204, text=''))

    headers = Forecasts(auth=StubAuth()).delete_forecast_segment_parameters('p1', 'f1', 'w1', 'oil', 'best')

    assert dict(headers) == {}
    assert [(call.method, call.url, call.body) for call in transport.calls] == [('DELETE', SEGMENT_URL, None)]


def test_forecast_delete_by_id_returns_the_headers_of_an_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    # Same empty-body success as the segment delete (verified live 2026-11-22 on dev).
    transport = install_recording_transport(monkeypatch, FakeResponse(204, text='', headers={'X-Delete-Count': '1'}))

    headers = Forecasts(auth=StubAuth()).delete_forecast_by_id('p1', 'f1')

    assert headers['x-delete-count'] == '1'
    assert [(call.method, call.url, call.body) for call in transport.calls] == [
        ('DELETE', f'{BASE}/projects/p1/forecasts/f1', None)
    ]
