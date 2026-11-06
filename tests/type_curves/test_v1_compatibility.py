"""Deprecated v1 type-curve behavior on the v2 routes. No network."""

import copy
import json
import warnings
from pathlib import Path
from typing import Any, cast

import pytest
import requests
from pytest import MonkeyPatch

from tests.http_fakes import FakeResponse, make_offline_api
from tests.type_curves.transport import RecordingTransport

FIXTURES = Path(__file__).parent / 'fixtures'
PROJECT_ID = '000000000000000000000001'
TYPE_CURVE_ID = '000000000000000000000002'
FORECAST_ID = '000000000000000000000004'
V1_TABLE_ID = 'aaaaaaaaaaaabbbbbbbbbbbb'
BASE = f'https://api.combocurve.com/v2/projects/{PROJECT_ID}/type-curves'


def load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding='utf8'))


def install(monkeypatch: MonkeyPatch, *responses: FakeResponse) -> RecordingTransport:
    transport = RecordingTransport(list(responses))
    monkeypatch.setattr(requests, 'request', transport)
    return transport


def test_monthly_fits_wrapper_returns_the_v1_rows(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(200, load('paired_v2_monthly_volumes.json')))

    with pytest.warns(DeprecationWarning, match=r'get_type_curve_monthly_fits.*2027-01-31'):
        rows = make_offline_api().get_type_curve_monthly_fits(PROJECT_ID, TYPE_CURVE_ID)

    assert rows == load('paired_v1_monthly_fits.json')
    assert transport.calls[0].params == {'resolution': 'monthly', 'take': 2500}


def test_daily_fits_wrapper_asks_for_daily(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(200, []))

    with pytest.warns(DeprecationWarning, match='get_type_curve_daily_fits'):
        make_offline_api().get_type_curve_daily_fits(PROJECT_ID, TYPE_CURVE_ID)

    assert transport.calls[0].params['resolution'] == 'daily'


def test_representative_wells_wrapper_joins_wells_and_outputs(monkeypatch: MonkeyPatch) -> None:
    wells = [
        {
            'id': f'00000000000000000000001{i}',
            'wellName': f'Sample Well {i}',
            'excluded': False,
            'perfLateralLength': 1000,
        }
        for i in range(2)
    ]
    outputs = [
        {
            'well': wells[0]['id'],
            'phase': 'oil',
            'forecastType': 'rate',
            'forecastSubType': 'automatic',
            'data_freq': 'monthly',
            'best': {'eur': 5000.0},
        }
    ]
    transport = install(
        monkeypatch,
        FakeResponse(200, {'id': TYPE_CURVE_ID, 'forecast': FORECAST_ID, 'forecastSeries': 'best'}),
        FakeResponse(200, wells),
        FakeResponse(200, outputs),
    )

    with pytest.warns(DeprecationWarning, match='get_type_curve_representative_fits'):
        rows = make_offline_api().get_type_curve_representative_fits(PROJECT_ID, TYPE_CURVE_ID)

    outputs_call = transport.calls[2]
    assert outputs_call.url == (
        f'https://api.combocurve.com/v1/projects/{PROJECT_ID}/forecasts/{FORECAST_ID}/outputs'
        f'?well={wells[0]["id"]}&well={wells[1]["id"]}'
    )
    assert [row['wellName'] for row in rows] == ['Sample Well 0', 'Sample Well 1']
    assert cast('Any', rows[0]['oil'])['eur'] == 5.0
    assert cast('Any', rows[1]['oil'])['forecastType'] == 'not_forecasted'


def test_post_without_v1_fields_is_the_native_batch_with_no_warning(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(207, {'successCount': 1, 'failedCount': 0, 'results': []}))

    with warnings.catch_warnings():
        warnings.simplefilter('error')
        make_offline_api().post_type_curves(PROJECT_ID, [{'name': 'Sample'}])

    assert transport.calls[0].url == f'{BASE}/batch'


def test_post_with_v1_fits_creates_then_writes_fits(monkeypatch: MonkeyPatch) -> None:
    record = load('v1_type_curve_ratio_linear.json')
    del record['id'], record['createdAt'], record['updatedAt']
    transport = install(
        monkeypatch,
        FakeResponse(
            207,
            {'successCount': 1, 'failedCount': 0, 'results': [{'status': 'Created', 'code': 201, 'id': TYPE_CURVE_ID}]},
        ),
        FakeResponse(200, {'gas': {}}),
    )

    with pytest.warns(DeprecationWarning, match='post_type_curves'):
        envelopes = make_offline_api().post_type_curves(PROJECT_ID, [record])

    create, fits = transport.calls
    assert create.url == f'{BASE}/batch'
    assert 'fits' not in create.body[0] and 'regressionType' not in create.body[0]
    assert (fits.method, fits.url) == ('PUT', f'{BASE}/{TYPE_CURVE_ID}/fits')
    assert fits.body['gas']['fitType'] == 'ratio'
    assert envelopes == [
        {
            'successCount': 1,
            'failedCount': 0,
            'generalErrors': [],
            'results': [{'status': 'Created', 'code': 201, 'id': TYPE_CURVE_ID}],
        }
    ]


def test_a_failed_fits_write_becomes_a_failed_result(monkeypatch: MonkeyPatch) -> None:
    record = load('v1_type_curve_ratio_linear.json')
    install(
        monkeypatch,
        FakeResponse(
            207,
            {'successCount': 1, 'failedCount': 0, 'results': [{'status': 'Created', 'code': 201, 'id': TYPE_CURVE_ID}]},
        ),
        FakeResponse(400, {'name': 'ValidationError', 'message': 'bad segment'}),
    )

    with pytest.warns(DeprecationWarning):
        envelopes = make_offline_api().post_type_curves(PROJECT_ID, [record])

    result = envelopes[0]['results'][0]
    assert (result['status'], result['code'], result['id']) == ('Error', 400, TYPE_CURVE_ID)
    assert (envelopes[0]['successCount'], envelopes[0]['failedCount']) == (0, 1)


def test_post_with_only_v1_normalizations_strips_them_and_warns(monkeypatch: MonkeyPatch) -> None:
    transport = install(
        monkeypatch,
        FakeResponse(
            207,
            {'successCount': 1, 'failedCount': 0, 'results': [{'status': 'Created', 'code': 201, 'id': TYPE_CURVE_ID}]},
        ),
    )

    with pytest.warns(DeprecationWarning, match='post_type_curves'):
        make_offline_api().post_type_curves(PROJECT_ID, [{'name': 'Sample', 'normalizations': []}])

    assert len(transport.calls) == 1
    assert transport.calls[0].body == [{'name': 'Sample'}]


def test_a_record_with_no_returned_result_becomes_a_missing_result_error(monkeypatch: MonkeyPatch) -> None:
    record = load('v1_type_curve_ratio_linear.json')
    transport = install(
        monkeypatch,
        FakeResponse(
            207,
            {'successCount': 1, 'failedCount': 0, 'results': [{'status': 'Created', 'code': 201, 'id': TYPE_CURVE_ID}]},
        ),
        FakeResponse(200, {'gas': {}}),
    )

    with pytest.warns(DeprecationWarning):
        envelopes = make_offline_api().post_type_curves(PROJECT_ID, [record, copy.deepcopy(record)])

    results = envelopes[0]['results']
    assert len(results) == 2
    assert results[1] == {
        'status': 'Error',
        'code': 0,
        'errors': [
            {
                'name': 'MissingResult',
                'message': 'the server returned no result for this record',
                'location': '[1]',
            }
        ],
    }
    assert (envelopes[0]['successCount'], envelopes[0]['failedCount']) == (1, 1)
    assert [call.method for call in transport.calls] == ['POST', 'PUT']


def test_put_type_curves_patches_existing_names_and_posts_new_ones(monkeypatch: MonkeyPatch) -> None:
    existing = {'id': TYPE_CURVE_ID, 'name': 'Existing'}
    transport = install(
        monkeypatch,
        FakeResponse(200, [existing]),
        FakeResponse(
            207,
            {
                'successCount': 1,
                'failedCount': 0,
                'results': [{'status': 'Created', 'code': 201, 'id': '000000000000000000000009'}],
            },
        ),
        FakeResponse(
            207, {'successCount': 1, 'failedCount': 0, 'results': [{'status': 'OK', 'code': 200, 'id': TYPE_CURVE_ID}]}
        ),
    )

    with pytest.warns(DeprecationWarning, match='put_type_curves'):
        envelopes = make_offline_api().put_type_curves(PROJECT_ID, [{'name': 'Existing'}, {'name': 'New'}])

    assert [(call.method, call.url) for call in transport.calls] == [
        ('GET', BASE),
        ('POST', f'{BASE}/batch'),
        ('PATCH', f'{BASE}/batch'),
    ]
    assert transport.calls[2].body == [{'name': 'Existing', 'id': TYPE_CURVE_ID}]
    assert [result['id'] for result in envelopes[0]['results']] == [TYPE_CURVE_ID, '000000000000000000000009']


def test_a_failed_patch_stage_still_writes_the_fits_of_created_records(monkeypatch: MonkeyPatch) -> None:
    created_id = '000000000000000000000009'
    record = load('v1_type_curve_ratio_linear.json')
    record['name'] = 'New'
    transport = install(
        monkeypatch,
        FakeResponse(200, [{'id': TYPE_CURVE_ID, 'name': 'Existing'}]),
        FakeResponse(
            207,
            {'successCount': 1, 'failedCount': 0, 'results': [{'status': 'Created', 'code': 201, 'id': created_id}]},
        ),
        FakeResponse(400, {'name': 'ValidationError', 'message': 'bad patch'}),
        FakeResponse(200, {'gas': {}}),
    )

    with pytest.warns(DeprecationWarning, match='put_type_curves'):
        envelopes = make_offline_api().put_type_curves(PROJECT_ID, [{'name': 'Existing'}, record])

    assert [(call.method, call.url) for call in transport.calls][-1] == ('PUT', f'{BASE}/{created_id}/fits')
    results = cast('Any', envelopes[0]['results'])
    assert results[1]['code'] == 201
    assert (results[0]['status'], results[0]['code']) == ('Error', 400)
    assert results[0]['errors'][0]['name'] == 'PatchError'
    assert (envelopes[0]['successCount'], envelopes[0]['failedCount']) == (1, 1)


def test_a_connection_failure_in_the_create_stage_marks_the_results_as_maybe_applied(
    monkeypatch: MonkeyPatch,
) -> None:
    def refuse(*arguments: Any, **keywords: Any) -> Any:
        raise requests.ConnectionError('reset')

    monkeypatch.setattr(requests, 'request', refuse)

    with pytest.warns(DeprecationWarning):
        envelopes = make_offline_api().post_type_curves(PROJECT_ID, [load('v1_type_curve_ratio_linear.json')])

    result = envelopes[0]['results'][0]
    assert (result['status'], result['code']) == ('Error', 0)
    assert result['mayHaveApplied'] is True
    assert envelopes[0]['failedCount'] == 1


def test_a_patch_result_without_an_id_writes_fits_to_the_body_id(monkeypatch: MonkeyPatch) -> None:
    record = load('v1_type_curve_ratio_linear.json')
    record['name'] = 'Existing'
    transport = install(
        monkeypatch,
        FakeResponse(200, [{'id': TYPE_CURVE_ID, 'name': 'Existing'}]),
        FakeResponse(207, {'successCount': 1, 'failedCount': 0, 'results': [{'status': 'OK', 'code': 204}]}),
        FakeResponse(200, {'gas': {}}),
    )

    with pytest.warns(DeprecationWarning):
        envelopes = make_offline_api().put_type_curves(PROJECT_ID, [record])

    assert (transport.calls[-1].method, transport.calls[-1].url) == ('PUT', f'{BASE}/{TYPE_CURVE_ID}/fits')
    assert (envelopes[0]['successCount'], envelopes[0]['failedCount']) == (1, 0)


def test_a_lookup_table_404_with_another_error_name_does_not_fall_back(monkeypatch: MonkeyPatch) -> None:
    transport = install(monkeypatch, FakeResponse(404, {'name': 'ProjectNotFoundError'}))

    with pytest.raises(requests.HTTPError):
        make_offline_api().get_type_curve_lookup_table_by_id(PROJECT_ID, V1_TABLE_ID)

    assert len(transport.calls) == 1


def test_delete_falls_back_when_the_server_answers_lookup_table_not_found(monkeypatch: MonkeyPatch) -> None:
    transport = install(
        monkeypatch,
        FakeResponse(404, {'name': 'LookupTableNotFoundError'}),
        FakeResponse(204, None, headers={'X-Delete-Count': '1'}),
    )

    with pytest.warns(DeprecationWarning, match='lookup-table id'):
        headers = make_offline_api().delete_type_curve_lookup_table_by_id(PROJECT_ID, V1_TABLE_ID)

    assert headers['X-Delete-Count'] == '1'
    assert transport.calls[1].url.endswith('/lookup-tables/bbbbbbbbbbbbaaaaaaaaaaaa')


def test_v1_lookup_table_fields_are_translated(monkeypatch: MonkeyPatch) -> None:
    table = load('v1_lookup_table_per_phase.json')
    table['rules'] = [rule for rule in table['rules'] if rule['filter'][0]['value'] != 'NM']
    transport = install(monkeypatch, FakeResponse(201, {}))

    with pytest.warns(DeprecationWarning, match='post_type_curve_lookup_table'):
        make_offline_api().post_type_curve_lookup_table(PROJECT_ID, table)

    sent_rules = transport.calls[0].body['rules']
    assert all('phase' not in rule and 'riskFactorOil' not in rule for rule in sent_rules)


def test_v1_lookup_table_id_falls_back_to_the_swapped_id(monkeypatch: MonkeyPatch) -> None:
    transport = install(
        monkeypatch,
        FakeResponse(404, {'name': 'LookupTableNotFoundError'}),
        FakeResponse(200, {'id': 'bbbbbbbbbbbbaaaaaaaaaaaa'}),
    )

    with pytest.warns(DeprecationWarning, match='lookup-table id'):
        table = make_offline_api().get_type_curve_lookup_table_by_id(PROJECT_ID, V1_TABLE_ID)

    assert transport.calls[1].url.endswith('/lookup-tables/bbbbbbbbbbbbaaaaaaaaaaaa')
    assert table['id'] == 'bbbbbbbbbbbbaaaaaaaaaaaa'


def test_v1_lookup_table_id_fallback_on_delete_when_nothing_matched(monkeypatch: MonkeyPatch) -> None:
    transport = install(
        monkeypatch,
        FakeResponse(204, None, headers={'X-Delete-Count': '0'}),
        FakeResponse(204, None, headers={'X-Delete-Count': '1'}),
    )

    with pytest.warns(DeprecationWarning):
        headers = make_offline_api().delete_type_curve_lookup_table_by_id(PROJECT_ID, V1_TABLE_ID)

    assert headers['X-Delete-Count'] == '1'
    assert len(transport.calls) == 2


def test_a_missing_id_raises_after_one_fallback(monkeypatch: MonkeyPatch) -> None:
    install(
        monkeypatch,
        FakeResponse(404, {'name': 'LookupTableNotFoundError'}),
        FakeResponse(404, {'name': 'LookupTableNotFoundError'}),
    )

    with pytest.raises(requests.HTTPError):
        make_offline_api().get_type_curve_lookup_table_by_id(PROJECT_ID, V1_TABLE_ID)


def test_conversions_are_exported_from_the_package() -> None:
    import combocurve_api_helper

    assert callable(combocurve_api_helper.fits_for_put)
    assert callable(combocurve_api_helper.normalization_for_put)
