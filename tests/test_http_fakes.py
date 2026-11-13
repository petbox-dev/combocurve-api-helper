"""The shared recording transport keeps the promises its docstring makes."""

import pytest
import requests
from pytest import MonkeyPatch

from tests.http_fakes import FakeResponse, install_recording_transport


def test_a_request_past_the_queued_responses_raises(monkeypatch: MonkeyPatch) -> None:
    install_recording_transport(monkeypatch, FakeResponse(200, []))
    requests.request('get', 'https://example.invalid/one')

    with pytest.raises(IndexError):
        requests.request('get', 'https://example.invalid/two')


def test_a_keyword_the_transport_does_not_send_fails(monkeypatch: MonkeyPatch) -> None:
    install_recording_transport(monkeypatch, FakeResponse(200, []))

    with pytest.raises(TypeError):
        requests.request('post', 'https://example.invalid', data=b'x')


def test_a_call_is_recorded_with_its_timeout(monkeypatch: MonkeyPatch) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(200, []))

    requests.request('delete', 'https://example.invalid', params={'take': 1}, json=['a'], timeout=5)

    call = transport.calls[0]
    assert (call.method, call.params, call.body, call.timeout) == ('DELETE', {'take': 1}, ['a'], 5)
