"""The shared recording transport keeps the promises its docstring makes."""

import pytest
import requests
from pytest import MonkeyPatch

from tests.http_fakes import FakeResponse, RecordedCall, install_recording_transport, install_responding_transport


def test_a_request_past_the_queued_responses_raises(monkeypatch: MonkeyPatch) -> None:
    install_recording_transport(monkeypatch, FakeResponse(200, []))
    requests.request('get', 'https://example.invalid/one')

    with pytest.raises(IndexError):
        requests.request('get', 'https://example.invalid/two')


def test_a_keyword_the_transport_does_not_send_fails(monkeypatch: MonkeyPatch) -> None:
    install_recording_transport(monkeypatch, FakeResponse(200, []))

    with pytest.raises(TypeError):
        requests.request('post', 'https://example.invalid', files={'f': b'x'})


def test_a_call_is_recorded_with_its_timeout(monkeypatch: MonkeyPatch) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(200, []))

    requests.request('delete', 'https://example.invalid', params={'take': 1}, json=['a'], timeout=5)

    call = transport.calls[0]
    assert (call.method, call.params, call.body, call.timeout) == ('DELETE', {'take': 1}, ['a'], 5)


def test_a_call_is_recorded_with_its_headers_and_raw_data(monkeypatch: MonkeyPatch) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(200))

    requests.request('put', 'https://upload.invalid/signed', headers={'Content-Type': 'application/zip'}, data=b'zip')

    call = transport.calls[0]
    assert (call.headers, call.data, call.body) == ({'Content-Type': 'application/zip'}, b'zip', None)


def test_a_responding_transport_answers_each_request_from_the_call(monkeypatch: MonkeyPatch) -> None:
    def echo(call: RecordedCall) -> FakeResponse:
        return FakeResponse(200, call.body)

    transport = install_responding_transport(monkeypatch, echo)

    first = requests.request('post', 'https://example.invalid', json=['a'])
    second = requests.request('post', 'https://example.invalid', json=['b', 'c'])

    assert (first.json(), second.json()) == (['a'], ['b', 'c'])
    assert transport.methods_and_urls == [('POST', 'https://example.invalid')] * 2
