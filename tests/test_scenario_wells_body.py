"""`post_scenario_wells` / `put_scenario_wells`: the route body is a list of well-id strings, not of objects."""

import pytest
from pytest import MonkeyPatch

from tests.http_fakes import FakeResponse, install_recording_transport, make_offline_api

PROJECT_ID = '000000000000000000000001'
SCENARIO_ID = '000000000000000000000002'
WELL_IDS = ['000000000000000000000005', '000000000000000000000006']
WRITE_ENVELOPE = {'failedCount': 0, 'generalErrors': [], 'results': [], 'successCount': 2}


def test_post_scenario_wells_sends_the_well_ids_as_a_list_of_strings(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(207, WRITE_ENVELOPE))
    well_ids: list[str] = list(WELL_IDS)

    responses = make_offline_api().post_scenario_wells(PROJECT_ID, SCENARIO_ID, well_ids)

    assert responses == [WRITE_ENVELOPE]
    assert len(recorder.calls) == 1
    assert recorder.calls[0].method == 'POST'
    assert recorder.calls[0].url.endswith(f'/v1/projects/{PROJECT_ID}/scenarios/{SCENARIO_ID}/well-assignments')
    assert recorder.calls[0].body == WELL_IDS


def test_put_scenario_wells_sends_the_well_ids_as_a_list_of_strings(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(207, WRITE_ENVELOPE))
    well_ids: tuple[str, ...] = tuple(WELL_IDS)

    make_offline_api().put_scenario_wells(PROJECT_ID, SCENARIO_ID, well_ids)

    assert recorder.calls[0].method == 'PUT'
    assert recorder.calls[0].body == WELL_IDS


@pytest.mark.parametrize('method_name', ['post_scenario_wells', 'put_scenario_wells'])
def test_a_single_string_is_refused_before_anything_is_sent(monkeypatch: MonkeyPatch, method_name: str) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(207, WRITE_ENVELOPE))
    method = getattr(make_offline_api(), method_name)

    with pytest.raises(TypeError, match='sequence of well ids'):
        method(PROJECT_ID, SCENARIO_ID, WELL_IDS[0])

    assert recorder.calls == []
