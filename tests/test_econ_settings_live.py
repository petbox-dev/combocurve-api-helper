"""Live dev round trip for the company econ settings and econ report settings (skip-by-default).

For each resource: POST a throwaway document, read it back by name and by id, PATCH it (by name), PUT it
(by name), and DELETE it. Self-cleaning: every document of the run's name is deleted in a `finally`, and
the test checks that none is left.

Skipped unless CC_LIVE_TEST=1 and ~/.combocurve/dev holds an unzipped ComboCurve credential download, so
CI and other machines are unaffected. The settings are company-scoped, so no project id is needed.
"""

from __future__ import annotations

import os
import pathlib
import uuid
from typing import Any

import pytest

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.config import find_native_credentials_directory

DEV = pathlib.Path.home() / '.combocurve' / 'dev'

# An econ setting names a real econ column and the category it belongs to. Those vocabularies are not
# in the Postman collection, and a wrong pair is refused, so the econ-settings test needs both from the
# environment (no default): the category, and a column key that belongs to it.
ECON_CATEGORY = os.environ.get('CC_DEV_ECON_CATEGORY', '')
ECON_COLUMN_KEY = os.environ.get('CC_DEV_ECON_COLUMN_KEY', '')

pytestmark = pytest.mark.skipif(
    os.environ.get('CC_LIVE_TEST') is None or find_native_credentials_directory(DEV) is None,
    reason='requires CC_LIVE_TEST=1 and ~/.combocurve/dev credentials',
)


@pytest.fixture(scope='module')
def api() -> ComboCurveAPI:
    return ComboCurveAPI.from_credentials_directory(DEV)


def _econ_setting(name: str, category: str) -> dict[str, Any]:
    return {
        'name': name,
        'categories': [{'category': category, 'columns': [{'key': ECON_COLUMN_KEY, 'selected': ['monthly']}]}],
    }


def _report_setting(name: str, rollup: bool) -> dict[str, Any]:
    return {'name': name, 'headers': [], 'allWellsAgg': True, 'rollUpEachLevel': rollup}


def _created_id(written: Any) -> str:
    result = written[0]['results'][0]
    assert result['status'] == 'Created', written
    return str(result['id'])


@pytest.mark.skipif(
    not (ECON_CATEGORY and ECON_COLUMN_KEY),
    reason='requires CC_DEV_ECON_CATEGORY and CC_DEV_ECON_COLUMN_KEY (a valid econ column of that category)',
)
def test_econ_settings_round_trip(api: ComboCurveAPI) -> None:
    name = f'API Helper Fixture ES {uuid.uuid4().hex[:8]}'
    try:
        created_id = _created_id(api.post_econ_settings([_econ_setting(name, ECON_CATEGORY)]))

        listed = api.get_econ_settings({'name': name})
        assert [str(setting['id']) for setting in listed] == [created_id]
        assert api.count_econ_settings({'name': name}) == 1
        assert str(api.get_econ_setting_by_id(created_id)['id']) == created_id

        patched: Any = api.patch_econ_settings([_econ_setting(name, ECON_CATEGORY)])
        assert patched[0]['results'][0]['status'] != 'Created', patched
        put: Any = api.put_econ_settings([_econ_setting(name, ECON_CATEGORY)])
        assert put[0]['results'][0]['id'] == created_id, put
        stored = api.get_econ_setting_by_id(created_id)
        assert str(stored['id']) == created_id, 'a PUT by name must replace the setting, not create one'
    finally:
        for setting in api.get_econ_settings({'name': name}):
            api.delete_econ_setting_by_id(str(setting['id']))
        assert api.get_econ_settings({'name': name}) == []


def test_econ_report_settings_round_trip(api: ComboCurveAPI) -> None:
    name = f'API Helper Fixture ERS {uuid.uuid4().hex[:8]}'
    try:
        created_id = _created_id(api.post_econ_report_settings([_report_setting(name, False)]))

        listed = api.get_econ_report_settings({'name': name})
        assert [str(setting['id']) for setting in listed] == [created_id]
        assert api.count_econ_report_settings({'name': name}) == 1
        assert str(api.get_econ_report_setting_by_id(created_id)['id']) == created_id

        api.patch_econ_report_settings([{'name': name, 'rollUpEachLevel': True}])
        patched = api.get_econ_report_setting_by_id(created_id)
        assert patched['rollUpEachLevel'] is True

        put: Any = api.put_econ_report_settings([_report_setting(name, False)])
        assert put[0]['results'][0]['id'] == created_id, put
        stored = api.get_econ_report_setting_by_id(created_id)
        assert stored['rollUpEachLevel'] is False
    finally:
        for setting in api.get_econ_report_settings({'name': name}):
            api.delete_econ_report_setting_by_id(str(setting['id']))
        assert api.get_econ_report_settings({'name': name}) == []
