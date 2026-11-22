"""Live dev round trips for scenario assignment writes (skip-by-default).

- Econ-model assignment (`Dates`, a multi-word type): PUT an assignment in a throwaway qualifier, read it
  back from the scenario grid, DELETE it through the query-filter route, confirm removal; once for one
  well, once for two wells unassigned with a list in ONE call (`X-Delete-Count: 2`).
- Saved combo: POST a throwaway saved combo of two combos, delete one by `combo_ids`, then the saved combo.
- Lookup-table assignment: create a throwaway scenario lookup table, assign it to one well in a throwaway
  qualifier, read it back (by id and as a list), and unassign it.

Every object is named with `FIXTURE_PREFIX` and a uuid suffix, and is deleted in a `finally`; each test
then checks that nothing of that name is left. Every qualifier is deleted with
`delete_scenario_qualifiers`, which must answer `X-Delete-Count: 1`.

Skipped unless CC_LIVE_TEST=1, ~/.combocurve/dev holds an unzipped ComboCurve credential download, and
CC_DEV_PROJECT_ID, CC_DEV_SCENARIO_ID and CC_DEV_DATES_MODEL_ID are set, so CI and other machines are
unaffected. The two-well, combo and lookup-table tests were written 2026-11-21 and have not been run yet.
"""

from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, cast

import pytest

from tests.live_support import FIXTURE_PREFIX, live_tests_enabled

if TYPE_CHECKING:
    from collections.abc import Iterator

    from combocurve_api_helper import ComboCurveAPI

# The dev target ids come from the environment, with no defaults: this repo is public.
PROJECT_ID = os.environ.get('CC_DEV_PROJECT_ID', '')
SCENARIO_ID = os.environ.get('CC_DEV_SCENARIO_ID', '')
DATES_MODEL_ID = os.environ.get('CC_DEV_DATES_MODEL_ID', '')

pytestmark = pytest.mark.skipif(
    not live_tests_enabled() or not (PROJECT_ID and SCENARIO_ID and DATES_MODEL_ID),
    reason=(
        'requires CC_LIVE_TEST=1, ~/.combocurve/dev credentials, and CC_DEV_PROJECT_ID, '
        'CC_DEV_SCENARIO_ID, CC_DEV_DATES_MODEL_ID'
    ),
)


def _fixture_name(kind: str) -> str:
    return f'{FIXTURE_PREFIX} {kind} {uuid.uuid4().hex[:8]}'


@contextmanager
def _fixture_qualifier(api: ComboCurveAPI) -> Iterator[str]:
    """A throwaway qualifier in the `dates` column; deleted on exit, which must delete exactly one."""
    name = _fixture_name('Q')
    api.post_scenario_qualifiers(PROJECT_ID, SCENARIO_ID, [{'econModel': 'dates', 'name': name}])
    try:
        yield name
    finally:
        headers = api.delete_scenario_qualifiers(PROJECT_ID, SCENARIO_ID, 'dates', name)
        assert headers.get('X-Delete-Count') == '1', dict(headers)


def _scenario_wells(api: ComboCurveAPI, count: int) -> list[str]:
    # Grid rows are dynamic live JSON; treat as Any rather than fight the deeply-typed ItemList union.
    grid: list[Any] = list(api.get_scenario_econ_model_assignments(PROJECT_ID, SCENARIO_ID))
    if len(grid) < count:
        pytest.skip(f'the dev scenario has fewer than {count} wells')
    return [str(row['wellId']) for row in grid[:count]]


def _dates_assignments(api: ComboCurveAPI, well: str) -> list[Any]:
    grid: list[Any] = list(api.get_scenario_econ_model_assignments(PROJECT_ID, SCENARIO_ID))
    row: Any = next((w for w in grid if str(w.get('wellId')) == well), None)
    if row is None:
        return []
    dates: Any = next((a for a in row.get('assumptions', []) if a.get('model') == 'dates'), None)
    return list(dates.get('assignments', [])) if dates else []


def _assigned_in(api: ComboCurveAPI, well: str, qualifier: str) -> bool:
    return any(
        a.get('qualifierName') == qualifier and a.get('econModelId') == DATES_MODEL_ID
        for a in _dates_assignments(api, well)
    )


def _assign_dates(api: ComboCurveAPI, qualifier: str, wells: list[str]) -> None:
    api.put_date_settings_assignments_by_id(
        PROJECT_ID,
        DATES_MODEL_ID,
        [{'scenario': SCENARIO_ID, 'allWells': False, 'qualifierName': qualifier, 'wells': wells}],
    )


def test_dates_assignment_roundtrip(dev_api: ComboCurveAPI) -> None:
    """PUT (multi-word econName) -> read -> query-filter DELETE -> read."""
    (well,) = _scenario_wells(dev_api, 1)
    with _fixture_qualifier(dev_api) as qualifier:
        _assign_dates(dev_api, qualifier, [well])
        assert _assigned_in(dev_api, well, qualifier), 'PUT assignment not found in the scenario grid'

        # DELETE via query filters (scenarioId + qualifierName + wells)
        dev_api.delete_date_settings_assignments_by_id(
            PROJECT_ID, DATES_MODEL_ID, scenario_id=SCENARIO_ID, qualifier_name=qualifier, wells=well
        )
        assert not _assigned_in(dev_api, well, qualifier), 'DELETE left the assignment'


def test_dates_unassign_of_two_wells_in_one_call(dev_api: ComboCurveAPI) -> None:
    """`wells` as a list goes as one repeated `wells` key per id; a comma-joined value was a live 400."""
    wells = _scenario_wells(dev_api, 2)
    with _fixture_qualifier(dev_api) as qualifier:
        _assign_dates(dev_api, qualifier, wells)
        assert all(_assigned_in(dev_api, well, qualifier) for well in wells), 'PUT did not assign both wells'

        responses = dev_api.delete_date_settings_assignments_by_id(
            PROJECT_ID, DATES_MODEL_ID, scenario_id=SCENARIO_ID, qualifier_name=qualifier, wells=wells
        )
        assert [response.headers.get('X-Delete-Count') for response in responses] == ['2']
        assert not any(_assigned_in(dev_api, well, qualifier) for well in wells), 'DELETE left an assignment'


def test_saved_combo_delete_by_combo_ids(dev_api: ComboCurveAPI) -> None:
    """Deleting one combo by id leaves the other; deleting the saved combo then leaves nothing.

    The server refuses a saved combo with no `selected: true` combo, and two combos that resolve to the
    same qualifiers ("Duplicate combo"), even under different names (dev, 2026-11-21). So combo B uses a
    fixture `dates` qualifier, and the saved combo is deleted before that qualifier.
    """
    saved_name = _fixture_name('Combo')

    def saved_combos() -> list[Any]:
        return list(dev_api.get_scenario_combos(PROJECT_ID, SCENARIO_ID, {'savedName': saved_name}))

    with _fixture_qualifier(dev_api) as qualifier:
        combos: list[Any] = [
            {'comboName': 'A', 'selected': True, 'qualifiers': [{'assumption': 'dates', 'qualifierName': 'Default'}]},
            {'comboName': 'B', 'selected': False, 'qualifiers': [{'assumption': 'dates', 'qualifierName': qualifier}]},
        ]
        try:
            created: Any = dev_api.post_scenario_combos(
                PROJECT_ID, SCENARIO_ID, [{'savedName': saved_name, 'combos': combos}]
            )
            assert created[0]['successCount'] == 1, created
            (saved,) = saved_combos()
            combo_ids = [str(entry['id']) for entry in saved['combos']]
            assert len(combo_ids) == 2, saved

            headers = dev_api.delete_scenario_combo(PROJECT_ID, SCENARIO_ID, saved_name, combo_ids=combo_ids[:1])
            assert headers.get('X-Delete-Count') == '1', dict(headers)
            (saved,) = saved_combos()
            assert [str(entry['id']) for entry in saved['combos']] == combo_ids[1:]
        finally:
            if saved_combos():
                headers = dev_api.delete_scenario_combo(PROJECT_ID, SCENARIO_ID, saved_name)
                assert headers.get('X-Delete-Count') == '1', dict(headers)
            assert saved_combos() == []


def test_lookup_table_assignment_read_and_unassign(dev_api: ComboCurveAPI) -> None:
    """Assign a throwaway lookup table in a throwaway (not active) qualifier, read it, unassign it.

    The unassign route has no qualifier parameter and clears only the column's ACTIVE qualifier, so for
    the fixture qualifier it answers `X-Delete-Count: 0` and changes nothing (documented on
    `delete_scenario_lookup_table_assignment_by_id`, verified 2026-11-12). Clearing the active qualifier
    would overwrite an assignment this test did not create, so that case is not tested here. The
    fixture qualifier is deleted before the table, which removes the assignment.
    """
    (well,) = _scenario_wells(dev_api, 1)
    table_name = _fixture_name('LT')

    def tables() -> list[Any]:
        return list(dev_api.get_scenario_lookup_tables(PROJECT_ID, {'name': table_name}))

    rule: dict[str, Any] = {'filter': [{'key': 'state', 'operator': 'equal', 'value': 'TX'}], 'dates': DATES_MODEL_ID}
    try:
        with _fixture_qualifier(dev_api) as qualifier:
            created = dev_api.post_scenario_lookup_tables(
                PROJECT_ID, [{'name': table_name, 'caseInsensitiveMatching': True, 'rules': [rule]}]
            )
            table_id = str(cast('Any', created)[0]['results'][0]['id'])
            dev_api.put_scenario_lookup_table_assignments(
                PROJECT_ID,
                SCENARIO_ID,
                [{'column': 'dates', 'lookUpTableId': table_id, 'wellIds': [well], 'qualifierName': qualifier}],
            )

            filters = {'column': 'dates', 'qualifierName': qualifier}
            by_id: Any = dev_api.get_scenario_lookup_table_assignment_by_id(PROJECT_ID, SCENARIO_ID, table_id, filters)
            assert well in [str(well_id) for well_id in by_id['wellIds']], by_id
            listed: Any = dev_api.get_scenario_lookup_table_assignments(PROJECT_ID, SCENARIO_ID, filters)
            assert any(well in [str(well_id) for well_id in entry.get('wellIds', [])] for entry in listed), listed

            headers = dev_api.delete_scenario_lookup_table_assignment_by_id(PROJECT_ID, SCENARIO_ID, table_id, [well])
            assert headers.get('X-Delete-Count') == '0', dict(headers)
    finally:
        for table in tables():
            dev_api.delete_scenario_lookup_table_by_id(PROJECT_ID, str(table['id']))
        assert tables() == []
