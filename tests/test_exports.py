"""Unit tests for the v2/v1 export wrappers (exports.py) -- no live API.

Answers requests.request (the transport's one send call) from the shared recording transport so we
verify URL construction, the per-kind -> URL mapping, and the raw-request delegation deterministically
(the one new module with logic beyond a thin URL-build-and-dispatch wrapper).
"""

import pytest
import requests
from pytest import MonkeyPatch

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
