from typing import Any

import pytest

from tests.http_fakes import V1, FakeResponse, install_recording_transport, make_offline_api

SCENARIO = f'{V1}/projects/p/scenarios/sc'


def test_scenario_assignments_url_and_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    api = make_offline_api()
    assert api.get_scenario_econ_model_assignments_url('p', 'sc') == f'{SCENARIO}/assignments/econ-models'
    transport = install_recording_transport(monkeypatch, FakeResponse(200, [{'grid': 'row'}]))
    result: object = api.get_scenario_econ_model_assignments('p', 'sc')
    assert result == [{'grid': 'row'}]
    assert [(call.method, call.url, call.params) for call in transport.calls] == [
        ('GET', f'{SCENARIO}/assignments/econ-models', None)
    ]


def test_delete_scenario_qualifiers_uses_plural_econ_names(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(200, [], headers={'X-Delete-Count': '1'}))

    headers: Any = make_offline_api().delete_scenario_qualifiers('p', 'sc', 'dates', 'P50')

    assert headers == {'X-Delete-Count': '1'}
    (call,) = transport.calls
    assert (call.method, call.body) == ('DELETE', None)
    assert 'econNames=dates' in call.url
    assert 'qualifierNames=P50' in call.url
    assert 'econName=' not in call.url.replace('econNames=', '')


def test_well_incrementals_url_and_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    api = make_offline_api()
    incrementals = f'{SCENARIO}/well-assignments/incrementals'
    assert api.get_scenario_well_incrementals_url('p', 'sc') == incrementals
    filtered_url = api.get_scenario_well_incrementals_url('p', 'sc', {'wellId': 'w1'})
    assert filtered_url.startswith(f'{incrementals}?')
    assert 'wellId=w1' in filtered_url
    transport = install_recording_transport(monkeypatch, FakeResponse(200, [{'inc': 1}]))
    result: object = api.get_scenario_well_incrementals('p', 'sc')
    assert result == [{'inc': 1}]
    assert [(call.method, call.url, call.params) for call in transport.calls] == [('GET', incrementals, {'take': 500})]


def test_econ_model_assignment_put_and_delete_send_one_request_and_refuse_over_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = make_offline_api()
    transport = install_recording_transport(
        monkeypatch,
        FakeResponse(207, [{'status': 'ok'}]),
        FakeResponse(200, [], headers={'X-Delete-Count': '1'}),
        FakeResponse(207, [{'status': 'ok'}]),
    )

    records: Any = [{'model': 'pricing'}]
    put_result: Any = api.put_scenario_econ_model_assignments('p', 'sc', records)
    assert put_result == [{'status': 'ok'}]
    headers: Any = api.delete_scenario_econ_model_assignments('p', 'sc', [{'model': 'risking', 'wellIds': ['w1']}])
    assert headers == {'X-Delete-Count': '1'}
    # These writes are all-or-nothing: 500 records (the limit) still go as ONE request, not split.
    at_limit: Any = [{'model': 'pricing'}] * 500
    api.put_scenario_econ_model_assignments('p', 'sc', at_limit)
    assert [(call.method, call.url, call.body) for call in transport.calls] == [
        ('PUT', f'{SCENARIO}/assignments/econ-models', records),
        ('DELETE', f'{SCENARIO}/assignments/econ-models', [{'model': 'risking', 'wellIds': ['w1']}]),
        ('PUT', f'{SCENARIO}/assignments/econ-models', at_limit),
    ]

    over_limit: Any = [{'model': 'pricing'}] * 501
    with pytest.raises(ValueError):
        api.put_scenario_econ_model_assignments('p', 'sc', over_limit)
    with pytest.raises(ValueError):
        api.delete_scenario_econ_model_assignments('p', 'sc', [{'model': 'risking', 'wellIds': ['w1']}] * 501)
    with pytest.raises(ValueError):
        api.put_scenario_econ_model_assignments('p', 'sc', [])
    assert len(transport.calls) == 3
