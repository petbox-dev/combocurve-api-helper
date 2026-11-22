"""Offline checks for production comments (company and project scope) and production comment types: the url
and verb each method sends, the body, the list order, and the requests refused before anything is sent."""

from typing import Any, Callable

import pytest
import requests

from combocurve_api_helper.production_comments import GET_LIMIT, WRITE_LIMIT, ProductionComments
from tests.http_fakes import FakeResponse, StubAuth, install_recording_transport

BASE = ProductionComments.API_BASE_URL
PROJECT_ID = 'p1'
COMPANY = f'{BASE}/production-comments'
PROJECT = f'{BASE}/projects/{PROJECT_ID}/production-comments'
WRITE_ENVELOPE: Any = {'results': [], 'generalErrors': [], 'successCount': 1, 'failedCount': 0}


def _api() -> ProductionComments:
    return ProductionComments(auth=StubAuth())


def test_urls_for_both_scopes_and_the_types() -> None:
    api = _api()
    assert api.get_company_production_comments_url() == COMPANY
    assert api.get_company_production_comments_url({'well': 'w1'}) == f'{COMPANY}?well=w1'
    assert api.get_company_production_comment_by_id_url('c1') == f'{COMPANY}/c1'
    assert api.get_project_production_comments_url(PROJECT_ID) == PROJECT
    assert api.get_project_production_comments_url(PROJECT_ID, {'commentType': 'prod_comment_type_0'}) == (
        f'{PROJECT}?commentType=prod_comment_type_0'
    )
    assert api.get_project_production_comment_by_id_url(PROJECT_ID, 'c1') == f'{PROJECT}/c1'
    assert api.get_production_comment_types_url() == f'{BASE}/production-comment-types'


def test_each_company_method_sends_its_verb_url_and_body(monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api()
    record: Any = {'well': 'w1', 'commentType': 'prod_comment_type_0', 'note': 'n'}
    transport = install_recording_transport(
        monkeypatch,
        FakeResponse(200, [{'id': 'c1'}]),
        FakeResponse(200, headers={'X-Query-Count': '4'}),
        FakeResponse(200, {'id': 'c1'}),
        FakeResponse(207, WRITE_ENVELOPE),
        FakeResponse(207, WRITE_ENVELOPE),
        FakeResponse(207, WRITE_ENVELOPE),
        FakeResponse(204),
        FakeResponse(204),
    )

    api.get_company_production_comments({'well': 'w1'})
    assert api.count_company_production_comments({'well': 'w1'}) == 4
    assert api.get_company_production_comment_by_id('c1') == {'id': 'c1'}
    assert api.post_company_production_comments([record]) == [WRITE_ENVELOPE]
    api.put_company_production_comments([record])
    api.patch_company_production_comments([{'id': 'c1', 'note': 'm'}])
    api.delete_company_production_comments(production_comment_id='c1')
    api.delete_company_production_comment_by_id('c1')

    assert [(call.method, call.url) for call in transport.calls] == [
        ('GET', f'{COMPANY}?well=w1'),
        ('HEAD', f'{COMPANY}?well=w1'),
        ('GET', f'{COMPANY}/c1'),
        ('POST', COMPANY),
        ('PUT', COMPANY),
        ('PATCH', COMPANY),
        ('DELETE', f'{COMPANY}?id=c1'),
        ('DELETE', f'{COMPANY}/c1'),
    ]
    assert transport.calls[0].params == {'take': GET_LIMIT}
    assert [call.body for call in transport.calls[3:6]] == [[record], [record], [{'id': 'c1', 'note': 'm'}]]
    assert transport.calls[6].body is None
    assert transport.calls[7].body is None


def test_each_project_method_sends_its_verb_url_and_body(monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api()
    record: Any = {'chosenID': 'x', 'dataSource': 'other', 'commentType': 'prod_comment_type_1'}
    transport = install_recording_transport(
        monkeypatch,
        FakeResponse(200, []),
        FakeResponse(200, headers={'X-Query-Count': '0'}),
        FakeResponse(200, {'id': 'c2'}),
        FakeResponse(207, WRITE_ENVELOPE),
        FakeResponse(207, WRITE_ENVELOPE),
        FakeResponse(207, WRITE_ENVELOPE),
        FakeResponse(204),
        FakeResponse(204),
    )

    api.get_project_production_comments(PROJECT_ID)
    assert api.count_project_production_comments(PROJECT_ID) == 0
    api.get_project_production_comment_by_id(PROJECT_ID, 'c2')
    api.post_project_production_comments(PROJECT_ID, record)
    api.put_project_production_comments(PROJECT_ID, [record])
    api.patch_project_production_comments(PROJECT_ID, [{'id': 'c2', 'note': 'm'}])
    api.delete_project_production_comments(
        PROJECT_ID, well_id='w1', start_date='2024-01-01T00:00:00Z', end_date='2024-02-01T00:00:00Z'
    )
    api.delete_project_production_comment_by_id(PROJECT_ID, 'c2')

    assert [(call.method, call.url) for call in transport.calls] == [
        ('GET', PROJECT),
        ('HEAD', PROJECT),
        ('GET', f'{PROJECT}/c2'),
        ('POST', PROJECT),
        ('PUT', PROJECT),
        ('PATCH', PROJECT),
        ('DELETE', f'{PROJECT}?well=w1&startDate=2024-01-01T00%3A00%3A00Z&endDate=2024-02-01T00%3A00%3A00Z'),
        ('DELETE', f'{PROJECT}/c2'),
    ]
    assert transport.calls[3].body == [record], 'a single comment is sent as a one-record list'


def test_list_is_ordered_by_well_then_start_date(monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api()
    comments: Any = [
        {'id': 'c3', 'startDate': '2024-03-01', 'well': 'w2'},
        {'id': 'c2', 'startDate': '2024-02-01', 'well': 'w1'},
        {'id': 'c1', 'startDate': '2024-01-01', 'well': 'w1'},
    ]
    install_recording_transport(monkeypatch, FakeResponse(200, comments))

    assert [comment['id'] for comment in api.get_company_production_comments()] == ['c1', 'c2', 'c3']


DeleteCall = Callable[..., Any]
DELETES: list[DeleteCall] = [
    lambda api, **filters: api.delete_company_production_comments(**filters),
    lambda api, **filters: api.delete_project_production_comments(PROJECT_ID, **filters),
]


@pytest.mark.parametrize('delete', DELETES)
@pytest.mark.parametrize(
    'filters',
    [
        {},
        {'production_comment_id': '', 'well_id': ''},
        {'start_date': '2024-01-01', 'end_date': '2024-02-01'},
        {'production_comment_id': 'c1', 'start_date': '2024-01-01'},
    ],
)
def test_delete_without_an_id_or_a_well_is_refused_before_sending(
    monkeypatch: pytest.MonkeyPatch, delete: DeleteCall, filters: dict[str, str]
) -> None:
    transport = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError):
        delete(_api(), **filters)
    assert transport.calls == []


@pytest.mark.parametrize('delete', DELETES)
@pytest.mark.parametrize(
    'filters',
    [
        {'well_id': 'w1'},
        {'well_id': 'w1', 'start_date': '2024-01-01T00:00:00.000Z'},
        {'well_id': 'w1', 'end_date': '2024-02-01T00:00:00.000Z'},
    ],
)
def test_delete_by_well_without_both_dates_is_refused_before_sending(
    monkeypatch: pytest.MonkeyPatch, delete: DeleteCall, filters: dict[str, str]
) -> None:
    # The server answers 400 `RequiredFilterError` ("When deleting by well, required filters are: `well` +
    # `startDate` + `endDate`"; dev, 2026-11-22).
    transport = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError, match='start_date and end_date'):
        delete(_api(), **filters)
    assert transport.calls == []


@pytest.mark.parametrize(
    'write',
    [
        lambda api, records: api.post_company_production_comments(records),
        lambda api, records: api.put_company_production_comments(records),
        lambda api, records: api.patch_company_production_comments(records),
        lambda api, records: api.post_project_production_comments(PROJECT_ID, records),
        lambda api, records: api.put_project_production_comments(PROJECT_ID, records),
        lambda api, records: api.patch_project_production_comments(PROJECT_ID, records),
    ],
)
def test_writes_are_sent_in_batches_of_the_write_limit(monkeypatch: pytest.MonkeyPatch, write: Any) -> None:
    # 201 records answer 400 `RecordCountError` on POST, PUT and PATCH (dev, 2026-11-22).
    records: Any = [{'id': f'c{i}', 'note': 'n'} for i in range(WRITE_LIMIT + 1)]
    transport = install_recording_transport(
        monkeypatch, FakeResponse(207, WRITE_ENVELOPE), FakeResponse(207, WRITE_ENVELOPE)
    )
    assert write(_api(), records) == [WRITE_ENVELOPE, WRITE_ENVELOPE], 'one 207 envelope per batch'
    assert [len(call.body) for call in transport.calls] == [WRITE_LIMIT, 1]


@pytest.mark.parametrize('delete', DELETES)
def test_delete_refuses_an_id_and_a_well_together(monkeypatch: pytest.MonkeyPatch, delete: DeleteCall) -> None:
    transport = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError, match='not both'):
        delete(_api(), production_comment_id='c1', well_id='w1')
    assert transport.calls == []


def test_delete_filters_are_keyword_only() -> None:
    api: Any = _api()
    with pytest.raises(TypeError):
        api.delete_company_production_comments('c1')
    with pytest.raises(TypeError):
        api.delete_project_production_comments(PROJECT_ID, 'c1')


@pytest.mark.parametrize(
    'write',
    [
        lambda api: api.post_company_production_comments([]),
        lambda api: api.put_company_production_comments([]),
        lambda api: api.patch_company_production_comments([]),
        lambda api: api.post_project_production_comments(PROJECT_ID, []),
        lambda api: api.put_project_production_comments(PROJECT_ID, []),
        lambda api: api.patch_project_production_comments(PROJECT_ID, []),
        lambda api: api.patch_production_comment_types([]),
    ],
)
def test_empty_write_is_refused_before_sending(monkeypatch: pytest.MonkeyPatch, write: Any) -> None:
    transport = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError, match='at least one'):
        write(_api())
    assert transport.calls == []


def test_comment_types_read_returns_the_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    envelope: Any = {'productionCommentTypes': [{'key': 'prod_comment_type_0', 'label': 'A', 'color': '#000000'}]}
    transport = install_recording_transport(monkeypatch, FakeResponse(200, envelope))

    assert _api().get_production_comment_types() == envelope
    assert [(call.method, call.url) for call in transport.calls] == [('GET', f'{BASE}/production-comment-types')]


def test_comment_types_patch_wraps_the_entries_and_returns_the_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries: Any = [{'key': 'prod_comment_type_3', 'label': 'Shut in', 'color': '#123456'}]
    configuration: Any = {'productionCommentTypes': entries}
    transport = install_recording_transport(monkeypatch, FakeResponse(200, configuration))

    assert _api().patch_production_comment_types(entries) == configuration
    assert transport.calls[0].method == 'PATCH'
    assert transport.calls[0].url == f'{BASE}/production-comment-types'
    assert transport.calls[0].body == {'productionCommentTypes': entries}


def test_comment_types_patch_raises_on_a_refused_request(monkeypatch: pytest.MonkeyPatch) -> None:
    refusal = {'name': 'TypeError', 'message': '`undefined` is not a string', 'details': {'location': '[0].color'}}
    install_recording_transport(monkeypatch, FakeResponse(400, refusal))

    with pytest.raises(requests.HTTPError):
        _api().patch_production_comment_types([{'key': 'prod_comment_type_3', 'label': 'Shut in'}])
