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
import pathlib
import time
import uuid
from typing import TYPE_CHECKING

import pytest

from combocurve_api_helper.config import find_native_credentials_directory
from combocurve_api_helper.formations import Formations

if TYPE_CHECKING:
    from combocurve_api_helper.base import Item, ItemList

DEV = pathlib.Path.home() / '.combocurve' / 'dev'
PROJECT_ID = os.environ.get('CC_DEV_PROJECT_ID', '')
RUNNING_JOB_STATUSES = ('pending', 'running')  # a job leaves these for its final status (`successful`)
JOB_POLL_SECONDS = 3.0
JOB_TIMEOUT_SECONDS = 180.0

pytestmark = pytest.mark.skipif(
    os.environ.get('CC_LIVE_TEST') is None or find_native_credentials_directory(DEV) is None,
    reason='requires CC_LIVE_TEST=1 and ~/.combocurve/dev credentials',
)


@pytest.fixture(scope='module')
def api() -> Formations:
    return Formations.from_credentials_directory(DEV)


def _grid_points() -> ItemList:
    """A synthetic 3 x 3 grid of points, top and base in feet TVD."""
    return [
        {'latitude': 31.0 + 0.01 * i, 'longitude': -102.0 + 0.01 * j, 'topTvd': 8000.0 + i, 'baseTvd': 8100.0 + i}
        for i in range(3)
        for j in range(3)
    ]


def _wait_for_job(api: Formations, job_id: str, project_id: str | None) -> Item:
    deadline = time.monotonic() + JOB_TIMEOUT_SECONDS
    while True:
        if project_id is None:
            job = api.get_company_formations_job(job_id)
        else:
            job = api.get_project_formations_job(project_id, job_id)
        if job.get('status') not in RUNNING_JOB_STATUSES or time.monotonic() > deadline:
            return job
        time.sleep(JOB_POLL_SECONDS)


def _round_trip(api: Formations, project_id: str | None) -> None:
    name = f'API Helper Fixture Formation {uuid.uuid4().hex[:8]}'
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
        for leftover in listed():
            if project_id is None:
                api.delete_company_formation_by_id(str(leftover['id']))
            else:
                api.delete_project_formation_by_id(project_id, str(leftover['id']))
        assert listed() == []


def test_company_formations_round_trip(api: Formations) -> None:
    _round_trip(api, None)


@pytest.mark.skipif(not PROJECT_ID, reason='requires CC_DEV_PROJECT_ID')
def test_project_formations_round_trip(api: Formations) -> None:
    _round_trip(api, PROJECT_ID)
