"""Unit tests for the v2/v1 export wrappers (exports.py) -- no live API.

Monkeypatches auth + requests.post/get so we verify URL construction, the
per-kind -> URL mapping, and the raw-request delegation deterministically
(the one new module with logic beyond a thin URL-build-and-dispatch wrapper).
"""

from typing import Any, Dict, List, Optional, Tuple

import pytest
import requests
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI

V1 = 'https://api.combocurve.com/v1'
V2 = 'https://api.combocurve.com/v2'

# export kind (URL segment) -> the snake fragment in the public method names
KINDS: Dict[str, str] = {
    'forecast-parameters': 'forecast_parameters',
    'forecast-volumes': 'forecast_volumes',
    'econ-monthly': 'econ_monthly',
    'econ-one-liners': 'econ_one_liners',
}


class _FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self._body = body
        self.headers: Dict[str, str] = {}

    def json(self) -> Any:
        return self._body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


def _make_api(monkeypatch: MonkeyPatch) -> ComboCurveAPI:
    api = ComboCurveAPI()
    monkeypatch.setattr(api.auth, 'get_auth_headers', lambda: {})
    return api


def test_export_url_builders() -> None:
    api = ComboCurveAPI()
    for kind in KINDS:
        assert api.get_v2_export_url(kind) == f'{V2}/exports/{kind}'
        assert api.get_v2_export_by_job_id_url(kind, 'JOB123') == f'{V2}/exports/{kind}/JOB123'
    assert api.get_exports_url() == f'{V1}/exports'


@pytest.mark.parametrize('kind', sorted(KINDS))
def test_post_export_hits_correct_v2_url(monkeypatch: MonkeyPatch, kind: str) -> None:
    api = _make_api(monkeypatch)
    calls: List[Tuple[str, Any]] = []

    def fake_post(url: str, headers: Any = None, json: Any = None) -> _FakeResponse:
        calls.append((url, json))
        return _FakeResponse(200, [{'id': 'JOB'}])

    monkeypatch.setattr(requests, 'post', fake_post)

    result = getattr(api, f'post_export_{KINDS[kind]}')({'scenarioId': 's'})

    assert calls == [(f'{V2}/exports/{kind}', {'scenarioId': 's'})]
    assert result == {'id': 'JOB'}


@pytest.mark.parametrize('kind', sorted(KINDS))
def test_get_export_by_job_id_hits_correct_v2_url(monkeypatch: MonkeyPatch, kind: str) -> None:
    api = _make_api(monkeypatch)
    calls: List[str] = []

    def fake_get(url: str, headers: Any = None, params: Optional[Any] = None) -> _FakeResponse:
        calls.append(url)
        return _FakeResponse(200, [{'status': 'complete'}])

    monkeypatch.setattr(requests, 'get', fake_get)

    result = getattr(api, f'get_export_{KINDS[kind]}_by_job_id')('JOB123')

    assert calls == [f'{V2}/exports/{kind}/JOB123']
    assert result == {'status': 'complete'}


def test_post_export_v1_hits_v1_url(monkeypatch: MonkeyPatch) -> None:
    api = _make_api(monkeypatch)
    calls: List[Tuple[str, Any]] = []

    def fake_post(url: str, headers: Any = None, json: Any = None) -> _FakeResponse:
        calls.append((url, json))
        return _FakeResponse(200, [{'id': 'X'}])

    monkeypatch.setattr(requests, 'post', fake_post)

    result = api.post_export({'exportType': 'x'})

    assert calls == [(f'{V1}/exports', {'exportType': 'x'})]
    assert result == {'id': 'X'}


def test_export_raises_on_http_error(monkeypatch: MonkeyPatch) -> None:
    api = _make_api(monkeypatch)
    monkeypatch.setattr(requests, 'post', lambda *a, **k: _FakeResponse(400, {}))
    with pytest.raises(requests.HTTPError):
        api.post_export_econ_monthly({})
