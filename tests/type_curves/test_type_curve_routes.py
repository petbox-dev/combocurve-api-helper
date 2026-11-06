"""Native v2 type-curve methods: route, verb, body and the documented edge cases. No network."""

from typing import TYPE_CHECKING, Any

import pytest
import requests
from pytest import MonkeyPatch

from tests.http_fakes import FakeResponse, make_offline_api
from tests.type_curves.transport import RecordingTransport

if TYPE_CHECKING:
    from combocurve_api_helper.base import Item

PROJECT_ID = '000000000000000000000001'
TYPE_CURVE_ID = '000000000000000000000002'
BASE = f'https://api.combocurve.com/v2/projects/{PROJECT_ID}/type-curves'
ENVELOPE: dict[str, Any] = {'successCount': 1, 'failedCount': 0, 'results': [{'status': 'Created', 'code': 201}]}


def install(monkeypatch: MonkeyPatch, *responses: FakeResponse) -> RecordingTransport:
    transport = RecordingTransport(list(responses))
    monkeypatch.setattr(requests, 'request', transport)
    return transport


def test_list_uses_v2_and_take_200(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(200, [{'id': TYPE_CURVE_ID, 'name': 'Sample'}]))

    rows = make_offline_api().get_type_curves(PROJECT_ID, {'name': 'Sample'})

    call = transport.calls[0]
    assert (call.method, call.url, call.params) == ('GET', f'{BASE}?name=Sample', {'take': 200})
    assert rows[0]['id'] == TYPE_CURVE_ID


def test_count_reads_the_head_header(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(200, None, headers={'X-Query-Count': '7'}))

    assert make_offline_api().count_type_curves(PROJECT_ID) == 7
    assert transport.calls[0].method == 'HEAD'


def test_get_by_id_returns_the_object(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(200, {'id': TYPE_CURVE_ID}))

    assert make_offline_api().get_type_curve_by_id(PROJECT_ID, TYPE_CURVE_ID) == {'id': TYPE_CURVE_ID}
    assert transport.calls[0].url == f'{BASE}/{TYPE_CURVE_ID}'


def test_post_one_sends_an_object_and_returns_the_stored_one(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(201, {'id': TYPE_CURVE_ID, 'name': 'Sample'}))

    stored = make_offline_api().post_type_curve(PROJECT_ID, {'name': 'Sample'})

    assert (transport.calls[0].method, transport.calls[0].url, transport.calls[0].body) == (
        'POST',
        BASE,
        {'name': 'Sample'},
    )
    assert stored['id'] == TYPE_CURVE_ID


def test_post_many_goes_to_batch_in_chunks_of_100(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(207, ENVELOPE), FakeResponse(207, ENVELOPE))
    records: list[Item] = [{'name': f'Sample {i}'} for i in range(150)]

    envelopes = make_offline_api().post_type_curves(PROJECT_ID, records)

    assert [call.url for call in transport.calls] == [f'{BASE}/batch', f'{BASE}/batch']
    assert [len(call.body) for call in transport.calls] == [100, 50]
    assert len(envelopes) == 2


def test_patch_one_and_many(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(200, {'id': TYPE_CURVE_ID}), FakeResponse(207, ENVELOPE))
    api = make_offline_api()

    api.patch_type_curve(PROJECT_ID, TYPE_CURVE_ID, {'name': 'Renamed'})
    api.patch_type_curves(PROJECT_ID, [{'id': TYPE_CURVE_ID, 'name': 'Renamed'}])

    assert [(call.method, call.url) for call in transport.calls] == [
        ('PATCH', f'{BASE}/{TYPE_CURVE_ID}'),
        ('PATCH', f'{BASE}/batch'),
    ]


def test_delete_with_no_match_reads_as_zero_deleted(monkeypatch: MonkeyPatch) -> None:
    """v2 answers 404 TypeCurveV2NotFoundError when no type curve matches (live 2026-11-05)."""
    install(monkeypatch, FakeResponse(404, {'name': 'TypeCurveV2NotFoundError', 'message': 'none'}))

    headers = make_offline_api().delete_type_curves(PROJECT_ID, name='Missing')

    assert headers['X-Delete-Count'] == '0'


def test_delete_with_another_404_still_raises(monkeypatch: MonkeyPatch) -> None:
    install(monkeypatch, FakeResponse(404, {'name': 'ProjectNotFoundError', 'message': 'no project'}))

    with pytest.raises(requests.HTTPError):
        make_offline_api().delete_type_curves(PROJECT_ID, name='Missing')


def test_delete_by_id(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(204, None, headers={'X-Delete-Count': '1'}))

    headers = make_offline_api().delete_type_curve_by_id(PROJECT_ID, TYPE_CURVE_ID)

    assert (transport.calls[0].method, transport.calls[0].url) == ('DELETE', f'{BASE}/{TYPE_CURVE_ID}')
    assert headers['X-Delete-Count'] == '1'


def test_fits_read_with_repeated_phase_and_write(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(200, {'gas': {}}), FakeResponse(200, {'gas': {}}))
    api = make_offline_api()

    api.get_type_curve_fits(PROJECT_ID, TYPE_CURVE_ID, phases=['oil', 'gas'])
    api.put_type_curve_fits(PROJECT_ID, TYPE_CURVE_ID, {'gas': {}})

    assert transport.calls[0].url == f'{BASE}/{TYPE_CURVE_ID}/fits?phase=oil&phase=gas'
    assert (transport.calls[1].method, transport.calls[1].body) == ('PUT', {'gas': {}})


def test_fits_never_fitted_is_an_empty_object(monkeypatch: MonkeyPatch) -> None:
    install(monkeypatch, FakeResponse(200, {}))

    assert make_offline_api().get_type_curve_fits(PROJECT_ID, TYPE_CURVE_ID) == {}


def test_normalization_read_and_write(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(200, {'oil': {}}), FakeResponse(200, {'oil': {}}))
    api = make_offline_api()

    api.get_type_curve_normalization(PROJECT_ID, TYPE_CURVE_ID)
    api.put_type_curve_normalization(PROJECT_ID, TYPE_CURVE_ID, {'oil': {}})

    assert [(call.method, call.url) for call in transport.calls] == [
        ('GET', f'{BASE}/{TYPE_CURVE_ID}/normalization'),
        ('PUT', f'{BASE}/{TYPE_CURVE_ID}/normalization'),
    ]


def test_volumes_send_resolution_and_take_2500(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(200, [{'date': '2026-01-31'}]))

    make_offline_api().get_type_curve_volumes(PROJECT_ID, TYPE_CURVE_ID, 'daily')

    assert transport.calls[0].url == f'{BASE}/{TYPE_CURVE_ID}/volumes'
    assert transport.calls[0].params == {'resolution': 'daily', 'take': 2500}


def test_wells_take_1000_and_count(monkeypatch: MonkeyPatch) -> None:
    transport = install(
        monkeypatch,
        FakeResponse(200, [{'id': 'w', 'wellName': 'Sample Well', 'excluded': False}]),
        FakeResponse(200, None, headers={'X-Query-Count': '1'}),
    )
    api = make_offline_api()

    api.get_type_curve_wells(PROJECT_ID, TYPE_CURVE_ID, {'excluded': 'true'})
    count = api.count_type_curve_wells(PROJECT_ID, TYPE_CURVE_ID)

    assert transport.calls[0].url == f'{BASE}/{TYPE_CURVE_ID}/wells?excluded=true'
    assert transport.calls[0].params == {'take': 1000}
    assert (transport.calls[1].method, count) == ('HEAD', 1)
