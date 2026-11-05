"""Native v2 type-curve lookup-table methods. No network."""

from typing import TYPE_CHECKING, Any

import requests
from pytest import MonkeyPatch

from tests.http_fakes import FakeResponse, make_offline_api
from tests.type_curves.transport import RecordingTransport

if TYPE_CHECKING:
    from combocurve_api_helper.base import Item

PROJECT_ID = '000000000000000000000001'
TABLE_ID = '000000000000000000000003'
BASE = f'https://api.combocurve.com/v2/projects/{PROJECT_ID}/type-curves/lookup-tables'
ENVELOPE: dict[str, Any] = {'successCount': 1, 'failedCount': 0, 'results': [{'status': 'OK', 'code': 200}]}
TABLE: 'Item' = {'name': 'Sample Table', 'rules': [{'filter': [], 'riskFactorPeakOil': 1}]}


def install(monkeypatch: MonkeyPatch, *responses: FakeResponse) -> RecordingTransport:
    transport = RecordingTransport(list(responses))
    monkeypatch.setattr(requests, 'request', transport)
    return transport


def test_list_count_and_get(monkeypatch: MonkeyPatch) -> None:
    transport = install(
        monkeypatch,
        FakeResponse(200, [TABLE]),
        FakeResponse(200, None, headers={'X-Query-Count': '1'}),
        FakeResponse(200, TABLE),
    )
    api = make_offline_api()

    api.get_type_curve_lookup_tables(PROJECT_ID)
    api.count_type_curve_lookup_tables(PROJECT_ID)
    api.get_type_curve_lookup_table_by_id(PROJECT_ID, TABLE_ID)

    assert [(call.method, call.url, call.params) for call in transport.calls] == [
        ('GET', BASE, {'take': 200}),
        ('HEAD', BASE, None),
        ('GET', f'{BASE}/{TABLE_ID}', None),
    ]


def test_writes(monkeypatch: MonkeyPatch) -> None:
    transport = install(
        monkeypatch,
        FakeResponse(201, TABLE),
        FakeResponse(207, ENVELOPE),
        FakeResponse(207, ENVELOPE),
        FakeResponse(200, TABLE),
        FakeResponse(204, None, headers={'X-Delete-Count': '1'}),
    )
    api = make_offline_api()

    api.post_type_curve_lookup_table(PROJECT_ID, TABLE)
    api.post_type_curve_lookup_tables(PROJECT_ID, [TABLE])
    api.put_type_curve_lookup_tables(PROJECT_ID, [TABLE])
    api.put_type_curve_lookup_table_by_id(PROJECT_ID, TABLE_ID, TABLE)
    headers = api.delete_type_curve_lookup_table_by_id(PROJECT_ID, TABLE_ID)

    assert [(call.method, call.url) for call in transport.calls] == [
        ('POST', BASE),
        ('POST', f'{BASE}/batch'),
        ('PUT', f'{BASE}/batch'),
        ('PUT', f'{BASE}/{TABLE_ID}'),
        ('DELETE', f'{BASE}/{TABLE_ID}'),
    ]
    assert headers['X-Delete-Count'] == '1'


def test_batch_writes_chunk_at_500(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(207, ENVELOPE), FakeResponse(207, ENVELOPE))

    make_offline_api().put_type_curve_lookup_tables(PROJECT_ID, [TABLE] * 501)

    assert [len(call.body) for call in transport.calls] == [500, 1]
