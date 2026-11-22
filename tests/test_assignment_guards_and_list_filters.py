"""Assignment write guards and the list methods' `filters`, offline.

- An econ-model unassign (`delete_econ_model_assignments_by_type_by_id` and its generated per-type
  wrappers) refuses a `wells` that names no well, before any request, and sends one repeated `wells` key
  per id (the route refuses a comma-joined value; verified live 2026-11-21).
- `delete_scenario_model_assignments` refuses a record that names no well; `delete_scenario_wells`
  refuses a blank element between commas.
- The scenario assignment writes refuse more than 500 records before any request, all with one message.
- The list twins of the filtered count methods take `filters`, and the filters reach the url.
"""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Union

import pytest
from pytest import MonkeyPatch

from tests.http_fakes import FakeResponse, install_recording_transport, make_offline_api, object_ids

if TYPE_CHECKING:
    from combocurve_api_helper.base import ItemList

PROJECT_ID = '000000000000000000000001'
SCENARIO_ID = '000000000000000000000002'
MODEL_ID = '000000000000000000000003'
RUN_ID = '000000000000000000000004'
TABLE_ID = '000000000000000000000005'
WELL_A = '00000000000000000000000a'
WELL_B = '00000000000000000000000b'

# Econ-model unassign: `wells`

BLANK_WELLS: list[Union[str, Sequence[str]]] = [
    [],
    [''],
    [WELL_A, ''],
    (),
    '',
    ',',
    f'{WELL_A},',
    f'{WELL_A},,{WELL_B}',
]


@pytest.mark.parametrize('wells', BLANK_WELLS)
def test_econ_model_unassign_refuses_a_wells_that_names_no_well(
    monkeypatch: MonkeyPatch, wells: Union[str, Sequence[str]]
) -> None:
    recorder = install_recording_transport(monkeypatch)

    with pytest.raises(ValueError, match='wells'):
        make_offline_api().delete_econ_model_assignments_by_type_by_id(
            PROJECT_ID, 'Capex', MODEL_ID, SCENARIO_ID, wells=wells
        )

    assert recorder.calls == []


@pytest.mark.parametrize('wells', BLANK_WELLS)
def test_generated_unassign_wrapper_refuses_a_wells_that_names_no_well(
    monkeypatch: MonkeyPatch, wells: Union[str, Sequence[str]]
) -> None:
    """FluidModel is the canary for the per-type wrappers (multi-word kebab route)."""
    recorder = install_recording_transport(monkeypatch)

    with pytest.raises(ValueError, match='wells'):
        make_offline_api().delete_fluid_assignments_by_id(PROJECT_ID, MODEL_ID, SCENARIO_ID, wells=wells)

    assert recorder.calls == []


@pytest.mark.parametrize('wells', [[WELL_A, WELL_B], (WELL_A, WELL_B), f'{WELL_A},{WELL_B}'])
def test_econ_model_unassign_sends_one_wells_key_per_id(
    monkeypatch: MonkeyPatch, wells: Union[str, Sequence[str]]
) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204, None, headers={'X-Delete-Count': '2'}))

    make_offline_api().delete_fluid_assignments_by_id(PROJECT_ID, MODEL_ID, SCENARIO_ID, wells=wells)

    assert len(recorder.calls) == 1
    assert recorder.calls[0].method == 'DELETE'
    assert '/econ-models/fluid-models/' in recorder.calls[0].url
    assert recorder.calls[0].url.endswith(f'?scenarioId={SCENARIO_ID}&wells={WELL_A}&wells={WELL_B}')


def test_econ_model_unassign_without_wells_sends_no_wells_key(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204, None))

    make_offline_api().delete_capex_assignments_by_id(PROJECT_ID, MODEL_ID, SCENARIO_ID)

    assert len(recorder.calls) == 1
    assert 'wells' not in recorder.calls[0].url


# Model-assignment DELETE: a record must name a well


@pytest.mark.parametrize(
    'record',
    [
        {'model': 'forecast', 'qualifierName': 'q', 'wellIds': []},
        {'model': 'forecast', 'qualifierName': 'q', 'wellIds': ['']},
        {'model': 'forecast', 'qualifierName': 'q', 'wellIds': [WELL_A, '']},
        {'model': 'forecast', 'qualifierName': 'q', 'wellIds': WELL_A},
        {'model': 'forecast', 'qualifierName': 'q'},
        {'model': 'forecast', 'qualifierName': 'q', 'allWells': False, 'wellIds': []},
    ],
)
def test_delete_scenario_model_assignments_refuses_a_record_that_names_no_well(
    monkeypatch: MonkeyPatch, record: dict[str, Any]
) -> None:
    recorder = install_recording_transport(monkeypatch)
    data: ItemList = [{'model': 'forecast', 'qualifierName': 'q', 'wellIds': [WELL_A]}, record]

    with pytest.raises(ValueError, match=r'data\[1\]'):
        make_offline_api().delete_scenario_model_assignments(PROJECT_ID, SCENARIO_ID, data)

    assert recorder.calls == []


@pytest.mark.parametrize(
    'record',
    [
        {'model': 'forecast', 'qualifierName': 'q', 'wellIds': [WELL_A, WELL_B]},
        {'model': 'forecast', 'qualifierName': 'q', 'allWells': True},
        {'model': 'forecast', 'qualifierName': 'q', 'allWells': True, 'wellIds': []},
    ],
)
def test_delete_scenario_model_assignments_sends_a_record_that_names_wells(
    monkeypatch: MonkeyPatch, record: dict[str, Any]
) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204, None, headers={'X-Delete-Count': '1'}))
    data: ItemList = [record]

    make_offline_api().delete_scenario_model_assignments(PROJECT_ID, SCENARIO_ID, data)

    assert len(recorder.calls) == 1
    assert recorder.calls[0].body == data


# Scenario well unassign: `wells` str


@pytest.mark.parametrize('wells', [',', f'{WELL_A},', f',{WELL_A}', f'{WELL_A},,{WELL_B}'])
def test_delete_scenario_wells_refuses_a_blank_element(monkeypatch: MonkeyPatch, wells: str) -> None:
    recorder = install_recording_transport(monkeypatch)

    with pytest.raises(ValueError, match='wells'):
        make_offline_api().delete_scenario_wells(PROJECT_ID, SCENARIO_ID, wells)

    assert recorder.calls == []


def test_delete_scenario_wells_repeats_the_wells_key(monkeypatch: MonkeyPatch) -> None:
    """A caller-joined string is split: the route answers 400 to a comma-joined `wells` (live 2026-11-21)."""
    recorder = install_recording_transport(monkeypatch, FakeResponse(204, None, headers={'X-Delete-Count': '2'}))

    headers = make_offline_api().delete_scenario_wells(PROJECT_ID, SCENARIO_ID, f'{WELL_A},{WELL_B}')

    assert headers['X-Delete-Count'] == '2'
    assert recorder.calls[0].url.endswith(f'/well-assignments?wells={WELL_A}&wells={WELL_B}')


# The 500-record limit

RECORD_LIMIT_METHODS = [
    'put_scenario_model_assignments',
    'delete_scenario_model_assignments',
    'put_scenario_econ_model_assignments',
    'delete_scenario_econ_model_assignments',
    'put_scenario_lookup_table_assignments',
]


@pytest.mark.parametrize('method_name', RECORD_LIMIT_METHODS)
def test_501_records_are_refused_before_any_request(monkeypatch: MonkeyPatch, method_name: str) -> None:
    recorder = install_recording_transport(monkeypatch)
    data: ItemList = [{'model': 'forecast', 'qualifierName': 'q', 'wellIds': [WELL_A]}] * 501

    with pytest.raises(ValueError, match=r'^data holds 501 records; the route takes at most 500 per request$'):
        getattr(make_offline_api(), method_name)(PROJECT_ID, SCENARIO_ID, data)

    assert recorder.calls == []


@pytest.mark.parametrize(
    ('method_name', 'response'),
    [
        ('put_scenario_model_assignments', FakeResponse(207, {'results': []})),
        ('delete_scenario_model_assignments', FakeResponse(204, None)),
    ],
)
def test_500_model_assignment_records_go_as_one_request(
    monkeypatch: MonkeyPatch, method_name: str, response: FakeResponse
) -> None:
    recorder = install_recording_transport(monkeypatch, response)
    data: ItemList = [{'model': 'forecast', 'qualifierName': 'q', 'wellIds': [WELL_A]}] * 500

    getattr(make_offline_api(), method_name)(PROJECT_ID, SCENARIO_ID, data)

    assert len(recorder.calls) == 1
    assert recorder.calls[0].body == data


def test_lookup_table_unassign_over_500_ids_keeps_its_message(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch)
    well_ids = object_ids(501)

    with pytest.raises(ValueError, match=r'^well_ids holds 501 ids; the route takes at most 500 per request$'):
        make_offline_api().delete_scenario_lookup_table_assignment_by_id(PROJECT_ID, SCENARIO_ID, TABLE_ID, well_ids)

    assert recorder.calls == []


# List methods take the filters of their count twins


def test_econ_model_assignments_list_sends_the_filters(monkeypatch: MonkeyPatch) -> None:
    rows: ItemList = [{'qualifierName': 'q', 'scenario': SCENARIO_ID, 'wells': [WELL_A]}]
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, rows), FakeResponse(200, rows))
    api = make_offline_api()

    generic = api.get_econ_model_assignments_by_type_by_id(
        PROJECT_ID, 'FluidModel', MODEL_ID, {'wells': WELL_A, 'scenarios': SCENARIO_ID}
    )
    per_type = api.get_fluid_assignments_by_id(PROJECT_ID, MODEL_ID, filters={'wells': WELL_A})

    assert generic == rows
    assert per_type == rows
    assert recorder.calls[0].url.endswith(
        f'/econ-models/fluid-models/{MODEL_ID}/assignments?wells={WELL_A}&scenarios={SCENARIO_ID}'
    )
    assert recorder.calls[1].url.endswith(f'/econ-models/fluid-models/{MODEL_ID}/assignments?wells={WELL_A}')


def test_econ_model_assignments_list_without_filters_keeps_the_bare_url(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, []))

    assert make_offline_api().get_capex_assignments_by_id(PROJECT_ID, MODEL_ID) is None
    assert recorder.calls[0].url.endswith(f'/econ-models/capex/{MODEL_ID}/assignments')


def test_get_econ_runs_sends_the_filters(monkeypatch: MonkeyPatch) -> None:
    runs: ItemList = [{'id': RUN_ID, 'runDate': '2026-01-01', 'status': 'complete'}]
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, runs))

    result = make_offline_api().get_econ_runs(
        PROJECT_ID, SCENARIO_ID, add_combo_names=False, filters={'runDate[gt]': '2025-01-01', 'tags': 't'}
    )

    assert [run['id'] for run in result] == [RUN_ID]
    assert recorder.calls[0].url.endswith(f'/scenarios/{SCENARIO_ID}/econ-runs?runDate%5Bgt%5D=2025-01-01&tags=t')
    assert recorder.calls[0].params == {'take': 200}


def test_get_econ_run_onelines_sends_the_filters(monkeypatch: MonkeyPatch) -> None:
    onelines: ItemList = [{'id': 'o1', 'well': WELL_A, 'output': {'wellName': 'Sample Well 1'}}]
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, onelines))

    result = make_offline_api().get_econ_run_onelines(
        PROJECT_ID, SCENARIO_ID, RUN_ID, filters={'comboName': 'Sample Combo', 'well': WELL_A}
    )

    assert result == [{'id': 'o1', 'well': WELL_A, 'wellName': 'Sample Well 1'}]
    assert recorder.calls[0].url.endswith(f'/econ-runs/{RUN_ID}/one-liners?comboName=Sample%20Combo&well={WELL_A}')
    assert recorder.calls[0].params == {'take': 200}


# The 25,000 wellIds cap on the assignment PUTs


@pytest.mark.parametrize('method_name', ['put_scenario_model_assignments', 'put_scenario_econ_model_assignments'])
def test_more_than_25000_well_ids_across_records_are_refused(monkeypatch: MonkeyPatch, method_name: str) -> None:
    recorder = install_recording_transport(monkeypatch)
    well_ids = object_ids(12_501)
    data: ItemList = [{'model': 'forecast', 'qualifierName': 'q', 'wellIds': well_ids}] * 2

    with pytest.raises(ValueError, match=r'^data holds 25002 wellIds; the route takes at most 25000 per request$'):
        getattr(make_offline_api(), method_name)(PROJECT_ID, SCENARIO_ID, data)

    assert recorder.calls == []


@pytest.mark.parametrize('method_name', ['put_scenario_model_assignments', 'put_scenario_econ_model_assignments'])
def test_25000_well_ids_go_as_one_request(monkeypatch: MonkeyPatch, method_name: str) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(207, {'results': []}))
    well_ids = object_ids(12_500)
    data: ItemList = [{'model': 'forecast', 'qualifierName': 'q', 'wellIds': well_ids}, {'allWells': True}] * 2

    getattr(make_offline_api(), method_name)(PROJECT_ID, SCENARIO_ID, data)

    assert len(recorder.calls) == 1


# Well incrementals: `wellId` batches of 100, page size 500


def test_well_incrementals_split_more_than_100_well_ids(monkeypatch: MonkeyPatch) -> None:
    well_ids = object_ids(151)
    first: ItemList = [{'wellId': well_ids[0], 'incrementalIndexes': [1]}]
    second: ItemList = [{'wellId': well_ids[150], 'incrementalIndexes': [1]}]
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, first), FakeResponse(200, second))

    result = make_offline_api().get_scenario_well_incrementals(
        PROJECT_ID, SCENARIO_ID, {'wellId': [*well_ids, well_ids[0]], 'incrementalIndex': '1'}
    )

    assert result == first + second
    assert len(recorder.calls) == 2
    assert recorder.calls[0].url.count('wellId=') == 100
    assert recorder.calls[1].url.count('wellId=') == 51
    assert all('incrementalIndex=1' in call.url for call in recorder.calls)
    assert all(call.params == {'take': 500} for call in recorder.calls)


def test_well_incrementals_without_filters_sends_one_request_of_500(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, []))

    assert make_offline_api().get_scenario_well_incrementals(PROJECT_ID, SCENARIO_ID) == []
    assert recorder.calls[0].url.endswith(f'/scenarios/{SCENARIO_ID}/well-assignments/incrementals')
    assert recorder.calls[0].params == {'take': 500}


@pytest.mark.parametrize(
    ('arguments', 'message'),
    [
        ({'qualifier_name': ''}, 'qualifier_name'),
        ({'qualifier_name': '  '}, 'qualifier_name'),
        ({'scenario_id': ''}, 'scenario_id'),
    ],
)
def test_econ_model_unassign_refuses_a_blank_qualifier_or_scenario(
    monkeypatch: MonkeyPatch, arguments: dict[str, str], message: str
) -> None:
    """A blank `qualifierName` (or `scenarioId`) the route may read as absent would widen the unassign."""
    transport = install_recording_transport(monkeypatch)
    call: dict[str, Any] = {'scenario_id': 'sc', 'wells': ['w1'], **arguments}
    with pytest.raises(ValueError, match=message):
        make_offline_api().delete_econ_model_assignments_by_type_by_id('p', 'FluidModel', 'm', **call)
    assert transport.calls == []


def test_the_well_id_cap_counts_a_tuple_of_well_ids(monkeypatch: MonkeyPatch) -> None:
    """`wellIds` may be any sequence of ids (`_require_assignment_wells` accepts it), so the 25,000 cap counts
    a tuple too."""
    transport = install_recording_transport(monkeypatch)
    data: Any = [{'model': 'm', 'wellIds': tuple(object_ids(25_001))}]
    with pytest.raises(ValueError, match='wellIds'):
        make_offline_api().put_scenario_econ_model_assignments('p', 'sc', data)
    assert transport.calls == []
