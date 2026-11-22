"""put_project_monthly_productions_batched: the chunked, 207-preserving monthly upsert -- no live API."""

from typing import Any

from pytest import MonkeyPatch

from combocurve_api_helper import BatchWriteResult
from combocurve_api_helper.production import PUT_LIMIT
from tests.http_fakes import FakeResponse, RecordedCall, install_responding_transport, make_offline_api


def test_put_project_monthly_productions_batched_chunks_and_preserves_the_envelope(monkeypatch: MonkeyPatch) -> None:
    api = make_offline_api()

    def respond(call: RecordedCall) -> FakeResponse:
        record_count = len(call.body)
        return FakeResponse(
            207,
            {
                'successCount': record_count,
                'failedCount': 0,
                'results': [{'status': 'Success', 'well': record['well']} for record in call.body],
                'generalErrors': [],
            },
        )

    transport = install_responding_transport(monkeypatch, respond)

    data: list[dict[str, Any]] = [
        {'well': f'w{i}', 'date': '2026-01-15', 'oil': 1.0, 'gas': 2.0, 'water': 3.0, 'daysOn': 31} for i in range(7)
    ]
    result = api.put_project_monthly_productions_batched('000000000000000000000001', data, chunksize=3, max_workers=2)

    assert isinstance(result, BatchWriteResult)
    assert result.ok and result.success_count == 7
    assert [chunk.count for chunk in result.chunks] == [3, 3, 1]
    assert [record['well'] for record in result.results] == [f'w{i}' for i in range(7)]
    assert {call.method for call in transport.calls} == {'PUT'}
    assert all(call.url.endswith('/projects/000000000000000000000001/monthly-productions') for call in transport.calls)


def test_put_project_monthly_productions_batched_defaults_to_the_put_limit(monkeypatch: MonkeyPatch) -> None:
    api = make_offline_api()

    def respond(call: RecordedCall) -> FakeResponse:
        return FakeResponse(
            207,
            {
                'successCount': len(call.body),
                'failedCount': 0,
                'results': [{'status': 'Success'}] * len(call.body),
                'generalErrors': [],
            },
        )

    transport = install_responding_transport(monkeypatch, respond)

    data: list[dict[str, Any]] = [{'well': f'w{i}', 'date': '2026-01-15', 'oil': 1.0} for i in range(PUT_LIMIT + 1)]
    api.put_project_monthly_productions_batched('000000000000000000000001', data, max_workers=1)

    assert sorted(len(call.body) for call in transport.calls) == [1, PUT_LIMIT]
