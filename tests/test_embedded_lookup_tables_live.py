"""Live dev round trip for the embedded-lookup-table writes (skip-by-default).

For the project and the company routes: POST a throwaway `expenses` table, read it back by name and
by id, PUT a changed rule value (by name), and DELETE it. Self-cleaning: the table is deleted in a
`finally`, and the test checks that no table of that name is left.

Skipped unless CC_LIVE_TEST=1, ~/.combocurve/dev holds an unzipped ComboCurve credential download, and
CC_DEV_PROJECT_ID is set, so CI and other machines are unaffected. Passed against dev on 2026-11-13.
"""

from __future__ import annotations

import os
import pathlib
import uuid
from typing import Any, cast

import pytest

from combocurve_api_helper import ComboCurveAPI, Item
from combocurve_api_helper.config import find_native_credentials_directory

DEV = pathlib.Path.home() / '.combocurve' / 'dev'

# The dev target id comes from the environment, with no default: this repo is public.
PROJECT_ID = os.environ.get('CC_DEV_PROJECT_ID', '')

pytestmark = pytest.mark.skipif(
    not os.environ.get('CC_LIVE_TEST') or find_native_credentials_directory(DEV) is None or not PROJECT_ID,
    reason='requires CC_LIVE_TEST=1, ~/.combocurve/dev credentials, and CC_DEV_PROJECT_ID',
)


@pytest.fixture(scope='module')
def api() -> ComboCurveAPI:
    return ComboCurveAPI.from_credentials_directory(DEV)


def _table(name: str, value: float) -> Item:
    """One `expenses` row whose `value` cell the rule fills (`"lookup_by"`), and one rule on `state`."""
    return {
        'type': 'expenses',
        'name': name,
        'caseInsensitiveMatching': True,
        'rows': [
            {
                'rowNumber': 1,
                'key': 'oil',
                'category': 'processing',
                'criteria': 'entire_well_life',
                'unit': 'dollar_per_bbl',
                'calculation': 'nri',
                'period': ['Flat'],
                'value': 'lookup_by',
            }
        ],
        'rules': [
            {
                'filter': [{'key': 'state', 'operator': 'equal', 'value': 'TX'}],
                'values': [{'rowNumber': 1, 'value': [value]}],
            }
        ],
    }


def _rule_value(table: Item) -> Any:
    return cast('Any', table['rules'])[0]['values'][0]['value']


@pytest.mark.parametrize('scope', ['project', 'company'])
def test_embedded_lookup_table_round_trip(api: ComboCurveAPI, scope: str) -> None:
    name = f'API Helper Fixture ELT {uuid.uuid4().hex[:8]}'
    project = scope == 'project'

    def find_by_name() -> list[Item]:
        if project:
            return api.get_embedded_lookup_tables(PROJECT_ID, {'name': name})
        return api.get_company_embedded_lookup_tables({'name': name})

    created_id = ''
    try:
        if project:
            created = api.post_embedded_lookup_tables(PROJECT_ID, [_table(name, 1.5)])
        else:
            created = api.post_company_embedded_lookup_tables([_table(name, 1.5)])
        result = cast('Any', created)[0]['results'][0]
        assert result['status'] == 'Created', created
        created_id = str(result['id'])  # the POST returns the new id (verified 2026-11-13)

        listed = find_by_name()
        assert [str(table['id']) for table in listed] == [created_id]
        assert _rule_value(listed[0]) == [1.5]

        if project:
            api.put_embedded_lookup_tables(PROJECT_ID, [_table(name, 2.25)])
            stored = api.get_embedded_lookup_table_by_id(PROJECT_ID, created_id)
        else:
            api.put_company_embedded_lookup_tables([_table(name, 2.25)])
            stored = api.get_company_embedded_lookup_table_by_id(created_id)
        assert str(stored['id']) == created_id, 'a PUT by name must replace the table, not create one'
        assert _rule_value(stored) == [2.25]
    finally:
        # Delete every table of this run's name, not only `created_id`: a POST whose response was
        # lost, or a PUT that created a second table, leaves one `created_id` does not name. The
        # name is unique to this run (uuid suffix), so nothing else matches it.
        delete_counts = []
        for table in find_by_name():
            if project:
                headers = api.delete_embedded_lookup_table_by_id(PROJECT_ID, str(table['id']))
            else:
                headers = api.delete_company_embedded_lookup_table_by_id(str(table['id']))
            delete_counts.append(headers.get('X-Delete-Count'))
        assert find_by_name() == []
        assert delete_counts == ['1'] * len(delete_counts)
