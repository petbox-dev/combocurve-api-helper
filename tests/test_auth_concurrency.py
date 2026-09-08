"""Unit test for serialised auth-header retrieval (_auth_headers) -- no live API.

`ComboCurveAuth.get_auth_headers` refreshes an expired token in place, so two threads
refreshing at once is undefined. `_request_with_retry` fetches headers through
`_auth_headers`, which holds a lock across the fetch. `aries pull` drives GETs from a
thread pool, so this guards the case where several threads hit an expired token together.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI


class _FakeResponse:
    """Minimal stand-in for requests.Response: _request_with_retry only reads status_code."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        self.headers: dict[str, str] = {}


def test_auth_headers_are_fetched_serially_under_threads(monkeypatch: MonkeyPatch) -> None:
    api = ComboCurveAPI()

    concurrent = 0
    peak = 0
    counter_lock = threading.Lock()

    def counting_get_auth_headers() -> dict[str, str]:
        nonlocal concurrent, peak
        # Count how many threads are inside this call at once. The counter lock is held only
        # for the brief increment/decrement, NOT across the sleep -- so any overlap that the
        # auth lock failed to prevent shows up as peak > 1.
        with counter_lock:
            concurrent += 1
            peak = max(peak, concurrent)
        time.sleep(0.01)
        with counter_lock:
            concurrent -= 1
        return {}

    monkeypatch.setattr(api.auth, 'get_auth_headers', counting_get_auth_headers)
    monkeypatch.setattr(requests, 'request', lambda *args, **kwargs: _FakeResponse(200))

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(api._request_with_retry, 'get', 'https://example/resource') for _ in range(8)]
        for future in futures:
            future.result()

    # With the lock the header fetch is serialised; without it up to 8 threads overlap.
    assert peak == 1
