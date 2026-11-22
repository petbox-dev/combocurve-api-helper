"""Live dev round trips for production comments, production comment types and the directional-survey batch
upsert (skip-by-default).

Production comments, per scope (company and project): POST a throwaway comment on the first well of the dev
project, read it back (list by well, count, by id), PUT and PATCH it, DELETE it by id, then check that no
fixture comment of the run is left. Every fixture comment is deleted in a `finally`. The tenant must have
production comments enabled: on the dev tenant every comment route answers 404
`ProductionCommentsDisabledError` (2026-11-21), and these tests then skip.

Comment types: read only (the PATCH changes a company configuration that other users see).

Directional-survey batch: upsert a throwaway survey on the first well of the dev project, only when that well
has no survey; upsert it again; delete it in a `finally` and check that none is left.

Skipped unless CC_LIVE_TEST=1, ~/.combocurve/dev holds an unzipped ComboCurve credential download, and
CC_DEV_PROJECT_ID is set.
"""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING, Any

import pytest

from tests.live_support import FIXTURE_PREFIX, live_tests_enabled

if TYPE_CHECKING:
    from combocurve_api_helper import ComboCurveAPI

PROJECT_ID = os.environ.get('CC_DEV_PROJECT_ID', '')

pytestmark = pytest.mark.skipif(
    not live_tests_enabled() or not PROJECT_ID,
    reason='requires CC_LIVE_TEST=1, ~/.combocurve/dev credentials and CC_DEV_PROJECT_ID',
)


@pytest.fixture(scope='module')
def well(dev_api: ComboCurveAPI) -> dict[str, Any]:
    response = dev_api._request_with_retry('get', dev_api.get_project_wells_url(PROJECT_ID), params={'take': 1})
    response.raise_for_status()
    wells = response.json()
    if not wells:
        pytest.skip('the dev project has no wells')
    return dict(wells[0])


def _skip_unless_comments_enabled(dev_api: ComboCurveAPI) -> None:
    response = dev_api._request_with_retry('get', dev_api.get_company_production_comments_url(), params={'take': 1})
    if response.status_code == 404 and 'ProductionCommentsDisabledError' in response.text:
        pytest.skip('production comments are not enabled on this tenant')
    response.raise_for_status()


def _created_id(written: Any) -> str:
    result = written[0]['results'][0]
    assert 200 <= int(result['code']) < 300, written
    return str(result['id'])


def _method(dev_api: ComboCurveAPI, scope: str, name: str) -> Any:
    """The bound method `name` of `scope`, with the project id already applied for the project scope."""
    method = getattr(dev_api, name.format(scope=scope))
    if scope == 'company':
        return method
    return lambda *args, **kwargs: method(PROJECT_ID, *args, **kwargs)


def _fixture_comments(dev_api: ComboCurveAPI, scope: str, well_id: str, note: str) -> list[dict[str, Any]]:
    comments = _method(dev_api, scope, 'get_{scope}_production_comments')({'well': well_id})
    return [comment for comment in comments if str(comment.get('note', '')).startswith(note)]


@pytest.mark.parametrize('scope', ['company', 'project'])
def test_production_comment_round_trip(dev_api: ComboCurveAPI, well: dict[str, Any], scope: str) -> None:
    _skip_unless_comments_enabled(dev_api)
    well_id = str(well['id'])
    note = f'{FIXTURE_PREFIX} {uuid.uuid4().hex[:8]}'
    record = {
        'well': well_id,
        'commentType': 'prod_comment_type_0',
        'startDate': '2020-01-01T00:00:00.000Z',
        'endDate': '2020-01-31T00:00:00.000Z',
        'note': note,
    }
    try:
        created_id = _created_id(_method(dev_api, scope, 'post_{scope}_production_comments')([record]))

        listed = [str(comment['id']) for comment in _fixture_comments(dev_api, scope, well_id, note)]
        assert listed == [created_id]
        assert _method(dev_api, scope, 'count_{scope}_production_comments')({'well': well_id}) >= 1
        assert str(_method(dev_api, scope, 'get_{scope}_production_comment_by_id')(created_id)['id']) == created_id

        _method(dev_api, scope, 'put_{scope}_production_comments')([dict(record, id=created_id, note=f'{note} put')])
        assert _method(dev_api, scope, 'get_{scope}_production_comment_by_id')(created_id)['note'] == f'{note} put'

        _method(dev_api, scope, 'patch_{scope}_production_comments')([{'id': created_id, 'note': f'{note} patch'}])
        assert _method(dev_api, scope, 'get_{scope}_production_comment_by_id')(created_id)['note'] == f'{note} patch'

        _method(dev_api, scope, 'delete_{scope}_production_comment_by_id')(created_id)
    finally:
        for comment in _fixture_comments(dev_api, scope, well_id, note):
            _method(dev_api, scope, 'delete_{scope}_production_comment_by_id')(str(comment['id']))
        assert _fixture_comments(dev_api, scope, well_id, note) == []


def test_production_comment_types_read(dev_api: ComboCurveAPI) -> None:
    configuration: Any = dev_api.get_production_comment_types()
    keys = [entry['key'] for entry in configuration['productionCommentTypes']]
    assert keys == [f'prod_comment_type_{i}' for i in range(15)]


def test_directional_survey_batch_round_trip(dev_api: ComboCurveAPI, well: dict[str, Any]) -> None:
    well_id = str(well['id'])
    if dev_api.count_directional_surveys({'well': well_id}) != 0:
        pytest.skip('the first dev project well already has a directional survey; it is not touched')
    latitude = well.get('surfaceLatitude') or 31.0
    longitude = well.get('surfaceLongitude') or -103.0

    def survey(depth: float) -> dict[str, Any]:
        return {
            'chosenID': well['chosenID'],
            'dataSource': well['dataSource'],
            'spatialDataType': 'WGS84',
            'measuredDepth': [0.0, depth],
            'trueVerticalDepth': [0.0, depth],
            'azimuth': [0.0, 0.0],
            'inclination': [0.0, 0.0],
            'deviationEW': [0.0, 0.0],
            'deviationNS': [0.0, 0.0],
            'latitude': [latitude, latitude],
            'longitude': [longitude, longitude],
            'projectID': PROJECT_ID,
        }

    try:
        created: Any = dev_api.post_directional_surveys_batch([survey(100.0)])
        assert created[0]['results'][0]['code'] == 201, created
        updated: Any = dev_api.post_directional_surveys_batch([survey(200.0)])
        assert updated[0]['results'][0]['code'] == 200, updated
        surveys = dev_api.get_directional_surveys({'well': well_id})
        assert len(surveys) == 1
        assert surveys[0]['measuredDepth'] == [0, 200]
    finally:
        # Only the survey this test wrote (the well had none before; its depths are the fixture's), so a
        # survey another writer added meanwhile, or rows of a filter the route ignored, are left alone.
        for stored in dev_api.get_directional_surveys({'well': well_id}):
            if str(stored.get('well')) == well_id and stored.get('measuredDepth') in ([0, 100], [0, 200]):
                dev_api.delete_directional_survey_by_id(str(stored['id']))
        assert dev_api.count_directional_surveys({'well': well_id}) == 0
