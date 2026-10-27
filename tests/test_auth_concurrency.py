"""Unit test for serialised auth-header retrieval (_auth_headers) -- no live API.

`get_auth_headers` refreshes an expired token in place, so two threads
refreshing at once is undefined. `_request_with_retry` fetches headers through
`_auth_headers`, which holds a lock across the fetch. `aries pull` drives GETs from a
thread pool, so this guards the case where several threads hit an expired token together.
"""

import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import requests
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI, base, config
from tests.http_fakes import FakeResponse, StubAuth, make_offline_api


def test_every_constructor_sets_the_lock_the_header_fetch_needs(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """`make_offline_api` passes a stub auth, so this pins the constructors that read credentials."""
    monkeypatch.setattr(base, 'default_auth', StubAuth)
    monkeypatch.setattr(base, 'auth_from_credentials_directory', lambda directory: StubAuth())
    monkeypatch.setattr(base, 'auth_from_credentials_file', lambda path, api_key: StubAuth())
    monkeypatch.setattr(config.Configuration, 'from_file', lambda path: SimpleNamespace(apikey='key'))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        clients: list[Any] = [
            ComboCurveAPI(),
            ComboCurveAPI.from_credentials_directory(tmp_path),
            ComboCurveAPI.from_alternate_config('combocurve.json', 'cc-api.config.json'),
        ]
    for client in clients:
        assert client._auth_headers() == {}


def test_auth_headers_are_fetched_serially_under_threads(monkeypatch: MonkeyPatch) -> None:
    api = make_offline_api()

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
    monkeypatch.setattr(requests, 'request', lambda *args, **kwargs: FakeResponse(200))

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(api._request_with_retry, 'get', 'https://example/resource') for _ in range(8)]
        for future in futures:
            future.result()

    # With the lock the header fetch is serialised; without it up to 8 threads overlap.
    assert peak == 1
