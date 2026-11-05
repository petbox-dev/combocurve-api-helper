"""The single-object endpoints send through `APIBase._request_with_retry`, so they get the request
timeout, the 429 retry, the GET/HEAD-only gateway retry and the never-sent connection retry.

Until 3.0.0 / 2.7.1 these eight call sites called `requests.get/post/put/patch` directly: no
timeout, no retry. A stalled connection blocked the call forever
(docs/todo/closed/direct-requests-calls-bypass-timeout-and-retry.md).
"""

from collections.abc import Callable
from typing import Any

import pytest
import requests
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.base import _REQUEST_TIMEOUT_SECONDS
from tests.http_fakes import FakeResponse, make_offline_api

PROJECT_ID = '000000000000000000000001'
FORECAST_ID = '000000000000000000000002'
SURVEY_ID = '000000000000000000000003'
JOB_ID = '000000000000000000000004'
BODY: dict[str, Any] = {'name': 'Sample'}

# method name -> (call, expected verb, expected url suffix, expected json body)
SINGLE_OBJECT_CALLS: dict[str, tuple[Callable[[ComboCurveAPI], object], str, str, Any]] = {
    'post_directional_surveys': (
        lambda api: api.post_directional_surveys(BODY),
        'POST',
        '/v1/directional-surveys',
        BODY,
    ),
    'put_directional_survey_by_id': (
        lambda api: api.put_directional_survey_by_id(SURVEY_ID, BODY),
        'PUT',
        f'/v1/directional-surveys/{SURVEY_ID}',
        BODY,
    ),
    '_post_v2_export': (
        lambda api: api._post_v2_export('forecast-parameters', BODY),
        'POST',
        '/v2/exports/forecast-parameters',
        BODY,
    ),
    '_get_v2_export': (
        lambda api: api._get_v2_export('forecast-parameters', JOB_ID),
        'GET',
        f'/v2/exports/forecast-parameters/{JOB_ID}',
        None,
    ),
    'post_export': (
        lambda api: api.post_export(BODY),
        'POST',
        '/v1/exports',
        BODY,
    ),
    'patch_forecast_by_id': (
        lambda api: api.patch_forecast_by_id(PROJECT_ID, FORECAST_ID, BODY),
        'PATCH',
        f'/v1/projects/{PROJECT_ID}/forecasts/{FORECAST_ID}',
        BODY,
    ),
    'post_forecast_run': (
        lambda api: api.post_forecast_run(PROJECT_ID, FORECAST_ID, 'configuration'),
        'POST',
        f'/v1/projects/{PROJECT_ID}/forecasts/{FORECAST_ID}/run',
        {'configurationId': 'configuration'},
    ),
}


class _Recorder:
    """Stands in for `requests.request`; keeps every call with its timeout."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self, method: str, url: str, headers: Any = None, params: Any = None, json: Any = None, timeout: Any = None
    ) -> FakeResponse:
        self.calls.append({'method': method.upper(), 'url': url, 'json': json, 'timeout': timeout})
        return FakeResponse(200, {'id': JOB_ID})


def _install(monkeypatch: MonkeyPatch) -> _Recorder:
    recorder = _Recorder()
    monkeypatch.setattr(requests, 'request', recorder)

    def direct_call(*arguments: Any, **keywords: Any) -> None:
        raise AssertionError('a direct requests.get/post/put/patch call bypasses the transport')

    for verb in ('get', 'post', 'put', 'patch'):
        monkeypatch.setattr(requests, verb, direct_call)
    return recorder


@pytest.mark.parametrize('method_name', sorted(SINGLE_OBJECT_CALLS))
def test_single_object_call_goes_through_the_transport(monkeypatch: MonkeyPatch, method_name: str) -> None:
    recorder = _install(monkeypatch)
    call, verb, url_suffix, body = SINGLE_OBJECT_CALLS[method_name]

    call(make_offline_api())

    assert len(recorder.calls) == 1
    sent = recorder.calls[0]
    assert sent['method'] == verb
    assert sent['url'].endswith(url_suffix)
    assert sent['json'] == body
    assert sent['timeout'] == _REQUEST_TIMEOUT_SECONDS


def test_post_forecast_wells_sends_each_chunk_through_the_transport(monkeypatch: MonkeyPatch) -> None:
    recorder = _install(monkeypatch)

    make_offline_api().post_forecast_wells(PROJECT_ID, FORECAST_ID, ['w1', 'w2', 'w3'], chunksize=2)

    assert [call['json'] for call in recorder.calls] == [{'wellIds': ['w1', 'w2']}, {'wellIds': ['w3']}]
    assert all(call['method'] == 'POST' and call['timeout'] == _REQUEST_TIMEOUT_SECONDS for call in recorder.calls)


def test_a_get_is_sent_again_after_a_gateway_timeout(monkeypatch: MonkeyPatch) -> None:
    """The export status poll is a GET, so a 504 is retried (writes are not)."""
    responses = [FakeResponse(504, {'message': 'gateway'}), FakeResponse(200, {'status': 'complete'})]
    calls: list[str] = []

    def answer(method: str, url: str, **keywords: Any) -> FakeResponse:
        calls.append(method.upper())
        return responses.pop(0)

    monkeypatch.setattr(requests, 'request', answer)
    monkeypatch.setattr('time.sleep', lambda seconds: None)

    result = make_offline_api()._get_v2_export('forecast-parameters', JOB_ID)

    assert calls == ['GET', 'GET']
    assert result == {'status': 'complete'}
