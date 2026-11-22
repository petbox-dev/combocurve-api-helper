"""Offline checks of the route-manifest tooling (`tests/route_manifest.py`, `scripts/generate_route_coverage.py`):
how a sent request is matched to a collection template, how arguments are made up, which methods raise on
the fake transport, and the generator's exit code when the collection is unavailable."""

from __future__ import annotations

import http.client
import importlib.util
import inspect
import sys

# `_placeholder_for` evaluates `_function_with_annotations`'s annotations in this module at run time, so the
# names they use are imported at run time, not under TYPE_CHECKING.
from collections.abc import Mapping, Sequence  # noqa: TC003
from pathlib import Path
from types import ModuleType  # noqa: TC003
from typing import Any, Literal

import pytest
import requests

from combocurve_api_helper.base import Item, ItemList  # noqa: TC001
from tests.http_fakes import FakeResponse
from tests.postman_collection import PLACEHOLDER
from tests.route_manifest import (
    ARGUMENT_OVERRIDES,
    EXPECTED_CAPPED,
    EXPECTED_EXCEPTIONS,
    SENDS_NOTHING_BY_DESIGN,
    Route,
    Template,
    _placeholder_for,
    area_of,
    build_manifest,
    match_score,
    operations_from_collection,
    public_method_names,
    routes_reached,
    sent_by_method,
    template_segments,
)

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'generate_route_coverage.py'


def _template(text: str) -> Template:
    verb, path = text.split(' ', 1)
    return (verb, tuple(path.strip('/').split('/')))


# --- collection templates -------------------------------------------------------------------------


def test_id_parameters_become_p_and_literal_valued_parameters_keep_their_name() -> None:
    raw = ['v1', 'projects', ':projectId', 'econ-models', ':econName', ':econModelId', 'assignments']
    assert template_segments(raw) == ('v1', 'projects', ':p', 'econ-models', ':econName', ':p', 'assignments')
    assert template_segments(['v1', 'custom-columns', ':collection']) == ('v1', 'custom-columns', ':collection')
    assert template_segments(['v1', 'wells', ':id']) == ('v1', 'wells', ':p')


def test_operations_from_collection_skips_a_request_with_no_path() -> None:
    items: list[tuple[str, dict[str, Any]]] = [
        ('get-thing', {'method': 'get', 'url': {'path': ['v1', 'projects', ':projectId', 'things', ':id']}}),
        ('no-path', {'method': 'GET', 'url': {}}),
    ]
    assert operations_from_collection(items) == [
        ('get-thing', 'things', 'GET', ('v1', 'projects', ':p', 'things', ':p'))
    ]


def test_area_skips_literal_valued_parameters() -> None:
    assert area_of(('v1', 'projects', ':p', 'econ-models', ':econName', ':p', 'assignments')) == 'econ-models'
    assert area_of(('v1', ':collection')) == 'projects'


# --- matching -------------------------------------------------------------------------------------


def test_an_id_parameter_does_not_match_a_sent_literal() -> None:
    assert match_score(('v1', 'econ-models', ':p'), ('v1', 'econ-models', 'actual-forecast')) is None
    assert match_score(('v1', 'econ-models', ':p'), ('v1', 'econ-models', ':p')) == 2


def test_a_literal_valued_parameter_matches_any_sent_segment() -> None:
    template = ('v1', 'custom-columns', ':collection')
    assert match_score(template, ('v1', 'custom-columns', 'wells')) is not None
    assert match_score(template, ('v1', 'custom-columns', ':p')) is not None


def test_a_sent_literal_reaches_only_the_most_specific_template() -> None:
    literal = _template('GET /v1/runs/:p/one-liners/combo-names')
    parameterized = _template('GET /v1/runs/:p/one-liners/:name')
    sent = {'get_combo_names': {_template('GET /v1/runs/:p/one-liners/combo-names')}}
    assert routes_reached([literal, parameterized], sent) == {literal: ['get_combo_names']}


def test_a_list_method_does_not_reach_the_by_id_route() -> None:
    """The defect this matcher fixes: `/v1/econ-models/actual-forecast` credited `GET /v1/econ-models/:p`."""
    by_id = _template('GET /v1/econ-models/:p')
    sent = {
        'get_company_actual_forecast_models': {_template('GET /v1/econ-models/actual-forecast')},
        'get_company_econ_model_by_id': {_template('GET /v1/econ-models/:p')},
    }
    assert routes_reached([by_id], sent) == {by_id: ['get_company_econ_model_by_id']}
    del sent['get_company_econ_model_by_id']
    assert routes_reached([by_id], sent) == {}


def test_a_literal_valued_parameter_takes_a_literal_when_no_sibling_spells_it() -> None:
    template = _template('GET /v1/projects/:p/econ-models/:econName/:p/assignments')
    sent = {'get_fluid_assignments': {_template('GET /v1/projects/:p/econ-models/fluid-models/:p/assignments')}}
    assert routes_reached([template], sent) == {template: ['get_fluid_assignments']}


def test_a_hand_kept_status_survives_the_new_spelling_of_a_literal_valued_parameter() -> None:
    previous = [Route('GET', '/v1/custom-columns/:p', 'get-custom-columns', 'custom-columns', 'retired', note='gone')]
    operations: list[tuple[str, str, str, tuple[str, ...]]] = [
        ('get-custom-columns', 'custom-columns', 'GET', ('v1', 'custom-columns', ':collection'))
    ]
    assert build_manifest(operations, {}, previous) == [
        Route('GET', '/v1/custom-columns/:collection', 'get-custom-columns', 'custom-columns', 'retired', note='gone')
    ]


# --- made-up arguments ----------------------------------------------------------------------------


def _function_with_annotations(
    sequence_of_items: Sequence[Item],
    item_or_items: Item | ItemList,
    items: ItemList,
    names: Sequence[str],
    frequency: Literal['daily', 'monthly'],
    count: int | None,
    mapping: Mapping[str, str],
    flag: bool,
    name: str,
) -> None:
    """Annotations `_placeholder_for` is checked against."""


def test_placeholder_values_follow_the_resolved_annotation() -> None:
    parameters = inspect.signature(_function_with_annotations).parameters
    values = {name: _placeholder_for(_function_with_annotations, parameter) for name, parameter in parameters.items()}
    assert values == {
        'sequence_of_items': [{'id': PLACEHOLDER}],
        'item_or_items': {'id': PLACEHOLDER},
        'items': [{'id': PLACEHOLDER}],
        'names': [PLACEHOLDER],
        'frequency': 'daily',
        'count': 1,
        'mapping': {'id': PLACEHOLDER},
        'flag': False,
        'name': PLACEHOLDER,
    }


def test_an_annotation_that_cannot_be_evaluated_falls_back_to_its_text() -> None:
    def function(items: Any, other: Any) -> None:
        """Annotations replaced below with names that do not exist."""

    function.__annotations__ = {'items': 'Sequence[UnknownItem]', 'other': 'UnknownAlias'}
    parameters = inspect.signature(function).parameters
    assert _placeholder_for(function, parameters['other']) == PLACEHOLDER
    assert _placeholder_for(function, parameters['items']) == PLACEHOLDER


# --- calling every public method ------------------------------------------------------------------


def test_argument_overrides_name_existing_public_methods() -> None:
    unknown = sorted(set(ARGUMENT_OVERRIDES) - set(public_method_names()))
    assert not unknown, f'ARGUMENT_OVERRIDES keys that are not public methods (renamed?): {unknown}'


def test_every_public_method_sends_except_the_pure_helpers() -> None:
    assert sorted(sent_by_method().silent) == sorted(SENDS_NOTHING_BY_DESIGN)


def test_the_exceptions_raised_on_the_fake_transport_are_the_reviewed_ones() -> None:
    raised = sent_by_method().exceptions
    unexpected = sorted(raised - EXPECTED_EXCEPTIONS)
    no_longer_raised = sorted(EXPECTED_EXCEPTIONS - raised)
    assert not unexpected, (
        f'new (method, exception) on the fake transport; check the method still sends every route, then '
        f'add it to EXPECTED_EXCEPTIONS: {unexpected}'
    )
    assert not no_longer_raised, f'no longer raised; remove from EXPECTED_EXCEPTIONS: {no_longer_raised}'


def test_no_unexpected_method_reaches_the_request_cap() -> None:
    assert sent_by_method().capped == set(EXPECTED_CAPPED)


# --- the generator's exit codes -------------------------------------------------------------------


@pytest.fixture(scope='module')
def generator() -> ModuleType:
    specification = importlib.util.spec_from_file_location('generate_route_coverage', _SCRIPT_PATH)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _raise(error: BaseException) -> Any:
    def fake_get(*arguments: Any, **keywords: Any) -> Any:
        raise error

    return fake_get


def _answer(response: FakeResponse) -> Any:
    def fake_get(*arguments: Any, **keywords: Any) -> FakeResponse:
        return response

    return fake_get


@pytest.mark.parametrize(
    'fake_get',
    [
        _raise(requests.Timeout('read timed out')),
        _raise(requests.ConnectionError('offline')),
        _raise(OSError('certificate store')),
        _raise(http.client.IncompleteRead(b'')),
        _answer(FakeResponse(503, {})),
        _answer(FakeResponse(200, text='<html>captive portal</html>')),
        _answer(FakeResponse(200, ['not', 'an', 'object'])),
        _answer(FakeResponse(200, {'info': {}})),
        _answer(FakeResponse(200, {'item': []})),
    ],
    ids=['timeout', 'connection', 'oserror', 'incomplete-read', 'http-503', 'not-json', 'list', 'no-item', 'empty'],
)
def test_an_unusable_live_collection_exits_2(
    generator: ModuleType, fake_get: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(requests, 'get', fake_get)
    monkeypatch.setattr(sys, 'argv', ['generate_route_coverage.py', '--check'])
    assert generator.main() == 2
    assert 'could not use the collection' in capsys.readouterr().err


def test_a_bad_local_collection_raises_rather_than_exit_2(
    generator: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    not_a_collection = tmp_path / 'collection.json'
    not_a_collection.write_text('{"info": {}}', encoding='utf-8')
    monkeypatch.setattr(sys, 'argv', ['generate_route_coverage.py', '--check', '--collection', str(not_a_collection)])
    with pytest.raises(ValueError, match='not a Postman collection'):
        generator.main()
    monkeypatch.setattr(sys, 'argv', ['generate_route_coverage.py', '--check', '--collection', str(tmp_path / 'x')])
    with pytest.raises(OSError):
        generator.main()
