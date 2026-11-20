"""Offline checks for the company econ settings and econ report settings: URLs and the route each method sends.

Both resources share one set of helpers, so each public method is checked against its own resource path.
"""

from typing import Any

import pytest

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.econ_settings import EconSettings

BASE = ComboCurveAPI.API_BASE_URL


class _StubResponse:
    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


def _api_with_recorded_calls(monkeypatch: pytest.MonkeyPatch) -> tuple[EconSettings, list[tuple[str, str, Any]]]:
    """An EconSettings whose transport methods record (verb, url, body) instead of sending."""
    api = EconSettings.__new__(EconSettings)
    calls: list[tuple[str, str, Any]] = []

    def record_get(url: str, params: Any = None) -> list[Any]:
        calls.append(('get', url, params))
        return [{'id': 'd1'}]

    def record_count(url: str) -> int:
        calls.append(('head', url, None))
        return 3

    def record_write(verb: str) -> Any:
        def write(url: str, data: Any, chunksize: Any = None) -> list[Any]:
            calls.append((verb, url, data))
            return [{'results': []}]

        return write

    def record_delete(url: str, data: Any, chunksize: Any = None) -> list[_StubResponse]:
        calls.append(('delete', url, data))
        return [_StubResponse({'X-Delete-Count': '1'})]

    monkeypatch.setattr(api, '_get_items', record_get)
    monkeypatch.setattr(api, '_count_items', record_count)
    monkeypatch.setattr(api, '_post_items', record_write('post'))
    monkeypatch.setattr(api, '_put_items', record_write('put'))
    monkeypatch.setattr(api, '_patch_items', record_write('patch'))
    monkeypatch.setattr(api, '_delete_responses', record_delete)
    return api, calls


def test_urls_for_both_resources() -> None:
    api = EconSettings.__new__(EconSettings)
    assert api.get_econ_settings_url() == f'{BASE}/econ-settings'
    assert api.get_econ_settings_url({'name': 'A'}) == f'{BASE}/econ-settings?name=A'
    assert api.get_econ_setting_by_id_url('s1') == f'{BASE}/econ-settings/s1'
    assert api.get_econ_report_settings_url() == f'{BASE}/econ-report-settings'
    assert api.get_econ_report_setting_by_id_url('r1') == f'{BASE}/econ-report-settings/r1'


def test_each_method_sends_to_its_own_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    api, calls = _api_with_recorded_calls(monkeypatch)
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

    urls = [(verb, url) for verb, url, _ in calls]
    settings = f'{BASE}/econ-settings'
    reports = f'{BASE}/econ-report-settings'
    assert urls == [
        ('get', settings),
        ('head', f'{settings}?name=x'),
        ('get', f'{settings}/s1'),
        ('post', settings),
        ('put', settings),
        ('patch', settings),
        ('delete', f'{settings}/s1'),
        ('get', reports),
        ('head', reports),
        ('get', f'{reports}/r1'),
        ('post', reports),
        ('put', reports),
        ('patch', reports),
        ('delete', f'{reports}/r1'),
    ]


def test_by_id_delete_sends_no_body_and_returns_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    api, calls = _api_with_recorded_calls(monkeypatch)
    headers: Any = api.delete_econ_setting_by_id('s1')
    assert headers == {'X-Delete-Count': '1'}
    assert calls == [('delete', f'{BASE}/econ-settings/s1', [])]


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
    api, calls = _api_with_recorded_calls(monkeypatch)
    with pytest.raises(ValueError, match='at least one document'):
        write(api)
    assert calls == []
