"""Offline checks for the company econ settings and econ report settings: URLs and the route each method sends.

Both resources share one set of helpers, so each public method is checked against its own resource path.
"""

from typing import Any

import pytest

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.econ_settings import ECON_REPORT_SETTINGS, ECON_SETTINGS, EconSettings
from tests.http_fakes import (
    FakeResponse,
    RecordedCall,
    RecordingTransport,
    install_recording_transport,
    install_responding_transport,
    make_offline_api,
)

BASE = ComboCurveAPI.API_BASE_URL


def _answer_by_verb(call: RecordedCall) -> FakeResponse:
    """A list for a GET, a count for a HEAD, a delete count for a DELETE, a 207 body for a write."""
    if call.method == 'GET':
        return FakeResponse(200, [{'id': 'd1'}])
    if call.method == 'HEAD':
        return FakeResponse(200, headers={'X-Query-Count': '3'})
    if call.method == 'DELETE':
        return FakeResponse(200, [], headers={'X-Delete-Count': '1'})
    return FakeResponse(207, {'results': []})


def _api_with_recorded_calls(monkeypatch: pytest.MonkeyPatch) -> tuple[ComboCurveAPI, RecordingTransport]:
    """An offline client whose every request is recorded and answered by `_answer_by_verb`."""
    return make_offline_api(), install_responding_transport(monkeypatch, _answer_by_verb)


def test_urls_for_both_resources() -> None:
    api = EconSettings.__new__(EconSettings)
    assert api.get_econ_settings_url() == f'{BASE}/econ-settings'
    assert api.get_econ_settings_url({'name': 'A'}) == f'{BASE}/econ-settings?name=A'
    assert api.get_econ_setting_by_id_url('s1') == f'{BASE}/econ-settings/s1'
    assert api.get_econ_report_settings_url() == f'{BASE}/econ-report-settings'
    assert api.get_econ_report_setting_by_id_url('r1') == f'{BASE}/econ-report-settings/r1'


def test_each_method_sends_to_its_own_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    api, transport = _api_with_recorded_calls(monkeypatch)
    body: Any = [{'name': 'x'}]

    api.get_econ_settings()
    api.count_econ_settings({'name': 'x'})
    api.get_econ_setting_by_id('s1')
    api.post_econ_settings(body)
    api.put_econ_settings(body)
    api.patch_econ_settings(body)
    api.delete_econ_setting_by_id('s1')

    api.get_econ_report_settings()
    api.count_econ_report_settings()
    api.get_econ_report_setting_by_id('r1')
    api.post_econ_report_settings(body)
    api.put_econ_report_settings(body)
    api.patch_econ_report_settings(body)
    api.delete_econ_report_setting_by_id('r1')

    settings = f'{BASE}/econ-settings'
    reports = f'{BASE}/econ-report-settings'
    assert transport.methods_and_urls == [
        ('GET', settings),
        ('HEAD', f'{settings}?name=x'),
        ('GET', f'{settings}/s1'),
        ('POST', settings),
        ('PUT', settings),
        ('PATCH', settings),
        ('DELETE', f'{settings}/s1'),
        ('GET', reports),
        ('HEAD', reports),
        ('GET', f'{reports}/r1'),
        ('POST', reports),
        ('PUT', reports),
        ('PATCH', reports),
        ('DELETE', f'{reports}/r1'),
    ]
    # Each write sends the whole body in one request.
    assert [call.body for call in transport.calls if call.method in ('POST', 'PUT', 'PATCH')] == [body] * 6


@pytest.mark.parametrize('resource', [ECON_SETTINGS, ECON_REPORT_SETTINGS])
def test_lists_use_the_shared_record_order(monkeypatch: pytest.MonkeyPatch, resource: str) -> None:
    api = make_offline_api()
    install_recording_transport(
        monkeypatch, FakeResponse(200, [{'name': 'Zulu', 'id': 'z'}, {'name': 'Alpha', 'id': 'a'}])
    )

    call = api.get_econ_settings if resource == ECON_SETTINGS else api.get_econ_report_settings

    assert [item['name'] for item in call()] == ['Alpha', 'Zulu']


def test_by_id_delete_sends_no_body_and_returns_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    api, transport = _api_with_recorded_calls(monkeypatch)
    headers: Any = api.delete_econ_setting_by_id('s1')
    assert headers == {'X-Delete-Count': '1'}
    assert [(call.method, call.url, call.body) for call in transport.calls] == [
        ('DELETE', f'{BASE}/econ-settings/s1', None)
    ]


@pytest.mark.parametrize(
    'write',
    [
        lambda api: api.post_econ_settings([]),
        lambda api: api.put_econ_settings([]),
        lambda api: api.patch_econ_settings([]),
        lambda api: api.post_econ_report_settings([]),
        lambda api: api.put_econ_report_settings([]),
        lambda api: api.patch_econ_report_settings([]),
    ],
)
def test_empty_write_is_refused_before_sending(monkeypatch: pytest.MonkeyPatch, write: Any) -> None:
    api, transport = _api_with_recorded_calls(monkeypatch)
    with pytest.raises(ValueError, match='at least one document'):
        write(api)
    assert transport.calls == []


@pytest.mark.parametrize(
    'write',
    [
        lambda api, record: api.post_econ_settings(record),
        lambda api, record: api.put_econ_settings(record),
        lambda api, record: api.patch_econ_settings(record),
        lambda api, record: api.post_econ_report_settings(record),
        lambda api, record: api.put_econ_report_settings(record),
        lambda api, record: api.patch_econ_report_settings(record),
    ],
)
def test_single_document_is_sent_as_a_one_record_list(monkeypatch: pytest.MonkeyPatch, write: Any) -> None:
    api, transport = _api_with_recorded_calls(monkeypatch)
    record = {'name': 'single'}

    write(api, record)

    assert [call.body for call in transport.calls] == [[record]]
