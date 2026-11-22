"""The request helpers that several endpoint groups share, after they moved to `APIBase` / `_transport`:
the id and record guards, the GET count, the single-object request, the job poll and the sender for a
signed url on another host. Offline, through the recording transport."""

import io
import time
import zipfile
from collections.abc import Callable
from typing import Any

import pytest
import requests
import urllib3.exceptions
from pytest import MonkeyPatch

from combocurve_api_helper import _transport
from combocurve_api_helper.base import WELL_FILTER_LIMIT, APIBase, Item, ItemList
from tests.http_fakes import FakeResponse, StubAuth, install_recording_transport, make_offline_api

V1 = APIBase.API_BASE_URL
SCENARIO = f'{V1}/projects/p/scenarios/sc'
SIGNED_URL = 'https://storage.example.invalid/upload?signature=abc'


# Guards moved from scenarios.py


def test_require_at_most_allows_the_limit_and_refuses_one_more() -> None:
    APIBase._require_at_most(500, 500, 'data', 'records')
    with pytest.raises(ValueError, match=r'^data holds 501 records; the route takes at most 500 per request$'):
        APIBase._require_at_most(501, 500, 'data', 'records')


def test_count_well_ids_sums_list_well_ids_and_ignores_other_shapes() -> None:
    records: ItemList = [{'wellIds': ['a', 'b']}, {'wellIds': 'a'}, {'allWells': True}, {'wellIds': ['c']}]
    assert APIBase._count_well_ids(records) == 3


@pytest.mark.parametrize(
    ('ids', 'expected'),
    [
        ('a', ['a']),
        ('a,b', ['a', 'b']),
        ('a, b', ['a', 'b']),
        (' a ,b ', ['a', 'b']),
        (['a', 'b'], ['a', 'b']),
        ([' a', 'b '], ['a', 'b']),
        (('a',), ['a']),
    ],
)
def test_split_ids_takes_a_comma_string_or_a_sequence(ids: Any, expected: list[str]) -> None:
    assert APIBase._split_ids(ids, 'wells') == expected


@pytest.mark.parametrize(
    ('ids', 'message'),
    [
        ('', 'wells must name at least one id, with no empty id between commas'),
        ('a,', 'wells must name at least one id, with no empty id between commas'),
        ('a,,b', 'wells must name at least one id, with no empty id between commas'),
        (' ', 'wells must name at least one id, with no empty id between commas'),
        ('a, ,b', 'wells must name at least one id, with no empty id between commas'),
        ([' '], 'wells must be a non-empty sequence of non-empty ids'),
        ([], 'wells must be a non-empty sequence of non-empty ids'),
        (['a', ''], 'wells must be a non-empty sequence of non-empty ids'),
    ],
)
def test_split_ids_refuses_a_blank_id(ids: Any, message: str) -> None:
    with pytest.raises(ValueError, match=f'^{message}$'):
        APIBase._split_ids(ids, 'wells')


@pytest.mark.parametrize(
    ('record', 'message'),
    [
        ({'model': 'm'}, r'data\[0\] must have allWells: true or a non-empty wellIds'),
        ({'wellIds': 5}, r'data\[0\] must have allWells: true or a non-empty wellIds'),
        ({'wellIds': []}, r'data\[0\]\.wellIds must be a non-empty sequence of non-empty ids'),
        ({'wellIds': 'w1'}, r'data\[0\]\.wellIds must be a sequence of ids, not a str'),
        ({'wellIds': ['w1', '']}, r'data\[0\]\.wellIds must be a non-empty sequence of non-empty ids'),
        ({'allWells': False}, r'data\[0\] must have allWells: true or a non-empty wellIds'),
    ],
)
def test_require_assignment_wells_refuses_a_record_that_names_no_well(record: Item, message: str) -> None:
    with pytest.raises(ValueError, match=f'^{message}$'):
        APIBase._require_assignment_wells([record])


def test_require_assignment_wells_accepts_all_wells_or_well_ids() -> None:
    APIBase._require_assignment_wells([{'allWells': True}, {'wellIds': ['w1']}])


# Item 2: the econ-model assignment DELETE refuses a record that names no well


@pytest.mark.parametrize('record', [{'model': 'risking'}, {'model': 'risking', 'wellIds': []}])
def test_econ_model_assignment_delete_refuses_a_record_without_wells(monkeypatch: MonkeyPatch, record: Item) -> None:
    transport = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError, match='wellIds'):
        make_offline_api().delete_scenario_econ_model_assignments('p', 'sc', [record])
    assert transport.calls == []


def test_econ_model_assignment_delete_sends_an_all_wells_record(monkeypatch: MonkeyPatch) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(204, [], headers={'X-Delete-Count': '2'}))
    record: Item = {'model': 'risking', 'qualifierName': 'q', 'allWells': True}
    headers = make_offline_api().delete_scenario_econ_model_assignments('p', 'sc', [record])
    assert headers['X-Delete-Count'] == '2'
    assert [(call.method, call.url, call.body) for call in transport.calls] == [
        ('DELETE', f'{SCENARIO}/assignments/econ-models', [record])
    ]


# Item 4: the GET count of a `.../head` sub-route


def test_count_items_with_get_sends_a_get_and_reads_the_header(monkeypatch: MonkeyPatch) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(200, None, headers={'X-Query-Count': '7'}))
    assert make_offline_api()._count_items(f'{V1}/formations/head', method='get') == 7
    assert transport.methods_and_urls == [('GET', f'{V1}/formations/head')]


def test_count_items_without_the_header_names_the_method(monkeypatch: MonkeyPatch) -> None:
    install_recording_transport(monkeypatch, FakeResponse(200, None), FakeResponse(200, None))
    api = make_offline_api()
    with pytest.raises(ValueError, match=r'^GET https://\S+/head returned no X-Query-Count header$'):
        api._count_items(f'{V1}/formations/head', method='get')
    with pytest.raises(ValueError, match=r'^HEAD https://\S+/formations returned no X-Query-Count header$'):
        api._count_items(f'{V1}/formations')


def test_the_formations_and_shapefiles_get_counts_use_the_head_sub_routes(monkeypatch: MonkeyPatch) -> None:
    transport = install_recording_transport(
        monkeypatch, *[FakeResponse(200, None, headers={'X-Query-Count': str(count)}) for count in range(4)]
    )
    api = make_offline_api()
    assert api.count_company_formations_with_get() == 0
    assert api.count_project_formations_with_get('p') == 1
    assert api.count_company_shapefiles_with_get({'name': 'n'}) == 2
    assert api.count_project_shapefiles_with_get('p') == 3
    assert transport.methods_and_urls == [
        ('GET', f'{V1}/formations/head'),
        ('GET', f'{V1}/projects/p/formations/head'),
        ('GET', f'{V1}/shapefiles/head?name=n'),
        ('GET', f'{V1}/projects/p/shapefiles/head'),
    ]


# Item 6: one request, one object


def test_send_for_item_sends_one_request_and_returns_the_object(monkeypatch: MonkeyPatch) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(202, {'jobId': 'j1'}))
    assert make_offline_api()._send_for_item('post', f'{V1}/x', {'a': 1}) == {'jobId': 'j1'}
    [call] = transport.calls
    assert (call.method, call.url, call.body, call.params) == ('POST', f'{V1}/x', {'a': 1}, None)


def test_send_for_item_raises_an_error_status(monkeypatch: MonkeyPatch) -> None:
    install_recording_transport(monkeypatch, FakeResponse(404, {'message': 'not found'}))
    with pytest.raises(requests.HTTPError):
        make_offline_api()._send_for_item('get', f'{V1}/x')


@pytest.mark.parametrize(
    ('call', 'verb', 'url', 'body'),
    [
        (lambda api: api.post_scenario_run('p', 'sc'), 'POST', f'{SCENARIO}/run', {}),
        (lambda api: api.post_export({'exportType': 't'}), 'POST', f'{V1}/exports', {'exportType': 't'}),
        (
            lambda api: api.post_export_econ_monthly({'runId': 'r'}),
            'POST',
            f'{APIBase.API_BASE_URL_V2}/exports/econ-monthly',
            {'runId': 'r'},
        ),
        (
            lambda api: api.get_export_econ_monthly_by_job_id('j1'),
            'GET',
            f'{APIBase.API_BASE_URL_V2}/exports/econ-monthly/j1',
            None,
        ),
    ],
)
def test_the_single_object_methods_send_through_send_for_item(
    monkeypatch: MonkeyPatch, call: Any, verb: str, url: str, body: Any
) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(200, {'jobId': 'j1'}))
    assert call(make_offline_api()) == {'jobId': 'j1'}
    [sent] = transport.calls
    assert (sent.method, sent.url, sent.body) == (verb, url, body)


# Item 5: the job poll


def test_wait_for_job_polls_until_the_status_leaves_pending_and_running(monkeypatch: MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, 'sleep', sleeps.append)
    job_reads: ItemList = [{'status': 'pending'}, {'status': 'running'}, {'status': 'failed'}]
    jobs = iter(job_reads)
    assert APIBase._wait_for_job(lambda: next(jobs), 60.0, 3.0, 'job j1') == {'status': 'failed'}
    assert sleeps == [3.0, 3.0]


def test_wait_for_job_refuses_a_job_with_no_status(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(time, 'sleep', lambda seconds: None)
    with pytest.raises(
        ValueError, match=r"^shapefile job j1 was read with no status; its keys are \['id', 'result'\]$"
    ):
        APIBase._wait_for_job(lambda: {'result': {}, 'id': 'j1'}, 60.0, 3.0, 'shapefile job j1')
    with pytest.raises(ValueError, match='no status'):
        APIBase._wait_for_job(lambda: {'status': None}, 60.0, 3.0, 'shapefile job j1')


def test_wait_for_job_raises_before_a_poll_past_the_timeout(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(time, 'sleep', lambda seconds: None)
    clock = iter([0.0, 1.0, 9.0])
    monkeypatch.setattr(time, 'monotonic', lambda: next(clock))
    with pytest.raises(TimeoutError, match=r"^formations job j1 is still 'running' after 10\.0 seconds$"):
        APIBase._wait_for_job(lambda: {'status': 'running'}, 10.0, 2.0, 'formations job j1')


# Item 7: the sender for a signed url on another host


def _new_connection_error() -> requests.ConnectionError:
    """A refused connection, as `requests` raises it: the request never reached the server."""
    reason = urllib3.exceptions.NewConnectionError(None, 'refused')  # type: ignore[arg-type]
    return requests.ConnectionError(urllib3.exceptions.MaxRetryError(None, SIGNED_URL, reason))  # type: ignore[arg-type]


class _ScriptedTransport:
    """Stands in for `requests.request`: raises or returns `outcomes` in order and keeps every call."""

    def __init__(self, *outcomes: Any) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, method: str, url: str, **kwargs: Any) -> Any:
        self.calls.append({'method': method, 'url': url, **kwargs})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _install_scripted(monkeypatch: MonkeyPatch, *outcomes: Any) -> _ScriptedTransport:
    transport = _ScriptedTransport(*outcomes)
    monkeypatch.setattr(requests, 'request', transport)
    monkeypatch.setattr(time, 'sleep', lambda seconds: None)
    return transport


def test_external_send_carries_only_the_given_headers_and_the_raw_body(monkeypatch: MonkeyPatch) -> None:
    transport = _install_scripted(monkeypatch, FakeResponse(200))
    _transport._send_to_external_url('PUT', SIGNED_URL, {'Content-Type': 'application/zip'}, b'zip')
    [call] = transport.calls
    assert call['headers'] == {'Content-Type': 'application/zip'}
    assert call['data'] == b'zip'
    assert 'json' not in call
    assert call['timeout'] == _transport._REQUEST_TIMEOUT_SECONDS


def test_external_send_retries_a_request_that_never_reached_the_host(monkeypatch: MonkeyPatch) -> None:
    transport = _install_scripted(monkeypatch, _new_connection_error(), FakeResponse(200))
    assert _transport._send_to_external_url('PUT', SIGNED_URL, {}, b'zip').status_code == 200
    assert len(transport.calls) == 2


def test_external_send_does_not_resend_a_write_that_may_have_arrived(monkeypatch: MonkeyPatch) -> None:
    transport = _install_scripted(monkeypatch, requests.ConnectionError('reset'), FakeResponse(200))
    with pytest.raises(requests.ConnectionError, match='reset'):
        _transport._send_to_external_url('PUT', SIGNED_URL, {}, b'zip')
    assert len(transport.calls) == 1


def test_external_send_resends_a_get_after_a_lost_connection(monkeypatch: MonkeyPatch) -> None:
    transport = _install_scripted(monkeypatch, requests.ReadTimeout('slow'), FakeResponse(200))
    assert _transport._send_to_external_url('GET', SIGNED_URL, {}, b'').status_code == 200
    assert len(transport.calls) == 2


def test_external_send_returns_an_error_status_without_retrying_it(monkeypatch: MonkeyPatch) -> None:
    transport = _install_scripted(monkeypatch, FakeResponse(503))
    assert _transport._send_to_external_url('PUT', SIGNED_URL, {}, b'zip').status_code == 503
    assert len(transport.calls) == 1


def test_the_signed_upload_is_not_sent_twice_after_a_lost_connection(monkeypatch: MonkeyPatch) -> None:
    """`put_shapefile_upload_file` sends through the external sender: a PUT whose connection broke after
    it was sent raises, and no auth header is fetched for it."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for name in ('layer.shp', 'layer.shx', 'layer.dbf'):
            archive.writestr(name, b'x')
    auth = StubAuth()
    api = make_offline_api(auth)
    transport = _install_scripted(monkeypatch, requests.ConnectionError('reset'), FakeResponse(200))
    ticket: Item = {'uploadUrl': SIGNED_URL, 'method': 'PUT', 'headers': {'Content-Type': 'application/zip'}}
    with pytest.raises(requests.ConnectionError):
        api.put_shapefile_upload_file(ticket, buffer.getvalue())
    assert len(transport.calls) == 1
    assert auth.fetches == 0


# Item 8: the scenario well removal sends repeated `wells` keys


@pytest.mark.parametrize('wells', ['w1,w2', ['w1', 'w2'], ('w1', 'w2')])
def test_delete_scenario_wells_repeats_the_wells_key(monkeypatch: MonkeyPatch, wells: Any) -> None:
    """A comma-joined `wells` is a live 400 (dev, 2026-11-21); repeated keys remove both wells."""
    transport = install_recording_transport(monkeypatch, FakeResponse(204, None, headers={'X-Delete-Count': '2'}))
    headers = make_offline_api().delete_scenario_wells('p', 'sc', wells)
    assert headers['X-Delete-Count'] == '2'
    assert transport.methods_and_urls == [('DELETE', f'{SCENARIO}/well-assignments?wells=w1&wells=w2')]


def test_delete_scenario_wells_sends_one_id_as_one_key(monkeypatch: MonkeyPatch) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(204, None))
    make_offline_api().delete_scenario_wells('p', 'sc', 'w1')
    assert transport.methods_and_urls == [('DELETE', f'{SCENARIO}/well-assignments?wells=w1')]


@pytest.mark.parametrize(
    ('wells', 'message'),
    [
        ('', 'Must provide at least one of wells'),
        ([], 'wells must be a non-empty sequence of non-empty ids'),
        (['w1', ''], 'wells must be a non-empty sequence of non-empty ids'),
        ('w1,', 'wells must name at least one id, with no empty id between commas'),
    ],
)
def test_delete_scenario_wells_refuses_a_blank_id(monkeypatch: MonkeyPatch, wells: Any, message: str) -> None:
    transport = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError, match=f'^{message}$'):
        make_offline_api().delete_scenario_wells('p', 'sc', wells)
    assert transport.calls == []


# The `wells` cap of the two unassign DELETE routes (100 -> 204, 101 -> 400, live on dev 2026-11-21)

UnassignCall = Callable[[Any, Any], Any]
UNASSIGN_CALLS: list[UnassignCall] = [
    lambda api, wells: api.delete_scenario_wells('p', 'sc', wells),
    lambda api, wells: api.delete_econ_model_assignments_by_type_by_id('p', 'FluidModel', 'm', 'sc', wells=wells),
    lambda api, wells: api.delete_fluid_assignments_by_id('p', 'm', 'sc', wells=wells),
]


def _object_ids(count: int) -> list[str]:
    return [f'{index:024x}' for index in range(1, count + 1)]


@pytest.mark.parametrize('unassign', UNASSIGN_CALLS)
def test_unassign_sends_100_wells_in_one_request(monkeypatch: MonkeyPatch, unassign: UnassignCall) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(204, None))
    unassign(make_offline_api(), _object_ids(WELL_FILTER_LIMIT))
    assert len(transport.calls) == 1
    assert transport.calls[0].url.count('wells=') == WELL_FILTER_LIMIT


@pytest.mark.parametrize('unassign', UNASSIGN_CALLS)
@pytest.mark.parametrize('as_string', [False, True])
def test_unassign_refuses_101_wells_before_sending(
    monkeypatch: MonkeyPatch, unassign: UnassignCall, as_string: bool
) -> None:
    transport = install_recording_transport(monkeypatch)
    wells = _object_ids(WELL_FILTER_LIMIT + 1)
    with pytest.raises(ValueError, match=r'^wells holds 101 well ids; the route takes at most 100 per request$'):
        unassign(make_offline_api(), ','.join(wells) if as_string else wells)
    assert transport.calls == []
