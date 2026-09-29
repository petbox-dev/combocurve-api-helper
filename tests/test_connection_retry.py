"""Unit tests for the connection-failure policy of `base._send_request` -- no live API.

Every request carries a timeout. A request that never reached the server is sent again, whatever its
method; a GET/HEAD that failed after it was sent is sent again; a write that failed after it was sent is
not, because the server may have applied it.
"""

import threading
import time
from typing import Any, cast

import pytest
import requests
import urllib3.exceptions
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.base import _MAX_CONNECTION_RETRIES, _REQUEST_TIMEOUT_SECONDS, Item

V1 = 'https://api.combocurve.com/v1'
URL = f'{V1}/projects'


class _FakeResponse:
    """Minimal stand-in for requests.Response carrying no next-page Link header."""

    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self._body = body
        self.headers: dict[str, str] = {}
        self.text = str(body)

    def json(self) -> Any:
        return self._body

    def raise_for_status(self) -> None:
        return None


class _StubAuth:
    """Stands in for ComboCurveAuth; counts the header fetches."""

    def __init__(self) -> None:
        self.fetches = 0

    def get_auth_headers(self) -> dict[str, str]:
        self.fetches += 1
        return {}


def _make_api() -> ComboCurveAPI:
    """A client with no credentials read from disk (see `test_root_urls_and_params._make_api`)."""
    api = ComboCurveAPI.__new__(ComboCurveAPI)
    api.auth = _StubAuth()
    api._auth_lock = threading.Lock()
    return api


def _never_sent_error() -> requests.ConnectionError:
    """What `requests` raises for a refused connection or a DNS failure."""
    reason = urllib3.exceptions.NewConnectionError(cast('Any', None), 'Failed to establish a new connection')
    return requests.ConnectionError(urllib3.exceptions.MaxRetryError(cast('Any', None), URL, reason))


class _Script:
    """A fake `requests.request` that raises or returns the scripted outcomes in order."""

    def __init__(self, outcomes: list[Any]) -> None:
        self._outcomes = iter(outcomes)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, method: str, url: str, **kwargs: Any) -> Any:
        self.calls.append({'method': method, **kwargs})
        outcome = next(self._outcomes)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


@pytest.fixture
def sleeps(monkeypatch: MonkeyPatch) -> list[float]:
    """Skip the real backoff and record each pause."""
    recorded: list[float] = []
    monkeypatch.setattr(time, 'sleep', recorded.append)
    return recorded


def _install(monkeypatch: MonkeyPatch, outcomes: list[Any]) -> _Script:
    script = _Script(outcomes)
    monkeypatch.setattr(requests, 'request', script)
    return script


LOST_AFTER_SEND: list[requests.RequestException] = [
    requests.ConnectionError('Connection aborted: RemoteDisconnected'),
    requests.ReadTimeout('read timed out'),
    requests.exceptions.ChunkedEncodingError('Connection broken: IncompleteRead'),
]
NEVER_SENT: list[requests.RequestException] = [requests.ConnectTimeout('connect timed out'), _never_sent_error()]


@pytest.mark.parametrize('error', LOST_AFTER_SEND + NEVER_SENT, ids=repr)
def test_a_get_is_sent_again_after_a_connection_failure(
    monkeypatch: MonkeyPatch, sleeps: list[float], error: requests.RequestException
) -> None:
    api = _make_api()
    script = _install(monkeypatch, [error, _FakeResponse(200, [{'id': 'a'}])])
    assert api._get_items(URL) == [{'id': 'a'}]
    assert len(script.calls) == 2
    assert sleeps == [2.0]


def test_a_get_raises_after_the_last_retry(monkeypatch: MonkeyPatch, sleeps: list[float]) -> None:
    api = _make_api()
    failures = [requests.ConnectionError(f'reset {i}') for i in range(_MAX_CONNECTION_RETRIES + 1)]
    script = _install(monkeypatch, failures)
    with pytest.raises(requests.ConnectionError, match=f'reset {_MAX_CONNECTION_RETRIES}'):
        api._get_items(URL)
    assert len(script.calls) == _MAX_CONNECTION_RETRIES + 1
    assert sleeps == [2.0, 4.0]


@pytest.mark.parametrize('method', ['post', 'put', 'patch', 'delete'])
@pytest.mark.parametrize('error', LOST_AFTER_SEND, ids=repr)
def test_a_write_that_failed_after_it_was_sent_is_not_sent_again(
    monkeypatch: MonkeyPatch, sleeps: list[float], method: str, error: requests.RequestException
) -> None:
    api = _make_api()
    script = _install(monkeypatch, [error, _FakeResponse(207, {})])
    with pytest.raises(type(error)):
        api._request_with_retry(method, URL, json_body=[{'name': 'a'}])
    assert len(script.calls) == 1
    assert sleeps == []


@pytest.mark.parametrize('error', NEVER_SENT, ids=repr)
def test_a_write_that_was_never_sent_is_sent_again(
    monkeypatch: MonkeyPatch, sleeps: list[float], error: requests.RequestException
) -> None:
    api = _make_api()
    body = {'successCount': 1, 'failedCount': 0, 'results': [{'id': 'a'}], 'generalErrors': []}
    script = _install(monkeypatch, [error, _FakeResponse(207, body)])
    data: list[Item] = [{'name': 'a'}]
    assert api._post_items(URL, data) == [body]
    assert [call['json'] for call in script.calls] == [data, data]


def test_an_http_error_status_is_not_a_connection_failure(monkeypatch: MonkeyPatch, sleeps: list[float]) -> None:
    api = _make_api()
    script = _install(monkeypatch, [requests.HTTPError('400 Client Error')])
    with pytest.raises(requests.HTTPError):
        api._get_items(URL)
    assert len(script.calls) == 1


def test_every_attempt_carries_the_timeout_and_fresh_auth_headers(
    monkeypatch: MonkeyPatch, sleeps: list[float]
) -> None:
    api = _make_api()
    script = _install(monkeypatch, [requests.ConnectTimeout('connect timed out'), _FakeResponse(200, [])])
    api._get_items(URL)
    assert [call['timeout'] for call in script.calls] == [_REQUEST_TIMEOUT_SECONDS, _REQUEST_TIMEOUT_SECONDS]
    assert cast('_StubAuth', api.auth).fetches == 2


def test_the_batched_write_path_uses_the_same_policy(monkeypatch: MonkeyPatch, sleeps: list[float]) -> None:
    api = _make_api()
    body = {'successCount': 1, 'failedCount': 0, 'results': [{'id': 'a'}], 'generalErrors': []}
    script = _install(monkeypatch, [requests.ConnectTimeout('connect timed out'), _FakeResponse(207, body)])
    result = api._request_batched('post', URL, [{'name': 'a'}], chunksize=1, max_workers=1)
    assert result.success_count == 1
    assert [call['timeout'] for call in script.calls] == [_REQUEST_TIMEOUT_SECONDS, _REQUEST_TIMEOUT_SECONDS]


def test_the_batched_write_path_does_not_resend_a_write_lost_after_send(
    monkeypatch: MonkeyPatch, sleeps: list[float]
) -> None:
    api = _make_api()
    script = _install(monkeypatch, [requests.ReadTimeout('read timed out')])
    with pytest.raises(requests.ReadTimeout):
        api._request_batched('post', URL, [{'name': 'a'}], chunksize=1, max_workers=1)
    assert len(script.calls) == 1
