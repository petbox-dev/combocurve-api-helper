"""Live dev round trip for the company econ settings and econ report settings (skip-by-default).

For each resource: POST a throwaway document, read it back by name and by id, PATCH it (by name), PUT it
(by name), and DELETE it. Self-cleaning: every document of the run's name is deleted in a `finally`, and
the test checks that none is left.

Skipped unless CC_LIVE_TEST=1 and ~/.combocurve/dev holds an unzipped ComboCurve credential download, so
CI and other machines are unaffected. The settings are company-scoped, so no project id is needed.
"""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING, Any

import pytest

from tests.live_support import FIXTURE_PREFIX, LIVE_TEST_SKIP_REASON, live_tests_enabled

if TYPE_CHECKING:
    from combocurve_api_helper import ComboCurveAPI

# An econ setting names a real econ column and the category it belongs to. Those vocabularies are not
# in the Postman collection, and a wrong pair is refused, so the econ-settings test needs both from the
# environment (no default): the category, and a column key that belongs to it.
ECON_CATEGORY = os.environ.get('CC_DEV_ECON_CATEGORY', '')
ECON_COLUMN_KEY = os.environ.get('CC_DEV_ECON_COLUMN_KEY', '')

pytestmark = pytest.mark.skipif(not live_tests_enabled(), reason=LIVE_TEST_SKIP_REASON)


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
def test_econ_settings_round_trip(dev_api: ComboCurveAPI) -> None:
    name = f'{FIXTURE_PREFIX} ES {uuid.uuid4().hex[:8]}'
    try:
        created_id = _created_id(dev_api.post_econ_settings([_econ_setting(name, ECON_CATEGORY)]))

        listed = dev_api.get_econ_settings({'name': name})
        assert [str(setting['id']) for setting in listed] == [created_id]
        assert dev_api.count_econ_settings({'name': name}) == 1
        assert str(dev_api.get_econ_setting_by_id(created_id)['id']) == created_id

        patched: Any = dev_api.patch_econ_settings([_econ_setting(name, ECON_CATEGORY)])
        assert patched[0]['results'][0]['status'] != 'Created', patched
        put: Any = dev_api.put_econ_settings([_econ_setting(name, ECON_CATEGORY)])
        assert put[0]['results'][0]['id'] == created_id, put
        stored = dev_api.get_econ_setting_by_id(created_id)
        assert str(stored['id']) == created_id, 'a PUT by name must replace the setting, not create one'
    finally:
        for setting in dev_api.get_econ_settings({'name': name}):
            dev_api.delete_econ_setting_by_id(str(setting['id']))
        assert dev_api.get_econ_settings({'name': name}) == []


def test_econ_report_settings_round_trip(dev_api: ComboCurveAPI) -> None:
    name = f'{FIXTURE_PREFIX} ERS {uuid.uuid4().hex[:8]}'
    try:
        created_id = _created_id(dev_api.post_econ_report_settings([_report_setting(name, False)]))

        listed = dev_api.get_econ_report_settings({'name': name})
        assert [str(setting['id']) for setting in listed] == [created_id]
        assert dev_api.count_econ_report_settings({'name': name}) == 1
        assert str(dev_api.get_econ_report_setting_by_id(created_id)['id']) == created_id

        dev_api.patch_econ_report_settings([{'name': name, 'rollUpEachLevel': True}])
        patched = dev_api.get_econ_report_setting_by_id(created_id)
        assert patched['rollUpEachLevel'] is True

        put: Any = dev_api.put_econ_report_settings([_report_setting(name, False)])
        assert put[0]['results'][0]['id'] == created_id, put
        stored = dev_api.get_econ_report_setting_by_id(created_id)
        assert stored['rollUpEachLevel'] is False
    finally:
        for setting in dev_api.get_econ_report_settings({'name': name}):
            dev_api.delete_econ_report_setting_by_id(str(setting['id']))
        assert dev_api.get_econ_report_settings({'name': name}) == []
