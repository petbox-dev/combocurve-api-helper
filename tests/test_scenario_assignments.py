from typing import Any

import pytest

from combocurve_api_helper.scenarios import Scenarios


def test_scenario_assignments_url_and_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    s = Scenarios.__new__(Scenarios)
    monkeypatch.setattr(s, 'get_scenario_by_id_url', lambda p, sc: f'BASE/{p}/{sc}')
    assert s.get_scenario_econ_model_assignments_url('p', 'sc') == 'BASE/p/sc/assignments/econ-models'
    monkeypatch.setattr(s, '_get_items', lambda url: [('grid', url)])
    result: object = s.get_scenario_econ_model_assignments('p', 'sc')
    assert result == [('grid', 'BASE/p/sc/assignments/econ-models')]


class _StubResponse:
    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


def test_delete_scenario_qualifiers_uses_plural_econ_names(monkeypatch: pytest.MonkeyPatch) -> None:
    s = Scenarios.__new__(Scenarios)
    monkeypatch.setattr(s, 'get_scenario_by_id_url', lambda p, sc: f'BASE/{p}/{sc}')

    captured_urls: list[str] = []

    def fake_delete_responses(url: str, data: Any) -> list[_StubResponse]:
        captured_urls.append(url)
        return [_StubResponse(headers={'X-Delete-Count': '1'})]

    monkeypatch.setattr(s, '_delete_responses', fake_delete_responses)

    headers: Any = s.delete_scenario_qualifiers('p', 'sc', 'dates', 'P50')

    assert headers == {'X-Delete-Count': '1'}
    assert len(captured_urls) == 1
    url = captured_urls[0]
    assert 'econNames=dates' in url
    assert 'qualifierNames=P50' in url
    assert 'econName=' not in url.replace('econNames=', '')


def test_well_incrementals_url_and_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    s = Scenarios.__new__(Scenarios)
    monkeypatch.setattr(s, 'get_scenario_wells_url', lambda p, sc: f'BASE/{p}/{sc}/well-assignments')
    assert s.get_scenario_well_incrementals_url('p', 'sc') == 'BASE/p/sc/well-assignments/incrementals'
    filtered_url = s.get_scenario_well_incrementals_url('p', 'sc', {'wellId': 'w1'})
    assert filtered_url.startswith('BASE/p/sc/well-assignments/incrementals?')
    assert 'wellId=w1' in filtered_url
    monkeypatch.setattr(s, '_get_items', lambda url: [('inc', url)])
    result: object = s.get_scenario_well_incrementals('p', 'sc')
    assert result == [('inc', 'BASE/p/sc/well-assignments/incrementals')]


def test_econ_model_assignment_put_and_delete_send_one_request_and_refuse_over_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s = Scenarios.__new__(Scenarios)
    monkeypatch.setattr(s, 'get_scenario_by_id_url', lambda p, sc: f'BASE/{p}/{sc}')
    put_calls: list[tuple[str, int]] = []
    delete_calls: list[tuple[str, int]] = []

    def fake_put_items(url: str, data: Any, chunksize: Any = None) -> list[Any]:
        put_calls.append((url, len(data)))
        return [{'status': 'ok'}]

    def fake_delete_responses(url: str, data: Any, chunksize: Any = None) -> list[_StubResponse]:
        delete_calls.append((url, len(data)))
        return [_StubResponse(headers={'X-Delete-Count': '1'})]

    monkeypatch.setattr(s, '_put_items', fake_put_items)
    monkeypatch.setattr(s, '_delete_responses', fake_delete_responses)

    records: Any = [{'model': 'pricing'}]
    put_result: Any = s.put_scenario_econ_model_assignments('p', 'sc', records)
    assert put_result == [{'status': 'ok'}]
    headers: Any = s.delete_scenario_econ_model_assignments('p', 'sc', [{'model': 'risking'}])
    assert headers == {'X-Delete-Count': '1'}
    assert put_calls == [('BASE/p/sc/assignments/econ-models', 1)]
    assert delete_calls == [('BASE/p/sc/assignments/econ-models', 1)]

    over_limit: Any = [{'model': 'pricing'}] * 501
    with pytest.raises(ValueError):
        s.put_scenario_econ_model_assignments('p', 'sc', over_limit)
    with pytest.raises(ValueError):
        s.delete_scenario_econ_model_assignments('p', 'sc', over_limit)
    with pytest.raises(ValueError):
        s.put_scenario_econ_model_assignments('p', 'sc', [])
    assert len(put_calls) == 1
    assert len(delete_calls) == 1
