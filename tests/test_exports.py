"""Unit tests for the v2/v1 export wrappers (exports.py) -- no live API.

Answers requests.request (the transport's one send call) from the shared recording transport so we
verify URL construction, the per-kind -> URL mapping, and the raw-request delegation deterministically
(the one new module with logic beyond a thin URL-build-and-dispatch wrapper).
"""

import time

import pytest
import requests
from pytest import MonkeyPatch

from combocurve_api_helper.exports import EXPORT_POLL_SECONDS, EXPORT_WAIT_TIMEOUT_SECONDS
from tests.http_fakes import V1, V2, FakeResponse, install_recording_transport, make_offline_api

# export kind (URL segment) -> the snake fragment in the public method names
KINDS: dict[str, str] = {
    'forecast-parameters': 'forecast_parameters',
    'forecast-volumes': 'forecast_volumes',
    'econ-monthly': 'econ_monthly',
    'econ-one-liners': 'econ_one_liners',
}


def test_export_url_builders() -> None:
    api = make_offline_api()
    for kind in KINDS:
        assert api.get_v2_export_url(kind) == f'{V2}/exports/{kind}'
        assert api.get_v2_export_by_job_id_url(kind, 'JOB123') == f'{V2}/exports/{kind}/JOB123'
    assert api.get_exports_url() == f'{V1}/exports'


@pytest.mark.parametrize('kind', sorted(KINDS))
def test_post_export_hits_correct_v2_url(monkeypatch: MonkeyPatch, kind: str) -> None:
    api = make_offline_api()
    transport = install_recording_transport(monkeypatch, FakeResponse(200, [{'id': 'JOB'}]))

    result = getattr(api, f'post_export_{KINDS[kind]}')({'scenarioId': 's'})

    assert [(call.method, call.url, call.body) for call in transport.calls] == [
        ('POST', f'{V2}/exports/{kind}', {'scenarioId': 's'})
    ]
    assert result == {'id': 'JOB'}


@pytest.mark.parametrize('kind', sorted(KINDS))
def test_get_export_by_job_id_hits_correct_v2_url(monkeypatch: MonkeyPatch, kind: str) -> None:
    api = make_offline_api()
    transport = install_recording_transport(monkeypatch, FakeResponse(200, [{'status': 'complete'}]))

    result = getattr(api, f'get_export_{KINDS[kind]}_by_job_id')('JOB123')

    assert transport.methods_and_urls == [('GET', f'{V2}/exports/{kind}/JOB123')]
    assert result == {'status': 'complete'}


def test_post_export_v1_hits_v1_url(monkeypatch: MonkeyPatch) -> None:
    api = make_offline_api()
    transport = install_recording_transport(monkeypatch, FakeResponse(200, [{'id': 'X'}]))

    result = api.post_export({'exportType': 'x'})

    assert [(call.method, call.url, call.body) for call in transport.calls] == [
        ('POST', f'{V1}/exports', {'exportType': 'x'})
    ]
    assert result == {'id': 'X'}


def test_export_raises_on_http_error(monkeypatch: MonkeyPatch) -> None:
    api = make_offline_api()
    install_recording_transport(monkeypatch, FakeResponse(400, {}))
    with pytest.raises(requests.HTTPError):
        api.post_export_econ_monthly({})


# export kind -> the status of a finished good job, seen live 2026-11-22
GOOD_STATUS: dict[str, str] = {
    'forecast-parameters': 'successful',
    'forecast-volumes': 'successful',
    'econ-monthly': 'complete',
    'econ-one-liners': 'complete',
}


@pytest.mark.parametrize('kind', sorted(KINDS))
def test_wait_for_export_polls_the_job_route_until_it_finishes(monkeypatch: MonkeyPatch, kind: str) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, 'sleep', sleeps.append)
    transport = install_recording_transport(
        monkeypatch,
        FakeResponse(200, {'status': 'pending', 'runDate': 'd', 'result': {}}),
        FakeResponse(200, {'status': 'running', 'runDate': 'd', 'result': {}}),
        FakeResponse(200, {'status': GOOD_STATUS[kind], 'runDate': 'd', 'result': {'fileUrls': ['u']}}),
    )

    job = getattr(make_offline_api(), f'wait_for_export_{KINDS[kind]}')('JOB123', poll_seconds=1.5)

    assert job['status'] == GOOD_STATUS[kind]
    assert job['result'] == {'fileUrls': ['u']}
    assert transport.methods_and_urls == [('GET', f'{V2}/exports/{kind}/JOB123')] * 3
    assert sleeps == [1.5, 1.5]


@pytest.mark.parametrize('kind', sorted(KINDS))
def test_wait_for_export_returns_a_failed_job(monkeypatch: MonkeyPatch, kind: str) -> None:
    monkeypatch.setattr(time, 'sleep', lambda seconds: None)
    failed = {'status': 'failed', 'runDate': 'd', 'result': {'error': 'Job JOB123 not found'}}
    transport = install_recording_transport(
        monkeypatch, FakeResponse(200, {'status': 'running', 'result': {}}), FakeResponse(200, failed)
    )

    job = getattr(make_offline_api(), f'wait_for_export_{KINDS[kind]}')('JOB123')

    assert job == failed
    assert len(transport.calls) == 2


@pytest.mark.parametrize('kind', sorted(KINDS))
def test_wait_for_export_raises_at_the_timeout(monkeypatch: MonkeyPatch, kind: str) -> None:
    monkeypatch.setattr(time, 'sleep', lambda seconds: None)
    install_recording_transport(monkeypatch, FakeResponse(200, {'status': 'pending', 'result': {}}))

    with pytest.raises(TimeoutError, match=f"{kind} export job JOB123 is still 'pending' after 0.0 seconds"):
        getattr(make_offline_api(), f'wait_for_export_{KINDS[kind]}')('JOB123', timeout_seconds=0.0, poll_seconds=1.0)


def test_wait_for_export_defaults_outlast_the_server_ten_minute_limit() -> None:
    assert EXPORT_WAIT_TIMEOUT_SECONDS > 600
    assert EXPORT_POLL_SECONDS == 2.0
