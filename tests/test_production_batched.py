"""put_project_monthly_productions_batched: the chunked, 207-preserving monthly upsert -- no live API."""

from typing import Any

import requests
from pytest import MonkeyPatch

from combocurve_api_helper import BatchWriteResult
from combocurve_api_helper.production import PUT_LIMIT
from tests.http_fakes import FakeResponse, make_offline_api


def test_put_project_monthly_productions_batched_chunks_and_preserves_the_envelope(monkeypatch: MonkeyPatch) -> None:
    api = make_offline_api()
    seen_urls: list[str] = []

    def fake_request(
        method: str, url: str, headers: Any = None, params: Any = None, json: Any = None, timeout: Any = None
    ) -> FakeResponse:
        seen_urls.append(url)
        assert method == 'put'
        n = len(json)
        return FakeResponse(
            207,
            {
                'successCount': n,
                'failedCount': 0,
                'results': [{'status': 'Success', 'well': rec['well']} for rec in json],
                'generalErrors': [],
            },
        )

    monkeypatch.setattr(requests, 'request', fake_request)

    data: list[dict[str, Any]] = [
        {'well': f'w{i}', 'date': '2026-01-15', 'oil': 1.0, 'gas': 2.0, 'water': 3.0, 'daysOn': 31} for i in range(7)
    ]
    result = api.put_project_monthly_productions_batched('000000000000000000000001', data, chunksize=3, max_workers=2)

    assert isinstance(result, BatchWriteResult)
    assert result.ok and result.success_count == 7
    assert [c.count for c in result.chunks] == [3, 3, 1]
    assert [rec['well'] for rec in result.results] == [f'w{i}' for i in range(7)]
    assert all(url.endswith('/projects/000000000000000000000001/monthly-productions') for url in seen_urls)


def test_put_project_monthly_productions_batched_defaults_to_the_put_limit(monkeypatch: MonkeyPatch) -> None:
    api = make_offline_api()
    chunk_sizes: list[int] = []

    def fake_request(
        method: str, url: str, headers: Any = None, params: Any = None, json: Any = None, timeout: Any = None
    ) -> FakeResponse:
        chunk_sizes.append(len(json))
        return FakeResponse(
            207,
            {
                'successCount': len(json),
                'failedCount': 0,
                'results': [{'status': 'Success'}] * len(json),
                'generalErrors': [],
            },
        )

    monkeypatch.setattr(requests, 'request', fake_request)

    data: list[dict[str, Any]] = [{'well': f'w{i}', 'date': '2026-01-15', 'oil': 1.0} for i in range(PUT_LIMIT + 1)]
    api.put_project_monthly_productions_batched('000000000000000000000001', data, max_workers=1)

    assert sorted(chunk_sizes) == [1, PUT_LIMIT]
