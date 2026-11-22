"""Offline checks for the shapefile (map layer) routes: the url of each scope, the request each public method
sends, the local refusals, the signed-url upload (no ComboCurve credentials leave for another host) and the
job polling.
"""

import io
import time
import zipfile
from pathlib import Path
from typing import Any

import pytest

from combocurve_api_helper import shapefiles as shapefiles_module
from combocurve_api_helper.base import Item
from combocurve_api_helper.shapefiles import GET_LIMIT, Shapefiles
from tests.http_fakes import (
    FakeResponse,
    RecordingTransport,
    StubAuth,
    install_fake_clock,
    install_recording_transport,
    make_offline_api,
)

BASE = Shapefiles.API_BASE_URL
PROJECT = 'p1'
COMPANY_ROOT = f'{BASE}/shapefiles'
PROJECT_ROOT = f'{BASE}/projects/{PROJECT}/shapefiles'
SIGNED_URL = 'https://storage.example.test/bucket/upload.zip?X-Goog-Signature=abc'
SECRET_HEADERS = {'Authorization': 'Bearer secret-token', 'x-api-key': 'secret-key'}


def _install(monkeypatch: pytest.MonkeyPatch, *responses: FakeResponse) -> RecordingTransport:
    transport = install_recording_transport(monkeypatch, *responses)
    monkeypatch.setattr(time, 'sleep', lambda seconds: None)
    return transport


def _api() -> Shapefiles:
    return Shapefiles(auth=StubAuth(SECRET_HEADERS))


def _shapefile_zip(*names: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for name in names:
            archive.writestr(name, b'x')
    return buffer.getvalue()


GOOD_ZIP = _shapefile_zip('layer.shp', 'layer.shx', 'layer.dbf', 'layer.prj')
TICKET: Item = {
    'uploadId': 'u1',
    'uploadUrl': SIGNED_URL,
    'method': 'PUT',
    'headers': {'Content-Type': 'application/zip'},
    'maxBytes': 272629760,
}


def test_urls_for_both_scopes() -> None:
    api = Shapefiles.__new__(Shapefiles)
    assert api.get_company_shapefiles_url() == COMPANY_ROOT
    assert api.get_company_shapefiles_url({'scope': 'company'}) == f'{COMPANY_ROOT}?scope=company'
    assert api.get_project_shapefiles_url(PROJECT, {'name': 'A B'}) == f'{PROJECT_ROOT}?name=A%20B'
    assert api.get_company_shapefiles_head_url({'name': 'A'}) == f'{COMPANY_ROOT}/head?name=A'
    assert api.get_project_shapefiles_head_url(PROJECT) == f'{PROJECT_ROOT}/head'
    assert api.get_company_shapefile_by_id_url('s1') == f'{COMPANY_ROOT}/s1'
    assert api.get_project_shapefile_by_id_url(PROJECT, 's1') == f'{PROJECT_ROOT}/s1'
    assert api.get_company_shapefile_features_url('s1', {'skip': '5'}) == f'{COMPANY_ROOT}/s1/features?skip=5'
    assert api.get_project_shapefile_features_url(PROJECT, 's1') == f'{PROJECT_ROOT}/s1/features'
    assert api.get_company_shapefile_job_url('j1') == f'{COMPANY_ROOT}/jobs/j1'
    assert api.get_project_shapefile_job_url(PROJECT, 'j1') == f'{PROJECT_ROOT}/jobs/j1'
    assert api.get_company_shapefile_upload_url() == f'{COMPANY_ROOT}/uploads'
    assert api.get_project_shapefile_upload_url(PROJECT) == f'{PROJECT_ROOT}/uploads'
    assert api.get_company_shapefile_upload_import_url('u1') == f'{COMPANY_ROOT}/uploads/u1'
    assert api.get_project_shapefile_upload_import_url(PROJECT, 'u1') == f'{PROJECT_ROOT}/uploads/u1'


@pytest.mark.parametrize(
    ('call', 'verb', 'url', 'body'),
    [
        (lambda api: api.get_company_shapefile_by_id('s1'), 'GET', f'{COMPANY_ROOT}/s1', None),
        (lambda api: api.get_project_shapefile_by_id(PROJECT, 's1'), 'GET', f'{PROJECT_ROOT}/s1', None),
        (lambda api: api.get_company_shapefile_job('j1'), 'GET', f'{COMPANY_ROOT}/jobs/j1', None),
        (lambda api: api.get_project_shapefile_job(PROJECT, 'j1'), 'GET', f'{PROJECT_ROOT}/jobs/j1', None),
        (lambda api: api.delete_company_shapefile_by_id('s1'), 'DELETE', f'{COMPANY_ROOT}/s1', None),
        (lambda api: api.delete_project_shapefile_by_id(PROJECT, 's1'), 'DELETE', f'{PROJECT_ROOT}/s1', None),
        (
            lambda api: api.post_company_shapefiles({'name': 'n', 'scope': 'company'}),
            'POST',
            COMPANY_ROOT,
            {'name': 'n', 'scope': 'company'},
        ),
        (lambda api: api.post_project_shapefiles(PROJECT, {'name': 'n'}), 'POST', PROJECT_ROOT, {'name': 'n'}),
        (
            lambda api: api.post_company_shapefile_upload(),
            'POST',
            f'{COMPANY_ROOT}/uploads',
            {'contentType': 'application/zip'},
        ),
        (
            lambda api: api.post_project_shapefile_upload(PROJECT, 'application/x-zip-compressed'),
            'POST',
            f'{PROJECT_ROOT}/uploads',
            {'contentType': 'application/x-zip-compressed'},
        ),
        (
            lambda api: api.post_company_shapefile_upload_import('u1', {'name': 'n', 'scope': 'company'}),
            'POST',
            f'{COMPANY_ROOT}/uploads/u1',
            {'name': 'n', 'scope': 'company'},
        ),
        (
            lambda api: api.post_project_shapefile_upload_import(PROJECT, 'u1', {'name': 'n'}),
            'POST',
            f'{PROJECT_ROOT}/uploads/u1',
            {'name': 'n'},
        ),
    ],
)
def test_single_object_routes(monkeypatch: pytest.MonkeyPatch, call: Any, verb: str, url: str, body: Any) -> None:
    transport = _install(monkeypatch, FakeResponse(200, {'jobId': 'j1'}))
    result = call(_api())
    assert result == {'jobId': 'j1'}
    [sent] = transport.calls
    assert (sent.method, sent.url, sent.body) == (verb, url, body)
    assert sent.headers == SECRET_HEADERS


def test_lists_follow_pages_at_the_maximum_take_and_order_by_name_then_id(monkeypatch: pytest.MonkeyPatch) -> None:
    first_page = [{'id': 'b2', 'name': 'B'}, {'id': 'a9', 'name': 'A'}]
    transport = _install(
        monkeypatch,
        FakeResponse(200, first_page, headers={'Link': f'<{COMPANY_ROOT}?take=200&skip=2>;rel="next"'}),
        FakeResponse(200, [{'id': 'a1', 'name': 'A'}]),
        FakeResponse(200, []),
    )
    api = _api()
    layers = api.get_company_shapefiles({'scope': 'project'})
    assert [layer['id'] for layer in layers] == ['a1', 'a9', 'b2']
    assert all(set(layer) == {'id', 'name'} for layer in layers), 'no ordering key may be padded in'
    assert transport.calls[0].url == f'{COMPANY_ROOT}?scope=project'
    assert transport.calls[0].params == {'take': GET_LIMIT}
    assert transport.calls[1].url == f'{COMPANY_ROOT}?take=200&skip=2'

    assert api.get_project_shapefiles(PROJECT) == []
    assert (transport.calls[2].url, transport.calls[2].params) == (PROJECT_ROOT, {'take': GET_LIMIT})


def test_features_keep_their_stored_order(monkeypatch: pytest.MonkeyPatch) -> None:
    features = [{'type': 'Feature', 'properties': {'n': 2}}, {'type': 'Feature', 'properties': {'n': 1}}]
    transport = _install(monkeypatch, FakeResponse(200, features), FakeResponse(200, features))
    api = _api()
    assert api.get_company_shapefile_features('s1') == features
    assert api.get_project_shapefile_features(PROJECT, 's1', {'skip': '10'}) == features
    assert [(call.url, call.params) for call in transport.calls] == [
        (f'{COMPANY_ROOT}/s1/features', {'take': GET_LIMIT}),
        (f'{PROJECT_ROOT}/s1/features?skip=10', {'take': GET_LIMIT}),
    ]


def test_counts_read_the_header_of_a_head_or_of_the_head_sub_route(monkeypatch: pytest.MonkeyPatch) -> None:
    count = {'X-Query-Count': '7'}
    transport = _install(monkeypatch, *(FakeResponse(200, None, headers=count) for _ in range(4)))
    api = _api()
    assert api.count_company_shapefiles({'name': 'n'}) == 7
    assert api.count_company_shapefiles_with_get({'name': 'n'}) == 7
    assert api.count_project_shapefiles(PROJECT) == 7
    assert api.count_project_shapefiles_with_get(PROJECT) == 7
    assert [(call.method, call.url) for call in transport.calls] == [
        ('HEAD', f'{COMPANY_ROOT}?name=n'),
        ('GET', f'{COMPANY_ROOT}/head?name=n'),
        ('HEAD', PROJECT_ROOT),
        ('GET', f'{PROJECT_ROOT}/head'),
    ]


def test_a_count_without_the_header_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, FakeResponse(200, None))
    with pytest.raises(ValueError, match='X-Query-Count'):
        _api().count_company_shapefiles_with_get()


def test_patch_sends_one_request_of_records(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _install(monkeypatch, FakeResponse(207, {'results': [], 'successCount': 1, 'failedCount': 0}))
    _api().patch_company_shapefiles({'id': 's1', 'description': 'd'})
    [sent] = transport.calls
    assert (sent.method, sent.url, sent.body) == ('PATCH', COMPANY_ROOT, [{'id': 's1', 'description': 'd'}])


@pytest.mark.parametrize(
    ('data', 'message'),
    [
        ([], 'at least one'),
        ([{'description': 'no id'}], 'carry an `id`'),
        ([{'id': 's1', 'color': '#000000'}, {'id': 's2'}, {'id': 's1', 'name': 'x'}], r"repeated ids: \['s1'\]"),
    ],
)
def test_patch_refuses_before_sending(monkeypatch: pytest.MonkeyPatch, data: Any, message: str) -> None:
    transport = _install(monkeypatch)
    with pytest.raises(ValueError, match=message):
        _api().patch_company_shapefiles(data)
    assert transport.calls == []


@pytest.mark.parametrize('key', ['scope', 'projectIds'])
def test_project_routes_refuse_the_scope_keys_before_sending(monkeypatch: pytest.MonkeyPatch, key: str) -> None:
    transport = _install(monkeypatch)
    api = _api()
    data: Item = {'name': 'n', key: 'project'}
    with pytest.raises(ValueError, match='project route'):
        api.post_project_shapefiles(PROJECT, data)
    with pytest.raises(ValueError, match='project route'):
        api.post_project_shapefile_upload_import(PROJECT, 'u1', data)
    with pytest.raises(ValueError, match='project route'):
        api.upload_project_shapefile(PROJECT, GOOD_ZIP, data)
    assert transport.calls == []


def test_upload_refuses_an_unknown_content_type_and_an_empty_upload_id(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _install(monkeypatch)
    api = _api()
    with pytest.raises(ValueError, match='content_type'):
        api.post_company_shapefile_upload('text/plain')
    with pytest.raises(ValueError, match='upload_id'):
        api.post_company_shapefile_upload_import('', {'name': 'n'})
    assert transport.calls == []


def test_the_signed_upload_sends_only_the_ticket_headers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    transport = _install(monkeypatch, FakeResponse(200, None), FakeResponse(200, None))
    auth = StubAuth(SECRET_HEADERS)
    api = Shapefiles(auth=auth)
    zip_path = tmp_path / 'layer.zip'
    zip_path.write_bytes(GOOD_ZIP)

    api.put_shapefile_upload_file(TICKET, GOOD_ZIP)
    api.put_shapefile_upload_file(TICKET, zip_path)

    assert auth.fetches == 0, 'no credential may be fetched for the signed url'
    for sent in transport.calls:
        assert (sent.method, sent.url, sent.data) == ('PUT', SIGNED_URL, GOOD_ZIP)
        assert sent.headers == {'Content-Type': 'application/zip'}
        assert sent.body is None
        assert sent.timeout is not None


@pytest.mark.parametrize(
    ('ticket', 'content', 'message'),
    [
        ({**TICKET, 'uploadUrl': 'http://storage.example.test/upload.zip'}, GOOD_ZIP, 'https'),
        ({**TICKET, 'uploadUrl': None}, GOOD_ZIP, 'https'),
        ({**TICKET, 'maxBytes': 10}, GOOD_ZIP, 'at most 10'),
        (TICKET, b'not a zip', 'not a zip'),
        (TICKET, _shapefile_zip('layer.shx', 'layer.dbf'), 'exactly one .shp'),
        (TICKET, _shapefile_zip('a.shp', 'a.shx', 'a.dbf', 'b.shp', 'b.shx', 'b.dbf'), 'exactly one .shp'),
        (TICKET, _shapefile_zip('layer.shp', 'layer.shx', 'other.dbf'), r"missing \['.dbf'\]"),
    ],
)
def test_the_signed_upload_refuses_before_sending(
    monkeypatch: pytest.MonkeyPatch, ticket: Item, content: bytes, message: str
) -> None:
    transport = _install(monkeypatch)
    with pytest.raises(ValueError, match=message):
        _api().put_shapefile_upload_file(ticket, content)
    assert transport.calls == []


def test_macos_metadata_members_are_not_counted() -> None:
    content = _shapefile_zip(
        'layer.shp', 'layer.shx', 'layer.dbf', '__MACOSX/', '__MACOSX/._layer.shp', '__MACOSX/._layer.dbf', '._b.shp'
    )
    assert shapefiles_module._read_upload_zip(content) == content


def test_macos_metadata_does_not_stand_in_for_a_missing_sidecar() -> None:
    content = _shapefile_zip('layer.shp', 'layer.shx', '__MACOSX/._layer.dbf')
    with pytest.raises(ValueError, match=r"missing \['.dbf'\]"):
        shapefiles_module._read_upload_zip(content)


def test_a_zip_in_a_folder_with_upper_case_suffixes_is_accepted() -> None:
    content = _shapefile_zip('folder/', 'folder/Layer.SHP', 'folder/Layer.SHX', 'folder/Layer.DBF')
    assert shapefiles_module._read_upload_zip(content) == content


def test_wait_polls_until_the_job_leaves_pending_and_running(monkeypatch: pytest.MonkeyPatch) -> None:
    done = {'jobId': 'j1', 'status': 'successful', 'result': {'shapefileId': 's1'}}
    transport = _install(
        monkeypatch,
        FakeResponse(200, {'jobId': 'j1', 'status': 'pending'}),
        FakeResponse(200, {'jobId': 'j1', 'status': 'running'}),
        FakeResponse(200, done),
    )
    assert _api().wait_for_project_shapefile_job(PROJECT, 'j1') == done
    assert [call.url for call in transport.calls] == [f'{PROJECT_ROOT}/jobs/j1'] * 3


def test_wait_returns_a_failed_job_without_raising(monkeypatch: pytest.MonkeyPatch) -> None:
    failed = {'jobId': 'j1', 'type': 'upload', 'status': 'failed', 'error': 'Error uploading to Mapbox: x'}
    _install(monkeypatch, FakeResponse(200, {'jobId': 'j1', 'status': 'running'}), FakeResponse(200, failed))
    assert _api().wait_for_company_shapefile_job('j1') == failed


def test_wait_raises_when_the_next_poll_would_pass_the_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    running = {'jobId': 'j1', 'status': 'running'}
    transport = _install(monkeypatch, *(FakeResponse(200, running) for _ in range(4)))
    clock = install_fake_clock(monkeypatch)
    # Polls at 0, 1 and 2; a poll at 3 would pass 2.5, so it raises after the third poll.
    with pytest.raises(TimeoutError, match='still'):
        _api().wait_for_company_shapefile_job('j1', timeout_seconds=2.5, poll_seconds=1.0)
    assert len(transport.calls) == 3
    assert clock.sleeps == [1.0, 1.0]


def test_wait_still_polls_at_exactly_the_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    running = {'jobId': 'j1', 'status': 'running'}
    done = {'jobId': 'j1', 'status': 'successful', 'result': {'shapefileId': 's1'}}
    transport = _install(monkeypatch, *(FakeResponse(200, running) for _ in range(3)), FakeResponse(200, done))
    clock = install_fake_clock(monkeypatch)
    # Timeout 3.0: the poll at 3 is not after the deadline, so it is made and sees the finished job.
    assert _api().wait_for_company_shapefile_job('j1', timeout_seconds=3.0, poll_seconds=1.0) == done
    assert len(transport.calls) == 4
    assert clock.sleeps == [1.0, 1.0, 1.0]


def _upload_responses(final_job: Item) -> list[FakeResponse]:
    return [
        FakeResponse(201, TICKET),
        FakeResponse(200, None),
        FakeResponse(202, {'jobId': 'j1'}),
        FakeResponse(200, {'jobId': 'j1', 'status': 'running'}),
        FakeResponse(200, final_job),
    ]


def test_upload_runs_the_three_steps_and_returns_the_new_layer(monkeypatch: pytest.MonkeyPatch) -> None:
    layer: Item = {'id': 's1', 'name': 'n'}
    done: Item = {'jobId': 'j1', 'status': 'successful', 'result': {'shapefileId': 's1'}}
    transport = _install(monkeypatch, *_upload_responses(done), FakeResponse(200, layer))

    assert _api().upload_project_shapefile(PROJECT, GOOD_ZIP, {'name': 'n'}) == layer

    assert [(call.method, call.url) for call in transport.calls] == [
        ('POST', f'{PROJECT_ROOT}/uploads'),
        ('PUT', SIGNED_URL),
        ('POST', f'{PROJECT_ROOT}/uploads/u1'),
        ('GET', f'{PROJECT_ROOT}/jobs/j1'),
        ('GET', f'{PROJECT_ROOT}/jobs/j1'),
        ('GET', f'{PROJECT_ROOT}/s1'),
    ]
    signed_put = transport.calls[1]
    assert 'Authorization' not in signed_put.headers
    assert 'x-api-key' not in signed_put.headers
    assert transport.calls[2].body == {'name': 'n'}


def test_upload_raises_when_the_job_does_not_succeed(monkeypatch: pytest.MonkeyPatch) -> None:
    # The shape of a failed job seen live 2026-11-22: no `result`, an `error` message string.
    failed: Item = {
        'jobId': 'j1',
        'type': 'upload',
        'status': 'failed',
        'createdAt': '2026-11-22T00:00:00.000Z',
        'completedAt': '2026-11-22T00:00:10.000Z',
        'error': 'Error uploading to Mapbox: Unknown filetype',
    }
    transport = _install(monkeypatch, *_upload_responses(failed))
    with pytest.raises(RuntimeError, match=r'did not succeed.*Unknown filetype'):
        _api().upload_company_shapefile(GOOD_ZIP, {'name': 'n', 'scope': 'company'})
    assert transport.calls[0].url == f'{COMPANY_ROOT}/uploads'


def test_upload_refuses_a_bad_zip_before_reserving_an_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _install(monkeypatch)
    with pytest.raises(ValueError, match='not a zip'):
        _api().upload_company_shapefile(b'not a zip', {'name': 'n'})
    assert transport.calls == []


@pytest.mark.parametrize(
    'send',
    [
        lambda api: api.post_company_shapefiles({'name': 'x', 'type': 'FeatureCollection', 'features': []}),
        lambda api: api.post_company_shapefile_upload_import('upload-1', {'name': 'x'}),
        lambda api: api.post_company_shapefile_upload_import('upload-1', {'name': 'x', 'scope': 'everyone'}),
        lambda api: api.upload_company_shapefile(GOOD_ZIP, {'name': 'x'}),
        lambda api: api.upload_company_shapefile(GOOD_ZIP, {'name': 'x', 'scope': 'everyone'}),
    ],
)
def test_company_create_without_scope_is_refused_before_sending(monkeypatch: pytest.MonkeyPatch, send: Any) -> None:
    """The company route answers 400 `RequiredFieldError` without `scope` (live 2026-11-22): refuse it locally."""
    transport = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError, match=r"requires data\['scope'\]"):
        send(make_offline_api())
    assert transport.calls == []
