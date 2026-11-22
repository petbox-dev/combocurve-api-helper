"""Live dev round trip for the shapefile (map layer) routes (skip-by-default).

Reads the dev layers at both scopes, then uploads a one-point synthetic shapefile zip into the dev project
through the three upload steps, follows the job, reads the layer back at both scopes (metadata, features,
counts), PATCHes it, creates a second layer from GeoJSON, and deletes both (one through each delete
route). A second test uploads through the company route, PATCHes `scope` and `projectIds` to share the
layer with CC_DEV_PROJECT_ID and one other dev project (the first other one `get_projects` lists; skipped
when there is none), and deletes it through each project's route (unlink, then delete job). A third uploads
a zip with a bad `.prj`, whose job fails. Self-cleaning: every layer of a test's name prefix is deleted in a
`finally`, and the test checks that none is left. Only the fixture layers' project links are changed.

Skipped unless CC_LIVE_TEST=1, ~/.combocurve/dev holds an unzipped ComboCurve credential download, and
CC_DEV_PROJECT_ID is set. The zip is written by hand here (no shapefile library is a dependency).
"""

from __future__ import annotations

import io
import os
import struct
import uuid
import zipfile
from typing import TYPE_CHECKING

import pytest

from tests.live_support import FIXTURE_PREFIX, live_tests_enabled

if TYPE_CHECKING:
    from combocurve_api_helper import ComboCurveAPI
    from combocurve_api_helper.base import Item

PROJECT_ID = os.environ.get('CC_DEV_PROJECT_ID', '')

pytestmark = pytest.mark.skipif(
    not live_tests_enabled() or not PROJECT_ID,
    reason='requires CC_LIVE_TEST=1, ~/.combocurve/dev credentials and CC_DEV_PROJECT_ID',
)

WGS84_PRJ = (
    'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],'
    'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'
)


def one_point_shapefile_zip(longitude: float, latitude: float, label: str) -> bytes:
    """A zip of a one-point shapefile in WGS84 (`.shp`, `.shx`, `.dbf` with one text field `LABEL`, `.prj`),
    written from the ESRI shapefile and dBase III layouts."""

    def file_header(file_bytes: int) -> bytes:
        bounding_box = (longitude, latitude, longitude, latitude, 0.0, 0.0, 0.0, 0.0)
        # File code 9994 and the length in 16-bit words are big-endian; version 1000, shape type 1 (point)
        # and the bounding box are little-endian.
        return (
            struct.pack('>7i', 9994, 0, 0, 0, 0, 0, file_bytes // 2)
            + struct.pack('<2i', 1000, 1)
            + struct.pack('<8d', *bounding_box)
        )

    point = struct.pack('<i2d', 1, longitude, latitude)
    record = struct.pack('>2i', 1, len(point) // 2) + point
    shp = file_header(100 + len(record)) + record
    shx = file_header(100 + 8) + struct.pack('>2i', 50, len(point) // 2)

    field_length = 20
    dbf = (
        struct.pack('<4BIHH20x', 3, 126, 1, 1, 1, 32 + 32 + 1, 1 + field_length)
        + struct.pack('<11sc4xBB14x', b'LABEL', b'C', field_length, 0)
        + b'\r'
        + b' '
        + label.encode('ascii').ljust(field_length)[:field_length]
        + b'\x1a'
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('fixture.shp', shp)
        archive.writestr('fixture.shx', shx)
        archive.writestr('fixture.dbf', dbf)
        archive.writestr('fixture.prj', WGS84_PRJ)
    return buffer.getvalue()


@pytest.fixture
def api(dev_api: ComboCurveAPI) -> ComboCurveAPI:
    """The session's shared dev client (`dev_api`)."""
    return dev_api


def test_reads_at_both_scopes(api: ComboCurveAPI) -> None:
    company_layers = api.get_company_shapefiles()
    assert api.count_company_shapefiles() == len(company_layers)
    assert api.count_company_shapefiles_with_get() == len(company_layers)
    project_layers = api.get_project_shapefiles(PROJECT_ID)
    assert api.count_project_shapefiles(PROJECT_ID) == len(project_layers)
    assert api.count_project_shapefiles_with_get(PROJECT_ID) == len(project_layers)
    for layer in company_layers[:1]:
        assert api.get_company_shapefile_by_id(str(layer['id']))['id'] == layer['id']
        assert isinstance(api.get_company_shapefile_features(str(layer['id']), {'take': '1'}), list)
    for layer in project_layers[:1]:
        assert api.get_project_shapefile_by_id(PROJECT_ID, str(layer['id']))['id'] == layer['id']


def test_upload_patch_and_delete_round_trip(api: ComboCurveAPI) -> None:
    prefix = f'{FIXTURE_PREFIX} {uuid.uuid4().hex[:8]}'
    try:
        layer = api.upload_project_shapefile(
            PROJECT_ID, one_point_shapefile_zip(-100.5, 31.25, 'A'), {'name': f'{prefix} zip'}
        )
        layer_id = str(layer['id'])
        assert layer['shapeType'] == 'POINT'
        assert layer['projectIds'] == [PROJECT_ID]
        assert str(api.get_company_shapefile_by_id(layer_id)['id']) == layer_id

        features = api.get_project_shapefile_features(PROJECT_ID, layer_id)
        assert features == api.get_company_shapefile_features(layer_id)
        assert [feature['properties'] for feature in features] == [{'LABEL': 'A'}]

        name_filter = {'name': f'{prefix} zip'}
        assert api.count_company_shapefiles(name_filter) == 1
        assert api.count_project_shapefiles_with_get(PROJECT_ID, name_filter) == 1
        assert [str(found['id']) for found in api.get_project_shapefiles(PROJECT_ID, name_filter)] == [layer_id]

        patched = api.patch_company_shapefiles({'id': layer_id, 'description': 'patched'})
        assert patched[0]['successCount'] == 1, patched
        assert api.get_project_shapefile_by_id(PROJECT_ID, layer_id)['description'] == 'patched'

        geojson: Item = {
            'name': f'{prefix} geojson',
            'type': 'FeatureCollection',
            'features': [
                {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [-100.0, 31.0]}, 'properties': {}}
            ],
        }
        created = api.wait_for_project_shapefile_job(
            PROJECT_ID, str(api.post_project_shapefiles(PROJECT_ID, geojson)['jobId'])
        )
        assert created['status'] == 'successful', created
        result = created['result']
        assert isinstance(result, dict), created
        geojson_layer_id = str(result['shapefileId'])

        deleted = api.delete_company_shapefile_by_id(geojson_layer_id)
        assert api.wait_for_company_shapefile_job(str(deleted['jobId']))['status'] == 'successful'
        deleted = api.delete_project_shapefile_by_id(PROJECT_ID, layer_id)
        assert api.wait_for_project_shapefile_job(PROJECT_ID, str(deleted['jobId']))['status'] == 'successful'
    finally:
        for leftover in api.get_company_shapefiles():
            if str(leftover['name']).startswith(prefix):
                job = api.delete_company_shapefile_by_id(str(leftover['id']))
                api.wait_for_company_shapefile_job(str(job['jobId']))
        assert [found for found in api.get_company_shapefiles() if str(found['name']).startswith(prefix)] == []


def bad_projection_shapefile_zip() -> bytes:
    """The one-point zip with an unreadable `.prj`: the import route accepts it (202) and the job fails."""
    with zipfile.ZipFile(io.BytesIO(one_point_shapefile_zip(-100.5, 31.25, 'A'))) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    files['fixture.prj'] = b'NOT A PROJECTION'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def delete_layers_named(api: ComboCurveAPI, prefix: str) -> None:
    """Delete every layer whose name starts with `prefix` through the company route, and check none is left."""
    for leftover in api.get_company_shapefiles():
        if str(leftover['name']).startswith(prefix):
            job = api.delete_company_shapefile_by_id(str(leftover['id']))
            api.wait_for_company_shapefile_job(str(job['jobId']))
    assert [found for found in api.get_company_shapefiles() if str(found['name']).startswith(prefix)] == []


def test_company_upload_scope_patch_and_shared_project_delete(api: ComboCurveAPI) -> None:
    """Company-route zip upload, PATCH of `scope` and `projectIds`, and the project-route delete of a layer
    shared with a second project (200 `unlinked`) and then of its last project (202 job)."""
    other_project_id = next(
        (str(project['id']) for project in api.get_projects() if str(project['id']) != PROJECT_ID), None
    )
    if other_project_id is None:
        pytest.skip('needs a second dev project')
    prefix = f'{FIXTURE_PREFIX} {uuid.uuid4().hex[:8]}'
    try:
        layer = api.upload_company_shapefile(
            one_point_shapefile_zip(-100.5, 31.25, 'A'), {'name': f'{prefix} company', 'scope': 'company'}
        )
        layer_id = str(layer['id'])
        assert (layer['scope'], layer['projectIds']) == ('company', [])

        refused = api.patch_company_shapefiles({'id': layer_id, 'scope': 'project'})
        assert refused[0]['failedCount'] == 1, refused
        both_projects = [PROJECT_ID, other_project_id]
        patched = api.patch_company_shapefiles({'id': layer_id, 'scope': 'project', 'projectIds': both_projects})
        assert patched[0]['successCount'] == 1, patched
        layer = api.get_company_shapefile_by_id(layer_id)
        project_ids = layer['projectIds']
        assert isinstance(project_ids, list), layer
        assert (layer['scope'], sorted(map(str, project_ids))) == ('project', sorted(both_projects))
        assert str(api.get_project_shapefile_by_id(other_project_id, layer_id)['id']) == layer_id

        unlinked = api.delete_project_shapefile_by_id(PROJECT_ID, layer_id)
        assert unlinked['result'] == 'unlinked', unlinked
        assert unlinked['remainingProjectIds'] == [other_project_id]
        assert api.get_project_shapefiles(PROJECT_ID, {'name': f'{prefix} company'}) == []
        assert str(api.get_project_shapefile_by_id(other_project_id, layer_id)['id']) == layer_id

        deleted = api.delete_project_shapefile_by_id(other_project_id, layer_id)
        job = api.wait_for_project_shapefile_job(other_project_id, str(deleted['jobId']))
        assert job['status'] == 'successful', job
        assert api.count_company_shapefiles({'name': f'{prefix} company'}) == 0
    finally:
        delete_layers_named(api, prefix)


def test_a_failed_upload_job_raises_with_the_job(api: ComboCurveAPI) -> None:
    prefix = f'{FIXTURE_PREFIX} {uuid.uuid4().hex[:8]}'
    try:
        with pytest.raises(RuntimeError, match=r"'status': 'failed'.*'error': 'Error uploading to Mapbox"):
            api.upload_company_shapefile(bad_projection_shapefile_zip(), {'name': f'{prefix} bad', 'scope': 'company'})
    finally:
        delete_layers_named(api, prefix)
