"""Unit tests for the batched-write driver (_request_batched) — no live API.

Monkeypatches auth + requests.request so we exercise chunking, parallel
completion, 207-envelope parsing, in-order stitching, and partial/whole-chunk
failure accounting deterministically.
"""

from typing import Any

from pytest import MonkeyPatch

import combocurve_api_helper.base as base_mod
from combocurve_api_helper import BatchWriteResult, ComboCurveAPI


class _FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self._body = body
        self.headers: dict[str, str] = {}
        self.text = str(body)

    def json(self) -> Any:
        return self._body


def _make_api(monkeypatch: MonkeyPatch) -> ComboCurveAPI:
    api = ComboCurveAPI()
    monkeypatch.setattr(api.auth, 'get_auth_headers', lambda: {})
    return api


def test_request_batched_chunks_and_stitches_207_in_order(monkeypatch: MonkeyPatch) -> None:
    api = _make_api(monkeypatch)

    def fake_request(method: str, url: str, headers: Any = None, params: Any = None, json: Any = None) -> _FakeResponse:
        n = len(json)
        return _FakeResponse(
            207,
            {
                'successCount': n,
                'failedCount': 0,
                'results': [{'status': 'Success', 'well': rec['well']} for rec in json],
                'generalErrors': [],
            },
        )

    monkeypatch.setattr(base_mod.requests, 'request', fake_request)

    data: list[dict[str, Any]] = [{'well': f'w{i}', 'phase': 'oil', 'segments': []} for i in range(60)]
    result = api._request_batched('put', 'https://x/parameters', data, chunksize=25, max_workers=4)

    assert isinstance(result, BatchWriteResult)
    assert result.success_count == 60
    assert result.failed_count == 0
    assert result.ok
    # 3 chunks of 25/25/10; results stitched back into input order despite
    # parallel (out-of-order) completion.
    assert [c.count for c in result.chunks] == [25, 25, 10]
    assert [rec['well'] for rec in result.results] == [f'w{i}' for i in range(60)]


def test_request_batched_preserves_partial_and_whole_chunk_failures(monkeypatch: MonkeyPatch) -> None:
    api = _make_api(monkeypatch)

    def fake_request(method: str, url: str, headers: Any = None, params: Any = None, json: Any = None) -> _FakeResponse:
        if json[0]['well'] == 'BAD':
            return _FakeResponse(400, {'generalErrors': [{'message': 'bad batch'}]})
        n = len(json)
        results = [{'status': 'Error' if i == 0 else 'Success'} for i in range(n)]
        return _FakeResponse(207, {'successCount': n - 1, 'failedCount': 1, 'results': results, 'generalErrors': []})

    monkeypatch.setattr(base_mod.requests, 'request', fake_request)

    # chunk 0: 25 records, 1 fails in the 207; chunk 1: 25 records, whole-chunk 400.
    data: list[dict[str, Any]] = (
        [{'well': f'w{i}'} for i in range(25)] + [{'well': 'BAD'}] + [{'well': f'x{i}'} for i in range(24)]
    )
    result = api._request_batched('put', 'https://x/parameters', data, chunksize=25, max_workers=4)

    assert not result.ok
    assert result.success_count == 24
    assert result.failed_count == 1 + 25  # 1 per-record in chunk 0, all 25 in the failed chunk 1
    assert any(c.is_chunk_failure for c in result.chunks)


def test_request_batched_empty_data(monkeypatch: MonkeyPatch) -> None:
    api = _make_api(monkeypatch)
    monkeypatch.setattr(base_mod.requests, 'request', lambda *a, **k: _FakeResponse(207, {}))
    result = api._request_batched('put', 'https://x/parameters', [], chunksize=25)
    assert result.ok
    assert result.success_count == 0
    assert result.results == []
    assert result.chunks == []


def test_request_batched_retries_transient_gateway_5xx(monkeypatch: MonkeyPatch) -> None:
    api = _make_api(monkeypatch)
    monkeypatch.setattr(base_mod.time, 'sleep', lambda _s: None)  # skip real backoff
    calls = {'n': 0}

    def fake_request(method: str, url: str, headers: Any = None, params: Any = None, json: Any = None) -> _FakeResponse:
        calls['n'] += 1
        if calls['n'] == 1:
            return _FakeResponse(503, {'error': 'temporarily unavailable'})
        n = len(json)
        return _FakeResponse(
            207, {'successCount': n, 'failedCount': 0, 'results': [{} for _ in json], 'generalErrors': []}
        )

    monkeypatch.setattr(base_mod.requests, 'request', fake_request)
    data: list[dict[str, Any]] = [{'well': f'w{i}'} for i in range(10)]
    result = api._request_batched('put', 'https://x', data, chunksize=25, max_workers=1)

    assert result.ok
    assert result.success_count == 10
    assert calls['n'] == 2  # one 503, retried, then success


def test_request_batched_does_not_retry_non_gateway_5xx(monkeypatch: MonkeyPatch) -> None:
    api = _make_api(monkeypatch)
    monkeypatch.setattr(base_mod.time, 'sleep', lambda _s: None)
    calls = {'n': 0}

    def fake_request(method: str, url: str, headers: Any = None, params: Any = None, json: Any = None) -> _FakeResponse:
        calls['n'] += 1
        return _FakeResponse(500, {'error': 'boom'})

    monkeypatch.setattr(base_mod.requests, 'request', fake_request)
    result = api._request_batched('put', 'https://x', [{'well': 'w0'}], chunksize=25, max_workers=1)

    assert not result.ok
    assert result.failed_count == 1
    assert calls['n'] == 1  # 500 is not a retryable gateway status
