"""Offline checks for the directional-survey batch upsert and delete by id: the url and verb each method
sends, the body, and the requests refused before anything is sent."""

from typing import Any

import pytest

from combocurve_api_helper.directional import Directional
from tests.http_fakes import V1, FakeResponse, StubAuth, install_recording_transport

BASE = V1
WRITE_ENVELOPE: Any = {'results': [], 'generalErrors': [], 'successCount': 1, 'failedCount': 0}


def test_directional_survey_batch_posts_the_records_to_the_batch_route(monkeypatch: pytest.MonkeyPatch) -> None:
    api = Directional(auth=StubAuth())
    surveys: Any = [{'chosenID': 'a', 'dataSource': 'other', 'measuredDepth': [0.0, 100.0]}]
    transport = install_recording_transport(monkeypatch, FakeResponse(207, WRITE_ENVELOPE))

    assert api.get_directional_surveys_batch_url() == f'{BASE}/directional-surveys/batch'
    assert api.post_directional_surveys_batch(surveys) == [WRITE_ENVELOPE]
    assert [(call.method, call.url, call.body) for call in transport.calls] == [
        ('POST', f'{BASE}/directional-surveys/batch', surveys)
    ]


def test_directional_survey_batch_refuses_an_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError, match='at least one directional survey'):
        Directional(auth=StubAuth()).post_directional_surveys_batch([])
    assert transport.calls == []


def test_directional_survey_delete_by_id_returns_the_headers_of_an_empty_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The route answers a success with an empty body (verified live 2026-11-21 on dev); reading that body
    # as JSON raised after the survey was already deleted.
    transport = install_recording_transport(monkeypatch, FakeResponse(204, text='', headers={'X-Delete-Count': '1'}))

    headers = Directional(auth=StubAuth()).delete_directional_survey_by_id('s1')

    assert headers['x-delete-count'] == '1'
    assert [(call.method, call.url, call.body) for call in transport.calls] == [
        ('DELETE', f'{BASE}/directional-surveys/s1', None)
    ]
