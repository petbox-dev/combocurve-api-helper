"""Unit tests for the connection-failure policy of `base._send_request`, and for the gateway-status
retry of `APIBase._request_with_retry` -- no live API.

Every request carries a timeout. A request that never reached the server is sent again, whatever its
method; a GET/HEAD that failed after it was sent is sent again; a write that failed after it was sent is
not, because the server may have applied it.
"""

import pickle
import time
from typing import Any, cast

import pytest
import requests
import urllib3.exceptions
from pytest import MonkeyPatch

from combocurve_api_helper.base import _MAX_CONNECTION_RETRIES, _REQUEST_TIMEOUT_SECONDS, Item
from tests.http_fakes import FakeResponse, StubAuth, make_offline_api

V1 = 'https://api.combocurve.com/v1'
URL = f'{V1}/projects'


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
    # What `requests` raises for a reset: a ConnectionError wrapping urllib3's ProtocolError.
    requests.ConnectionError(urllib3.exceptions.ProtocolError('Connection aborted.', ConnectionResetError())),
    requests.ReadTimeout('read timed out'),
    requests.exceptions.ChunkedEncodingError('Connection broken: IncompleteRead'),
]
NEVER_SENT: list[requests.RequestException] = [requests.ConnectTimeout('connect timed out'), _never_sent_error()]


@pytest.mark.parametrize('error', LOST_AFTER_SEND + NEVER_SENT, ids=repr)
def test_a_get_is_sent_again_after_a_connection_failure(
    monkeypatch: MonkeyPatch, sleeps: list[float], error: requests.RequestException
) -> None:
    api = make_offline_api()
    script = _install(monkeypatch, [error, FakeResponse(200, [{'id': 'a'}])])
    assert api._get_items(URL) == [{'id': 'a'}]
    assert len(script.calls) == 2
    assert sleeps == [2.0]


def test_a_get_raises_after_the_last_retry(monkeypatch: MonkeyPatch, sleeps: list[float]) -> None:
    api = make_offline_api()
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
    api = make_offline_api()
    script = _install(monkeypatch, [error, FakeResponse(207, {})])
    with pytest.raises(type(error)):
        api._request_with_retry(method, URL, json_body=[{'name': 'a'}])
    assert len(script.calls) == 1
    assert sleeps == []


@pytest.mark.parametrize('error', NEVER_SENT, ids=repr)
def test_a_write_that_was_never_sent_is_sent_again(
    monkeypatch: MonkeyPatch, sleeps: list[float], error: requests.RequestException
) -> None:
    api = make_offline_api()
    body = {'successCount': 1, 'failedCount': 0, 'results': [{'id': 'a'}], 'generalErrors': []}
    script = _install(monkeypatch, [error, FakeResponse(207, body)])
    data: list[Item] = [{'name': 'a'}]
    assert api._post_items(URL, data) == [body]
    assert [call['json'] for call in script.calls] == [data, data]


def test_an_http_error_status_is_not_a_connection_failure(monkeypatch: MonkeyPatch, sleeps: list[float]) -> None:
    # `requests.request` returns a response for a 400; the HTTPError comes from `raise_for_status`.
    api = make_offline_api()
    script = _install(monkeypatch, [FakeResponse(400, {})])
    with pytest.raises(requests.HTTPError):
        api._get_items(URL)
    assert len(script.calls) == 1


def test_a_request_error_that_is_not_a_connection_failure_is_not_sent_again(
    monkeypatch: MonkeyPatch, sleeps: list[float]
) -> None:
    api = make_offline_api()
    script = _install(monkeypatch, [requests.exceptions.InvalidURL('bad url')])
    with pytest.raises(requests.exceptions.InvalidURL):
        api._get_items(URL)
    assert len(script.calls) == 1


def test_every_attempt_carries_the_timeout_and_fresh_auth_headers(
    monkeypatch: MonkeyPatch, sleeps: list[float]
) -> None:
    api = make_offline_api()
    script = _install(monkeypatch, [requests.ConnectTimeout('connect timed out'), FakeResponse(200, [])])
    api._get_items(URL)
    assert [call['timeout'] for call in script.calls] == [_REQUEST_TIMEOUT_SECONDS, _REQUEST_TIMEOUT_SECONDS]
    assert cast('StubAuth', api.auth).fetches == 2


def test_the_batched_write_path_uses_the_same_policy(monkeypatch: MonkeyPatch, sleeps: list[float]) -> None:
    api = make_offline_api()
    body = {'successCount': 1, 'failedCount': 0, 'results': [{'id': 'a'}], 'generalErrors': []}
    script = _install(monkeypatch, [requests.ConnectTimeout('connect timed out'), FakeResponse(207, body)])
    result = api._request_batched('post', URL, [{'name': 'a'}], chunksize=1, max_workers=1)
    assert result.success_count == 1
    assert [call['timeout'] for call in script.calls] == [_REQUEST_TIMEOUT_SECONDS, _REQUEST_TIMEOUT_SECONDS]


def test_the_batched_write_path_does_not_resend_a_write_lost_after_send(
    monkeypatch: MonkeyPatch, sleeps: list[float]
) -> None:
    api = make_offline_api()
    script = _install(monkeypatch, [requests.ReadTimeout('read timed out')])
    result = api._request_batched('post', URL, [{'name': 'a'}], chunksize=1, max_workers=1)
    assert len(script.calls) == 1
    (chunk,) = result.chunks
    assert chunk.may_have_applied
    assert chunk.failed_count == 1
    assert 'the server may have applied this chunk' in chunk.error_message
    assert not result.ok


def test_a_lost_chunk_does_not_discard_the_other_chunks_results(monkeypatch: MonkeyPatch, sleeps: list[float]) -> None:
    """The other chunks were sent and applied: their results must reach the caller."""
    api = make_offline_api()
    applied = {'successCount': 1, 'failedCount': 0, 'results': [{'id': 'x'}], 'generalErrors': []}
    outcomes = [requests.ReadTimeout('read timed out')] + [FakeResponse(207, applied) for _ in range(3)]
    script = _install(monkeypatch, outcomes)
    data: list[Item] = [{'name': f'r{i}'} for i in range(4)]
    result = api._request_batched('post', URL, data, chunksize=1, max_workers=1)
    assert len(script.calls) == 4
    assert [chunk.may_have_applied for chunk in result.chunks] == [True, False, False, False]
    assert result.success_count == 3
    assert result.failed_count == 1


def test_batch_results_stay_aligned_with_the_payload_after_a_failed_chunk(
    monkeypatch: MonkeyPatch, sleeps: list[float]
) -> None:
    """`results[i]` must describe `data[i]`: a caller picks the records to resend by position."""
    api = make_offline_api()
    applied = {'successCount': 1, 'failedCount': 0, 'results': [{'id': 'r1'}], 'generalErrors': []}
    _install(monkeypatch, [requests.ReadTimeout('read timed out'), FakeResponse(207, applied)])
    data: list[Item] = [{'name': 'r0'}, {'name': 'r1'}]
    result = api._request_batched('post', URL, data, chunksize=1, max_workers=1)
    assert len(result.results) == len(data)
    assert result.results[0]['status'] == 'ChunkFailed'
    assert result.results[0]['mayHaveApplied'] is True
    assert result.results[1] == {'id': 'r1'}


def test_the_client_can_be_pickled_and_the_copy_has_its_own_lock() -> None:
    api = make_offline_api()
    copy = pickle.loads(pickle.dumps(api))
    assert copy._auth_headers() == {}
    assert copy._auth_lock is not api._auth_lock


def test_a_batch_chunk_that_was_never_sent_is_not_marked_as_maybe_applied(
    monkeypatch: MonkeyPatch, sleeps: list[float]
) -> None:
    api = make_offline_api()
    script = _install(monkeypatch, [_never_sent_error() for _ in range(_MAX_CONNECTION_RETRIES + 1)])
    result = api._request_batched('post', URL, [{'name': 'a'}], chunksize=1, max_workers=1)
    assert len(script.calls) == _MAX_CONNECTION_RETRIES + 1
    (chunk,) = result.chunks
    assert not chunk.may_have_applied
    assert 'the chunk was not sent' in chunk.error_message


def test_a_read_only_batch_chunk_lost_after_send_is_not_marked_as_maybe_applied(
    monkeypatch: MonkeyPatch, sleeps: list[float]
) -> None:
    api = make_offline_api()
    lost = [requests.ReadTimeout(f'read timed out {i}') for i in range(_MAX_CONNECTION_RETRIES + 1)]
    script = _install(monkeypatch, lost)
    result = api._request_batched('get', URL, [{'name': 'a'}], chunksize=1, max_workers=1)
    assert len(script.calls) == _MAX_CONNECTION_RETRIES + 1  # a GET is sent again after a lost connection
    (chunk,) = result.chunks
    assert not chunk.may_have_applied
    assert 'a read-only request changes nothing on the server' in chunk.error_message


def test_the_batched_write_path_fetches_auth_headers_for_every_attempt(
    monkeypatch: MonkeyPatch, sleeps: list[float]
) -> None:
    """A batch can outlive its token (a 429 pause is 60 s); a header fetch per attempt refreshes it."""
    auth = StubAuth()
    api = make_offline_api(auth)
    body = {'successCount': 1, 'failedCount': 0, 'results': [{'id': 'a'}], 'generalErrors': []}
    _install(monkeypatch, [FakeResponse(429, {}, headers={'Retry-After': '0'}), FakeResponse(207, body)])
    api._request_batched('post', URL, [{'name': 'a'}], chunksize=1, max_workers=1)
    assert auth.fetches == 2


@pytest.mark.parametrize(('retry_after', 'expected_pause'), [('7', 7.0), ('0', 0.0), ('-1', 60.0), ('nan', 60.0)])
def test_a_rate_limited_batch_chunk_waits_for_retry_after(
    monkeypatch: MonkeyPatch, sleeps: list[float], retry_after: str, expected_pause: float
) -> None:
    api = make_offline_api()
    now = [1000.0]
    monkeypatch.setattr(time, 'monotonic', lambda: now[0])
    body = {'successCount': 1, 'failedCount': 0, 'results': [{'id': 'a'}], 'generalErrors': []}
    script = _install(
        monkeypatch, [FakeResponse(429, {}, headers={'Retry-After': retry_after}), FakeResponse(207, body)]
    )
    result = api._request_batched('post', URL, [{'name': 'a'}], chunksize=1, max_workers=1)
    assert result.ok
    assert len(script.calls) == 2
    assert sleeps == ([expected_pause] if expected_pause > 0 else [])


@pytest.mark.parametrize(('retry_after', 'expected_pause'), [('0', 0.0), ('-1', 60.0), ('inf', 60.0), ('1e10', 3600.0)])
def test_retry_after_zero_is_honoured_and_an_unusable_value_falls_back(
    monkeypatch: MonkeyPatch, sleeps: list[float], retry_after: str, expected_pause: float
) -> None:
    api = make_offline_api()
    limited = FakeResponse(429, {}, headers={'Retry-After': retry_after})
    _install(monkeypatch, [limited, FakeResponse(200, [])])
    assert api._request_with_retry('get', URL).status_code == 200
    assert sleeps == [expected_pause]


@pytest.mark.parametrize('method', ['get', 'head'])
@pytest.mark.parametrize('status', [502, 503, 504])
def test_a_read_is_sent_again_after_a_gateway_status(
    monkeypatch: MonkeyPatch, sleeps: list[float], method: str, status: int
) -> None:
    api = make_offline_api()
    script = _install(monkeypatch, [FakeResponse(status, {}), FakeResponse(200, [])])
    assert api._request_with_retry(method, URL).status_code == 200
    assert len(script.calls) == 2


@pytest.mark.parametrize('method', ['post', 'put', 'patch', 'delete'])
@pytest.mark.parametrize('status', [502, 503, 504])
def test_a_write_is_not_sent_again_after_a_gateway_status(
    monkeypatch: MonkeyPatch, sleeps: list[float], method: str, status: int
) -> None:
    api = make_offline_api()
    script = _install(monkeypatch, [FakeResponse(status, {}), FakeResponse(207, {})])
    assert api._request_with_retry(method, URL, json_body=[{'name': 'a'}]).status_code == status
    assert len(script.calls) == 1
    assert sleeps == []


@pytest.mark.parametrize('method', ['get', 'post'])
def test_a_rate_limited_request_is_sent_again_for_every_method(
    monkeypatch: MonkeyPatch, sleeps: list[float], method: str
) -> None:
    api = make_offline_api()
    limited = FakeResponse(429, {}, headers={'Retry-After': '7'})
    script = _install(monkeypatch, [limited, FakeResponse(200, [])])
    assert api._request_with_retry(method, URL).status_code == 200
    assert len(script.calls) == 2
    assert sleeps == [7.0]
