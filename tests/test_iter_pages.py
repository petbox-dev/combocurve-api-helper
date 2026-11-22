"""`APIBase.iter_pages`, the public page iterator, and its identity with `_get_items_iterator`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.http_fakes import FakeResponse, install_recording_transport, make_offline_api

if TYPE_CHECKING:
    from pytest import MonkeyPatch

    from combocurve_api_helper import ComboCurveAPI
    from combocurve_api_helper.base import Item, ItemList
    from tests.http_fakes import RecordingTransport

FIRST_URL = 'https://api.combocurve.com/v1/projects?take=2'
SECOND_URL = 'https://api.combocurve.com/v1/projects?take=2&skip=2'
THIRD_URL = 'https://api.combocurve.com/v1/projects?take=2&skip=4'

FIRST_PAGE: ItemList = [{'id': 'a'}, {'id': 'b'}]
SECOND_PAGE: ItemList = [{'id': 'c'}, {'id': 'd'}]
THIRD_PAGE: ItemList = [{'id': 'e'}]


def link(url: str) -> dict[str, str]:
    return {'Link': f'<{url}>;rel="next"'}


def three_pages(monkeypatch: MonkeyPatch) -> RecordingTransport:
    return install_recording_transport(
        monkeypatch,
        FakeResponse(200, FIRST_PAGE, headers=link(SECOND_URL)),
        FakeResponse(200, SECOND_PAGE, headers=link(THIRD_URL)),
        FakeResponse(200, THIRD_PAGE),
    )


def test_two_pages_are_followed_through_the_link_header(monkeypatch: MonkeyPatch) -> None:
    transport = install_recording_transport(
        monkeypatch,
        FakeResponse(200, FIRST_PAGE, headers=link(SECOND_URL)),
        FakeResponse(200, SECOND_PAGE),
    )

    pages = list(make_offline_api().iter_pages(FIRST_URL))

    assert pages == [FIRST_PAGE, SECOND_PAGE]
    assert [call.url for call in transport.calls] == [FIRST_URL, SECOND_URL]


def test_next_page_keeps_the_request_host_when_link_names_another(monkeypatch: MonkeyPatch) -> None:
    internal = 'https://external-api-000000000000.us-central1.run.app/v1/projects?take=2&skip=2'
    transport = install_recording_transport(
        monkeypatch,
        FakeResponse(200, FIRST_PAGE, headers=link(internal)),
        FakeResponse(200, SECOND_PAGE),
    )

    list(make_offline_api().iter_pages(FIRST_URL))

    assert transport.calls[1].url == SECOND_URL


def test_stopping_early_sends_only_the_pages_consumed(monkeypatch: MonkeyPatch) -> None:
    transport = three_pages(monkeypatch)

    iterator = make_offline_api().iter_pages(FIRST_URL)
    assert transport.calls == []  # lazy: nothing is sent before the first read
    first = next(iterator)

    assert first == FIRST_PAGE
    assert [call.url for call in transport.calls] == [FIRST_URL]


def test_params_go_to_the_first_request_only(monkeypatch: MonkeyPatch) -> None:
    transport = install_recording_transport(
        monkeypatch,
        FakeResponse(200, FIRST_PAGE, headers=link(SECOND_URL)),
        FakeResponse(200, SECOND_PAGE),
    )

    list(make_offline_api().iter_pages('https://api.combocurve.com/v1/projects', {'take': 2}))

    assert transport.calls[0].params == {'take': 2}
    assert not transport.calls[1].params


def test_params_already_in_the_url_are_dropped(monkeypatch: MonkeyPatch) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(200, FIRST_PAGE))

    list(make_offline_api().iter_pages(FIRST_URL, {'take': 500}))

    assert not transport.calls[0].params


def test_get_items_iterator_yields_the_same_pages_as_iter_pages(monkeypatch: MonkeyPatch) -> None:
    api: ComboCurveAPI = make_offline_api()
    three_pages(monkeypatch)
    from_public = list(api.iter_pages(FIRST_URL))
    transport = three_pages(monkeypatch)
    from_private = list(api._get_items_iterator(FIRST_URL))

    assert from_private == from_public == [FIRST_PAGE, SECOND_PAGE, THIRD_PAGE]
    assert [call.url for call in transport.calls] == [FIRST_URL, SECOND_URL, THIRD_URL]


def test_get_items_flattens_what_iter_pages_yields(monkeypatch: MonkeyPatch) -> None:
    three_pages(monkeypatch)

    items: list[Item] = make_offline_api()._get_items(FIRST_URL)

    assert [item['id'] for item in items] == ['a', 'b', 'c', 'd', 'e']
