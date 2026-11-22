"""Offline checks of `tests/postman_collection.py`: the collection url agrees with the docstring
generator's, an unusable collection skips the route tests instead of failing them, and the first
outcome is kept for the session."""

import importlib.util
import pathlib
from typing import Any

import pytest
import requests
from pytest import MonkeyPatch

from tests import postman_collection
from tests.http_fakes import FakeResponse

GENERATOR_PATH = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'generate_docstrings.py'
OPERATION = {'name': 'get-sample', 'request': {'method': 'GET', 'url': {'path': ['v1', 'sample']}}}


def _answer_with(monkeypatch: MonkeyPatch, response: FakeResponse) -> list[int]:
    """Patch `requests.get` to answer `response`; returns a one-element list counting the fetches."""
    fetches = [0]

    def get(*arguments: Any, **keywords: Any) -> FakeResponse:
        fetches[0] += 1
        return response

    monkeypatch.setattr(requests, 'get', get)
    return fetches


def _raise_on_get(monkeypatch: MonkeyPatch, error: BaseException) -> None:
    def get(*arguments: Any, **keywords: Any) -> FakeResponse:
        raise error

    monkeypatch.setattr(requests, 'get', get)


def test_the_collection_url_matches_the_docstring_generator() -> None:
    specification = importlib.util.spec_from_file_location('generate_docstrings', GENERATOR_PATH)
    assert specification is not None and specification.loader is not None
    generator = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(generator)

    assert postman_collection.COLLECTION_URL == generator.COLLECTION_URL


@pytest.mark.parametrize(
    'payload',
    [[], None, 'text', {}, {'item': None}, {'item': []}, {'item': [{'name': 'folder without operations'}]}],
)
def test_a_collection_with_no_operation_is_unavailable(monkeypatch: MonkeyPatch, payload: Any) -> None:
    _answer_with(monkeypatch, FakeResponse(200, payload))

    outcome = postman_collection.fetch_collection()

    assert outcome.operations is None
    assert 'operation' in outcome.unavailable_reason


@pytest.mark.parametrize(
    'error',
    [requests.ConnectionError('offline'), OSError('Could not find a suitable TLS CA certificate bundle')],
)
def test_a_transport_or_certificate_failure_is_unavailable(monkeypatch: MonkeyPatch, error: BaseException) -> None:
    _raise_on_get(monkeypatch, error)

    assert postman_collection.fetch_collection().unavailable_reason == str(error)


@pytest.mark.parametrize('response', [FakeResponse(500, {'error': 'x'}), FakeResponse(200, text='<html>')])
def test_an_error_status_or_a_body_that_is_not_json_is_unavailable(
    monkeypatch: MonkeyPatch, response: FakeResponse
) -> None:
    _answer_with(monkeypatch, response)

    assert postman_collection.fetch_collection().operations is None


def test_operations_are_the_leaf_items_of_every_folder(monkeypatch: MonkeyPatch) -> None:
    _answer_with(monkeypatch, FakeResponse(200, {'item': [{'name': 'folder', 'item': [OPERATION]}]}))

    assert postman_collection.fetch_collection().operations == [('get-sample', OPERATION['request'])]


@pytest.mark.parametrize(
    'tree',
    [
        [OPERATION, None],
        [{'name': 'folder', 'item': 'not a list'}, OPERATION],
        [OPERATION, {'name': 'bad', 'request': 'GET /x'}],
    ],
    ids=['entry-not-an-object', 'folder-item-not-a-list', 'request-not-an-object'],
)
def test_a_malformed_entry_makes_the_collection_unavailable(monkeypatch: MonkeyPatch, tree: list[Any]) -> None:
    """As in `scripts/generate_docstrings.py`: a malformed entry gives no verdict, not the usable rest."""
    _answer_with(monkeypatch, FakeResponse(200, {'item': tree}))

    assert postman_collection.fetch_collection().operations is None


def test_an_unavailable_collection_skips_and_is_not_fetched_again(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(postman_collection, '_fetch_outcome', None)
    fetches = _answer_with(monkeypatch, FakeResponse(200, {}))

    for _ in range(2):
        with pytest.raises(pytest.skip.Exception, match='unavailable'):
            postman_collection.collection_requests()

    assert fetches == [1]


def test_an_available_collection_is_fetched_once(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(postman_collection, '_fetch_outcome', None)
    fetches = _answer_with(monkeypatch, FakeResponse(200, {'item': [OPERATION]}))

    first = postman_collection.collection_requests()
    second = postman_collection.collection_requests()

    assert first == second == [('get-sample', OPERATION['request'])]
    assert fetches == [1]
