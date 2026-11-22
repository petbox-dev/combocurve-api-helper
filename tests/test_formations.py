"""Formations (company and project scope): verb, url, query, body and result of each method. No live API.

The route paths and docs slugs are also checked against the Postman collection by `test_route_paths.py`
and `test_docstring_slugs.py` once `Formations` is in `ComboCurveAPI`.
"""

import time
from typing import Any, Optional

import pytest
from pytest import MonkeyPatch

from combocurve_api_helper.base import Item, ItemList
from combocurve_api_helper.formations import GET_LIMIT, POINTS_GET_LIMIT, Formations
from tests.http_fakes import FakeResponse, StubAuth, install_recording_transport

V1 = 'https://api.combocurve.com/v1'
PROJECT_ID = '000000000000000000000001'
FORMATION_ID = '000000000000000000000002'
JOB_ID = '000000000000000000000003'
COMPANY_URL = f'{V1}/formations'
PROJECT_URL = f'{V1}/projects/{PROJECT_ID}/formations'

SUMMARIES: ItemList = [
    {'id': 'b', 'name': 'Sample Formation B', 'createdAt': '2020', 'updatedAt': '2020'},
    {'id': 'a', 'name': 'Sample Formation A', 'createdAt': '2020', 'updatedAt': '2020'},
]
POINTS: ItemList = [
    {'latitude': 31.0, 'longitude': -102.0, 'topTvd': 8000.0, 'baseTvd': 8100.0, 'baseIsPlaceholder': False},
    {'latitude': 30.0, 'longitude': -101.0, 'topTvd': 7000.0, 'baseTvd': 7100.0, 'baseIsPlaceholder': False},
]
NEW_FORMATION: Item = {
    'name': 'Sample Formation A',
    'points': [{'latitude': 31.0, 'longitude': -102.0, 'topTvd': 8000.0}],
}
WRITE_RESPONSE = {'generalErrors': [], 'results': [], 'failedCount': 0, 'successCount': 1}


def _api() -> Formations:
    return Formations(auth=StubAuth())


def _scope_url(scope: str) -> str:
    return COMPANY_URL if scope == 'company' else PROJECT_URL


# URLs


def test_urls_of_both_scopes() -> None:
    api = _api()
    assert api.get_company_formations_url() == COMPANY_URL
    assert api.get_company_formations_url({'scope': 'company'}) == f'{COMPANY_URL}?scope=company'
    assert api.get_company_formations_head_url({'name': 'A B'}) == f'{COMPANY_URL}/head?name=A%20B'
    assert api.get_company_formations_job_url(JOB_ID) == f'{COMPANY_URL}/jobs/{JOB_ID}'
    assert api.get_company_formation_by_id_url(FORMATION_ID) == f'{COMPANY_URL}/{FORMATION_ID}'
    assert api.get_company_formation_points_url(FORMATION_ID) == f'{COMPANY_URL}/{FORMATION_ID}/points'

    assert api.get_project_formations_url(PROJECT_ID) == PROJECT_URL
    assert api.get_project_formations_url(PROJECT_ID, {'name': 'A'}) == f'{PROJECT_URL}?name=A'
    assert api.get_project_formations_head_url(PROJECT_ID) == f'{PROJECT_URL}/head'
    assert api.get_project_formations_job_url(PROJECT_ID, JOB_ID) == f'{PROJECT_URL}/jobs/{JOB_ID}'
    assert api.get_project_formation_by_id_url(PROJECT_ID, FORMATION_ID) == f'{PROJECT_URL}/{FORMATION_ID}'
    assert api.get_project_formation_points_url(PROJECT_ID, FORMATION_ID, {'skip': '5'}) == (
        f'{PROJECT_URL}/{FORMATION_ID}/points?skip=5'
    )


# Reads


@pytest.mark.parametrize('scope', ['company', 'project'])
def test_list_takes_200_carries_the_filters_and_sorts_by_name(monkeypatch: MonkeyPatch, scope: str) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, [dict(item) for item in SUMMARIES]))
    api = _api()
    if scope == 'company':
        listed = api.get_company_formations({'name': 'Sample Formation A'})
    else:
        listed = api.get_project_formations(PROJECT_ID, {'name': 'Sample Formation A'})

    [call] = recorder.calls
    assert (call.method, call.url, call.params) == (
        'GET',
        f'{_scope_url(scope)}?name=Sample%20Formation%20A',
        {'take': GET_LIMIT},
    )
    assert [item['id'] for item in listed] == ['a', 'b']


def test_list_follows_the_next_page_link(monkeypatch: MonkeyPatch) -> None:
    next_page = f'{COMPANY_URL}?skip=200&take=200'
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, [dict(SUMMARIES[0])], headers={'Link': f'<{next_page}>;rel="next"'}),
        FakeResponse(200, [dict(SUMMARIES[1])]),
    )
    listed = _api().get_company_formations()
    assert [call.url for call in recorder.calls] == [COMPANY_URL, next_page]
    assert len(listed) == 2


@pytest.mark.parametrize('scope', ['company', 'project'])
def test_count_sends_head(monkeypatch: MonkeyPatch, scope: str) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, None, headers={'X-Query-Count': '4'}))
    api = _api()
    count = api.count_company_formations() if scope == 'company' else api.count_project_formations(PROJECT_ID)
    [call] = recorder.calls
    assert (call.method, call.url) == ('HEAD', _scope_url(scope))
    assert count == 4


@pytest.mark.parametrize('scope', ['company', 'project'])
def test_count_with_get_sends_get_to_the_head_route(monkeypatch: MonkeyPatch, scope: str) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, None, headers={'X-Query-Count': '7'}))
    api = _api()
    if scope == 'company':
        count = api.count_company_formations_with_get({'scope': 'company'})
        expected_url = f'{COMPANY_URL}/head?scope=company'
    else:
        count = api.count_project_formations_with_get(PROJECT_ID, {'name': 'A'})
        expected_url = f'{PROJECT_URL}/head?name=A'
    [call] = recorder.calls
    assert (call.method, call.url) == ('GET', expected_url)
    assert count == 7


def test_count_with_get_raises_without_the_header(monkeypatch: MonkeyPatch) -> None:
    install_recording_transport(monkeypatch, FakeResponse(200, None))
    with pytest.raises(ValueError, match='X-Query-Count'):
        _api().count_company_formations_with_get()


@pytest.mark.parametrize('scope', ['company', 'project'])
def test_by_id_and_job_return_the_one_object(monkeypatch: MonkeyPatch, scope: str) -> None:
    summary = {'id': FORMATION_ID, 'name': 'Sample Formation A'}
    job = {'jobId': JOB_ID, 'status': 'successful'}
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, summary), FakeResponse(200, job))
    api = _api()
    if scope == 'company':
        got = api.get_company_formation_by_id(FORMATION_ID)
        got_job = api.get_company_formations_job(JOB_ID)
    else:
        got = api.get_project_formation_by_id(PROJECT_ID, FORMATION_ID)
        got_job = api.get_project_formations_job(PROJECT_ID, JOB_ID)
    assert [(call.method, call.url) for call in recorder.calls] == [
        ('GET', f'{_scope_url(scope)}/{FORMATION_ID}'),
        ('GET', f'{_scope_url(scope)}/jobs/{JOB_ID}'),
    ]
    assert got == summary
    assert got_job == job


@pytest.mark.parametrize('scope', ['company', 'project'])
def test_points_follow_every_page_in_stored_order(monkeypatch: MonkeyPatch, scope: str) -> None:
    points_url = f'{_scope_url(scope)}/{FORMATION_ID}/points'
    next_page = f'{points_url}?skip={POINTS_GET_LIMIT}&take={POINTS_GET_LIMIT}'
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, [dict(POINTS[0])], headers={'Link': f'<{next_page}>;rel="next"'}),
        FakeResponse(200, [dict(POINTS[1])]),
    )
    api = _api()
    if scope == 'company':
        points = api.get_company_formation_points(FORMATION_ID)
    else:
        points = api.get_project_formation_points(PROJECT_ID, FORMATION_ID)
    assert [(call.url, call.params) for call in recorder.calls] == [
        (points_url, {'take': POINTS_GET_LIMIT}),
        (next_page, None),
    ]
    assert points == POINTS, 'points must stay in stored order (the shape the PUT accepts)'


# Writes


@pytest.mark.parametrize('scope', ['company', 'project'])
def test_put_sends_one_request_and_returns_the_job(monkeypatch: MonkeyPatch, scope: str) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(202, {'jobId': JOB_ID}))
    api = _api()
    data: ItemList = [dict(NEW_FORMATION) for _ in range(3)]
    if scope == 'company':
        job = api.put_company_formations(data, overlap_handling='keep')
    else:
        job = api.put_project_formations(PROJECT_ID, data, overlap_handling='keep')
    [call] = recorder.calls
    assert (call.method, call.url, call.body) == ('PUT', f'{_scope_url(scope)}?overlapHandling=keep', data)
    assert job == {'jobId': JOB_ID}


def test_put_wraps_one_formation_and_sends_no_overlap_handling_by_default(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(202, {'jobId': JOB_ID}))
    _api().put_company_formations(NEW_FORMATION)
    [call] = recorder.calls
    assert (call.url, call.body) == (COMPANY_URL, [NEW_FORMATION])


@pytest.mark.parametrize(
    ('data', 'overlap_handling', 'message'),
    [([], None, 'at least one formation'), ([NEW_FORMATION], 'clip', 'overlap_handling')],
)
def test_put_refuses_before_sending(
    monkeypatch: MonkeyPatch, data: Any, overlap_handling: Optional[str], message: str
) -> None:
    recorder = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError, match=message):
        _api().put_project_formations(PROJECT_ID, data, overlap_handling=overlap_handling)
    assert recorder.calls == []


@pytest.mark.parametrize('scope', ['company', 'project'])
def test_patch_sends_the_records_and_returns_the_207_envelope(monkeypatch: MonkeyPatch, scope: str) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(207, WRITE_RESPONSE))
    api = _api()
    record: Item = {'id': FORMATION_ID, 'enabled': False}
    written = (
        api.patch_company_formations(record)
        if scope == 'company'
        else api.patch_project_formations(PROJECT_ID, [record])
    )
    [call] = recorder.calls
    assert (call.method, call.url, call.body) == ('PATCH', _scope_url(scope), [record])
    assert written == [WRITE_RESPONSE]


def test_patch_refuses_an_empty_list(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError, match='at least one formation'):
        _api().patch_company_formations([])
    assert recorder.calls == []


@pytest.mark.parametrize('scope', ['company', 'project'])
def test_delete_by_id_sends_no_body(monkeypatch: MonkeyPatch, scope: str) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204, None, headers={'X-Delete-Count': '1'}))
    api = _api()
    if scope == 'company':
        headers = api.delete_company_formation_by_id(FORMATION_ID)
    else:
        headers = api.delete_project_formation_by_id(PROJECT_ID, FORMATION_ID)
    [call] = recorder.calls
    assert (call.method, call.url, call.body) == ('DELETE', f'{_scope_url(scope)}/{FORMATION_ID}', None)
    assert headers['X-Delete-Count'] == '1'


@pytest.mark.parametrize('scope', ['company', 'project'])
def test_wait_for_formations_job_polls_the_job_route_until_it_finishes(monkeypatch: MonkeyPatch, scope: str) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, 'sleep', sleeps.append)
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, {'jobId': JOB_ID, 'status': 'pending'}),
        FakeResponse(200, {'jobId': JOB_ID, 'status': 'running'}),
        FakeResponse(200, {'jobId': JOB_ID, 'status': 'successful', 'result': {}}),
    )
    api = _api()
    if scope == 'company':
        job = api.wait_for_company_formations_job(JOB_ID, poll_seconds=1.5)
    else:
        job = api.wait_for_project_formations_job(PROJECT_ID, JOB_ID, poll_seconds=1.5)
    assert job['status'] == 'successful'
    assert [(call.method, call.url) for call in recorder.calls] == [('GET', f'{_scope_url(scope)}/jobs/{JOB_ID}')] * 3
    assert sleeps == [1.5, 1.5]


def test_wait_for_formations_job_raises_at_the_timeout(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(time, 'sleep', lambda seconds: None)
    install_recording_transport(monkeypatch, FakeResponse(200, {'jobId': JOB_ID, 'status': 'running'}))
    with pytest.raises(TimeoutError, match=f'formations job {JOB_ID} is still'):
        _api().wait_for_company_formations_job(JOB_ID, timeout_seconds=0.0, poll_seconds=1.0)
