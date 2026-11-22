"""Live dev round trip for the company and project formations (skip-by-default).

For each scope: PUT a throwaway formation (an asynchronous import), poll its job until it is final, read it
back (list by name, count with HEAD and with GET `/head`, by id, points), PATCH its metadata, and DELETE it.
Self-cleaning: every formation of the run's name is deleted in a `finally`, and the test checks that none is
left.

The points are a synthetic 3 x 3 grid; nothing in them comes from a real well or project. Skipped unless
CC_LIVE_TEST=1 and ~/.combocurve/dev holds an unzipped ComboCurve credential download; the project test also
needs CC_DEV_PROJECT_ID (no default: a real id must not sit in this public repo).
"""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING

import pytest

from tests.live_support import FIXTURE_PREFIX, LIVE_TEST_SKIP_REASON, live_tests_enabled

if TYPE_CHECKING:
    from combocurve_api_helper import ComboCurveAPI
    from combocurve_api_helper.base import Item, ItemList

PROJECT_ID = os.environ.get('CC_DEV_PROJECT_ID', '')
JOB_POLL_SECONDS = 3.0
JOB_TIMEOUT_SECONDS = 180.0

pytestmark = pytest.mark.skipif(not live_tests_enabled(), reason=LIVE_TEST_SKIP_REASON)


@pytest.fixture
def api(dev_api: ComboCurveAPI) -> ComboCurveAPI:
    """The session's shared dev client (`dev_api`)."""
    return dev_api


def _grid_points() -> ItemList:
    """A synthetic 3 x 3 grid of points, top and base in feet TVD."""
    return [
        {'latitude': 31.0 + 0.01 * i, 'longitude': -102.0 + 0.01 * j, 'topTvd': 8000.0 + i, 'baseTvd': 8100.0 + i}
        for i in range(3)
        for j in range(3)
    ]


def _wait_for_job(api: ComboCurveAPI, job_id: str, project_id: str | None) -> Item:
    """The formations job at its final status, through the public wait methods."""
    if project_id is None:
        return api.wait_for_company_formations_job(job_id, JOB_TIMEOUT_SECONDS, JOB_POLL_SECONDS)
    return api.wait_for_project_formations_job(project_id, job_id, JOB_TIMEOUT_SECONDS, JOB_POLL_SECONDS)


def _round_trip(api: ComboCurveAPI, project_id: str | None) -> None:
    name = f'{FIXTURE_PREFIX} Formation {uuid.uuid4().hex[:8]}'
    formation: Item = {'name': name, 'points': _grid_points(), 'color': '#123abc'}

    def listed() -> ItemList:
        if project_id is None:
            return api.get_company_formations({'scope': 'company', 'name': name})
        return api.get_project_formations(project_id, {'name': name})

    try:
        if project_id is None:
            started = api.put_company_formations(formation, overlap_handling='trim')
        else:
            started = api.put_project_formations(project_id, [formation], overlap_handling='trim')
        job = _wait_for_job(api, str(started['jobId']), project_id)
        assert job['status'] == 'successful', job

        [summary] = listed()
        formation_id = str(summary['id'])
        assert summary['pointCount'] == len(_grid_points())
        if project_id is None:
            assert api.count_company_formations({'scope': 'company', 'name': name}) == 1
            assert api.count_company_formations_with_get({'scope': 'company', 'name': name}) == 1
            assert str(api.get_company_formation_by_id(formation_id)['id']) == formation_id
            points = api.get_company_formation_points(formation_id)
            api.patch_company_formations({'id': formation_id, 'enabled': False, 'maxDepth': 9000})
            patched = api.get_company_formation_by_id(formation_id)
        else:
            assert api.count_project_formations(project_id, {'name': name}) == 1
            assert api.count_project_formations_with_get(project_id, {'name': name}) == 1
            assert str(api.get_project_formation_by_id(project_id, formation_id)['id']) == formation_id
            points = api.get_project_formation_points(project_id, formation_id)
            api.patch_project_formations(project_id, [{'id': formation_id, 'enabled': False, 'maxDepth': 9000}])
            patched = api.get_project_formation_by_id(project_id, formation_id)
        assert len(points) == len(_grid_points())
        assert patched['enabled'] is False
        assert patched['maxDepth'] == 9000
    finally:
        # Only this run's formations: the name filter is the server's, so check the name here too.
        for leftover in (formation for formation in listed() if formation.get('name') == name):
            if project_id is None:
                api.delete_company_formation_by_id(str(leftover['id']))
            else:
                api.delete_project_formation_by_id(project_id, str(leftover['id']))
        assert listed() == []


def test_company_formations_round_trip(api: ComboCurveAPI) -> None:
    _round_trip(api, None)


@pytest.mark.skipif(not PROJECT_ID, reason='requires CC_DEV_PROJECT_ID')
def test_project_formations_round_trip(api: ComboCurveAPI) -> None:
    _round_trip(api, PROJECT_ID)
