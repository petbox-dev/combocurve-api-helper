"""Embedded lookup tables (project and company) and the 3.1.0 saved-combo filters: verb, url,
query, body and result. No live API.

The route paths and docs slugs are also checked against the Postman collection by
`test_route_paths.py` and `test_docstring_slugs.py`.
"""

from collections.abc import Callable, Sequence

import pytest
import requests
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.base import ItemList
from combocurve_api_helper.scenarios import MAX_LOOKUP_TABLE_ASSIGNMENT_RECORDS, MAX_LOOKUP_TABLE_UNASSIGN_WELLS
from tests.http_fakes import FakeResponse, install_recording_transport, make_offline_api

V1 = 'https://api.combocurve.com/v1'
PROJECT_ID = '000000000000000000000001'
SCENARIO_ID = '000000000000000000000002'
TABLE_ID = '000000000000000000000003'
COMBO_ID_A = '000000000000000000000004'
COMBO_ID_B = '000000000000000000000005'
PROJECT_TABLES_URL = f'{V1}/projects/{PROJECT_ID}/embedded-lookup-tables'
COMPANY_TABLES_URL = f'{V1}/embedded-lookup-tables'
COMBOS_URL = f'{V1}/projects/{PROJECT_ID}/scenarios/{SCENARIO_ID}/combos'


WRITE_RESPONSE = {'generalErrors': [], 'results': [], 'failedCount': 0, 'successCount': 1}
TABLES: ItemList = [
    {'id': 'b', 'type': 'capex', 'name': 'Sample Table B', 'createdAt': '2020', 'updatedAt': '2020'},
    {'id': 'z', 'type': 'expenses', 'name': 'Sample Table A', 'createdAt': '2020', 'updatedAt': '2020'},
]
NEW_TABLE: ItemList = [{'type': 'capex', 'name': 'Sample Table C', 'rows': [], 'rules': []}]


# URLs


def test_embedded_lookup_table_urls() -> None:
    api = make_offline_api()
    assert api.get_embedded_lookup_tables_url(PROJECT_ID) == PROJECT_TABLES_URL
    assert api.get_embedded_lookup_tables_url(PROJECT_ID, {'type': 'capex'}) == f'{PROJECT_TABLES_URL}?type=capex'
    assert api.get_embedded_lookup_table_by_id_url(PROJECT_ID, TABLE_ID) == f'{PROJECT_TABLES_URL}/{TABLE_ID}'
    assert api.get_company_embedded_lookup_tables_url() == COMPANY_TABLES_URL
    assert api.get_company_embedded_lookup_tables_url({'name': 'Sample Table A'}) == (
        f'{COMPANY_TABLES_URL}?name=Sample%20Table%20A'
    )
    assert api.get_company_embedded_lookup_table_by_id_url(TABLE_ID) == f'{COMPANY_TABLES_URL}/{TABLE_ID}'


# Reads


@pytest.mark.parametrize(
    ('scope', 'expected_url'),
    [('project', f'{PROJECT_TABLES_URL}?type=capex'), ('company', f'{COMPANY_TABLES_URL}?type=capex')],
)
def test_get_lists_take_200_carry_the_filters_and_sort_by_name(
    monkeypatch: MonkeyPatch, scope: str, expected_url: str
) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, [dict(table) for table in TABLES]))
    api = make_offline_api()

    if scope == 'project':
        result = api.get_embedded_lookup_tables(PROJECT_ID, {'type': 'capex'})
    else:
        result = api.get_company_embedded_lookup_tables({'type': 'capex'})

    assert [table['id'] for table in result] == ['z', 'b']  # by name; an id sort would give b, z
    assert recorder.calls[0].method == 'GET'
    assert recorder.calls[0].url == expected_url
    assert recorder.calls[0].params == {'take': 200}


def test_counts_send_head_to_the_filtered_url(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, *[FakeResponse(200, headers={'X-Query-Count': '7'})] * 2)
    api = make_offline_api()

    assert api.count_embedded_lookup_tables(PROJECT_ID, {'type': 'risking'}) == 7
    assert api.count_company_embedded_lookup_tables({'type': 'operations'}) == 7
    assert [(call.method, call.url) for call in recorder.calls] == [
        ('HEAD', f'{PROJECT_TABLES_URL}?type=risking'),
        ('HEAD', f'{COMPANY_TABLES_URL}?type=operations'),
    ]


def test_get_by_id_returns_the_single_object(monkeypatch: MonkeyPatch) -> None:
    table = {'id': TABLE_ID, 'type': 'capex', 'name': 'Sample Table A', 'rows': [], 'rules': []}
    recorder = install_recording_transport(monkeypatch, *[FakeResponse(200, table)] * 2)
    api = make_offline_api()

    assert api.get_embedded_lookup_table_by_id(PROJECT_ID, TABLE_ID) == table
    assert api.get_company_embedded_lookup_table_by_id(TABLE_ID) == table
    assert [call.url for call in recorder.calls] == [
        f'{PROJECT_TABLES_URL}/{TABLE_ID}',
        f'{COMPANY_TABLES_URL}/{TABLE_ID}',
    ]


# Writes


def test_post_and_put_send_the_list_body(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, *[FakeResponse(207, WRITE_RESPONSE)] * 4)
    api = make_offline_api()

    assert api.post_embedded_lookup_tables(PROJECT_ID, NEW_TABLE) == [WRITE_RESPONSE]
    assert api.put_embedded_lookup_tables(PROJECT_ID, NEW_TABLE) == [WRITE_RESPONSE]
    assert api.post_company_embedded_lookup_tables(NEW_TABLE) == [WRITE_RESPONSE]
    assert api.put_company_embedded_lookup_tables(NEW_TABLE) == [WRITE_RESPONSE]
    assert [(call.method, call.url, call.body) for call in recorder.calls] == [
        ('POST', PROJECT_TABLES_URL, NEW_TABLE),
        ('PUT', PROJECT_TABLES_URL, NEW_TABLE),
        ('POST', COMPANY_TABLES_URL, NEW_TABLE),
        ('PUT', COMPANY_TABLES_URL, NEW_TABLE),
    ]


def test_delete_by_id_returns_the_headers(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, *[FakeResponse(204, headers={'X-Delete-Count': '1'})] * 2)
    api = make_offline_api()

    assert api.delete_embedded_lookup_table_by_id(PROJECT_ID, TABLE_ID)['X-Delete-Count'] == '1'
    assert api.delete_company_embedded_lookup_table_by_id(TABLE_ID)['X-Delete-Count'] == '1'
    assert [(call.method, call.url) for call in recorder.calls] == [
        ('DELETE', f'{PROJECT_TABLES_URL}/{TABLE_ID}'),
        ('DELETE', f'{COMPANY_TABLES_URL}/{TABLE_ID}'),
    ]


# Saved combos


def test_get_scenario_combos_carries_the_filters_and_keeps_the_order(monkeypatch: MonkeyPatch) -> None:
    saved_combos: ItemList = [
        {'id': 'b', 'savedName': 'Sample Group B', 'updatedAt': '2026', 'combos': []},
        {'id': 'a', 'savedName': 'Sample Group A', 'updatedAt': '2025', 'combos': []},
    ]
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, saved_combos))

    result = make_offline_api().get_scenario_combos(
        PROJECT_ID, SCENARIO_ID, {'sort': '-updatedAt', 'updatedAt[ge]': '2025-01-01'}
    )

    assert result == saved_combos
    assert recorder.calls[0].url == f'{COMBOS_URL}?sort=-updatedAt&updatedAt%5Bge%5D=2025-01-01'
    assert recorder.calls[0].params == {'take': 200}


def test_get_scenario_combos_without_filters_sends_the_bare_url(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, []))

    make_offline_api().get_scenario_combos(PROJECT_ID, SCENARIO_ID)

    assert recorder.calls[0].url == COMBOS_URL


def test_delete_scenario_combo_without_combo_ids_deletes_the_group(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204, headers={'X-Delete-Count': '1'}))

    headers = make_offline_api().delete_scenario_combo(PROJECT_ID, SCENARIO_ID, 'Sample Group A')

    assert headers['X-Delete-Count'] == '1'
    assert recorder.calls[0].method == 'DELETE'
    assert recorder.calls[0].url == f'{COMBOS_URL}?savedName=Sample%20Group%20A'


def test_delete_scenario_combo_with_combo_ids_repeats_the_key(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204, headers={'X-Delete-Count': '2'}))

    make_offline_api().delete_scenario_combo(PROJECT_ID, SCENARIO_ID, 'Sample Group A', [COMBO_ID_A, COMBO_ID_B])

    assert recorder.calls[0].url == (
        f'{COMBOS_URL}?savedName=Sample%20Group%20A&comboIds={COMBO_ID_A}&comboIds={COMBO_ID_B}'
    )


@pytest.mark.parametrize('combo_ids', [[], [COMBO_ID_A, ''], COMBO_ID_A])
def test_delete_scenario_combo_refuses_combo_ids_that_name_no_combo(
    monkeypatch: MonkeyPatch, combo_ids: Sequence[str]
) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204))

    with pytest.raises(ValueError, match='combo_ids'):
        make_offline_api().delete_scenario_combo(PROJECT_ID, SCENARIO_ID, 'Sample Group A', combo_ids)

    assert recorder.calls == []


def test_delete_scenario_combo_still_requires_a_saved_name(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204))

    with pytest.raises(ValueError, match='saved_name'):
        make_offline_api().delete_scenario_combo(PROJECT_ID, SCENARIO_ID, '', [COMBO_ID_A])

    assert recorder.calls == []


# Scenario lookup-table assignments (forecast column takes a Type Curve V2 lookup table)

LOOKUP_ASSIGNMENTS_URL = f'{V1}/projects/{PROJECT_ID}/scenarios/{SCENARIO_ID}/assignments/lookup-tables'
WELL_ID_A = '000000000000000000000006'
WELL_ID_B = '000000000000000000000007'


def test_get_scenario_lookup_table_assignments_carries_the_filters(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, []))

    make_offline_api().get_scenario_lookup_table_assignments(
        PROJECT_ID, SCENARIO_ID, {'column': 'forecast', 'qualifierName': 'Sample Qualifier'}
    )

    assert recorder.calls[0].url == f'{LOOKUP_ASSIGNMENTS_URL}?column=forecast&qualifierName=Sample%20Qualifier'


def test_delete_lookup_table_assignment_sends_the_well_ids_as_the_body(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204, headers={'X-Delete-Count': '2'}))

    headers = make_offline_api().delete_scenario_lookup_table_assignment_by_id(
        PROJECT_ID, SCENARIO_ID, TABLE_ID, [WELL_ID_A, WELL_ID_B]
    )

    assert headers['X-Delete-Count'] == '2'
    assert len(recorder.calls) == 1
    assert recorder.calls[0].method == 'DELETE'
    assert recorder.calls[0].url == f'{LOOKUP_ASSIGNMENTS_URL}/{TABLE_ID}'
    assert recorder.calls[0].body == [WELL_ID_A, WELL_ID_B]


def test_delete_lookup_table_assignment_sends_the_maximum_in_one_request(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204))
    well_ids = [WELL_ID_A] * MAX_LOOKUP_TABLE_UNASSIGN_WELLS

    make_offline_api().delete_scenario_lookup_table_assignment_by_id(PROJECT_ID, SCENARIO_ID, TABLE_ID, well_ids)

    assert [call.body for call in recorder.calls] == [well_ids]


def test_delete_lookup_table_assignment_carries_the_incremental_index(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204))

    make_offline_api().delete_scenario_lookup_table_assignment_by_id(
        PROJECT_ID, SCENARIO_ID, TABLE_ID, [WELL_ID_A], incremental_index=2
    )

    assert recorder.calls[0].url == f'{LOOKUP_ASSIGNMENTS_URL}/{TABLE_ID}?incrementalIndex=2'


@pytest.mark.parametrize(
    'well_ids', [[], [WELL_ID_A, ''], WELL_ID_A, [WELL_ID_A] * (MAX_LOOKUP_TABLE_UNASSIGN_WELLS + 1)]
)
def test_delete_lookup_table_assignment_refuses_bad_well_ids(monkeypatch: MonkeyPatch, well_ids: Sequence[str]) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204))

    with pytest.raises(ValueError, match='well_ids'):
        make_offline_api().delete_scenario_lookup_table_assignment_by_id(PROJECT_ID, SCENARIO_ID, TABLE_ID, well_ids)

    assert recorder.calls == []


def test_delete_lookup_table_assignment_raises_on_an_error_status(monkeypatch: MonkeyPatch) -> None:
    install_recording_transport(monkeypatch, FakeResponse(400, {'message': 'bad'}))

    with pytest.raises(requests.HTTPError):
        make_offline_api().delete_scenario_lookup_table_assignment_by_id(PROJECT_ID, SCENARIO_ID, TABLE_ID, [WELL_ID_A])


def test_delete_scenario_combo_sends_the_ids_of_a_one_shot_iterable(monkeypatch: MonkeyPatch) -> None:
    """A generator passes a truthiness check and is then empty; the ids must still be sent, or the
    call would delete the whole saved combo."""
    recorder = install_recording_transport(monkeypatch, FakeResponse(204, headers={'X-Delete-Count': '1'}))

    make_offline_api().delete_scenario_combo(
        PROJECT_ID,
        SCENARIO_ID,
        'Sample Group A',
        (combo_id for combo_id in [COMBO_ID_A]),  # type: ignore[arg-type]
    )

    assert recorder.calls[0].url.endswith(f'&comboIds={COMBO_ID_A}')


NO_COMBO_IDS: list[str] = []


def test_delete_scenario_combo_refuses_an_empty_one_shot_iterable(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204))

    with pytest.raises(ValueError, match='combo_ids'):
        make_offline_api().delete_scenario_combo(
            PROJECT_ID,
            SCENARIO_ID,
            'Sample Group A',
            (combo_id for combo_id in NO_COMBO_IDS),  # type: ignore[arg-type]
        )

    assert recorder.calls == []


def test_put_lookup_table_assignments_refuses_an_empty_list(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(207, WRITE_RESPONSE))

    with pytest.raises(ValueError, match='data must hold at least one assignment record'):
        make_offline_api().put_scenario_lookup_table_assignments(PROJECT_ID, SCENARIO_ID, [])

    assert recorder.calls == []


def _assignment_records(count: int) -> ItemList:
    record = {'column': 'forecast', 'lookUpTableId': TABLE_ID, 'wellIds': [WELL_ID_A], 'qualifierName': 'Default'}
    return [dict(record) for _ in range(count)]


def test_put_lookup_table_assignments_sends_the_maximum_in_one_request(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(207, WRITE_RESPONSE))
    data = _assignment_records(MAX_LOOKUP_TABLE_ASSIGNMENT_RECORDS)

    make_offline_api().put_scenario_lookup_table_assignments(PROJECT_ID, SCENARIO_ID, data)

    assert [(call.method, call.body) for call in recorder.calls] == [('PUT', data)]


def test_put_lookup_table_assignments_refuses_more_than_the_maximum(monkeypatch: MonkeyPatch) -> None:
    """One request or none: a split write could leave earlier batches applied with no sign of it."""
    recorder = install_recording_transport(monkeypatch)

    with pytest.raises(ValueError, match='at most'):
        make_offline_api().put_scenario_lookup_table_assignments(
            PROJECT_ID, SCENARIO_ID, _assignment_records(MAX_LOOKUP_TABLE_ASSIGNMENT_RECORDS + 1)
        )

    assert recorder.calls == []


def test_the_lookup_table_assignment_caps_are_the_documented_500() -> None:
    """Pinned apart from the constants, so the boundary tests above cannot follow a wrong value."""
    assert MAX_LOOKUP_TABLE_ASSIGNMENT_RECORDS == MAX_LOOKUP_TABLE_UNASSIGN_WELLS == 500


@pytest.mark.parametrize(
    'call',
    [
        lambda api: api.post_embedded_lookup_tables(PROJECT_ID, []),
        lambda api: api.put_embedded_lookup_tables(PROJECT_ID, []),
        lambda api: api.post_company_embedded_lookup_tables([]),
        lambda api: api.put_company_embedded_lookup_tables([]),
    ],
)
def test_embedded_lookup_table_writes_refuse_an_empty_list(
    monkeypatch: MonkeyPatch, call: Callable[[ComboCurveAPI], object]
) -> None:
    recorder = install_recording_transport(monkeypatch)

    with pytest.raises(ValueError, match='at least one embedded lookup table'):
        call(make_offline_api())

    assert recorder.calls == []
