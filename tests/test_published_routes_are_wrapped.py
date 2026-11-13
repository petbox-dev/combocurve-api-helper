"""Every route in the ComboCurve Postman collection has a method, or a reviewed entry in `_UNWRAPPED`.

Call-based: each public method of `ComboCurveAPI` is called once on a fake transport with
placeholder arguments, and every (verb, path) it sends is recorded. A collection operation that no
call reaches must be listed in `_UNWRAPPED`, so a route that ComboCurve publishes fails this test
until someone wraps it or records the decision. An `_UNWRAPPED` entry that a method now reaches
fails too, so the list cannot go stale.

This complements `test_route_paths.py`, which checks the path a docstring-linked method builds.
That test cannot see a route with no method; this one can.

Network-dependent, skipped when the collection can't be fetched -- same policy as
`test_route_paths.py` / `test_docstring_slugs.py`.
(docs/todo/open/no-test-checks-that-published-routes-are-wrapped.md)
"""

from __future__ import annotations

import inspect
import re
import warnings
from collections.abc import Iterator
from typing import Any
from urllib.parse import urlsplit

import pytest
import requests
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI
from tests.http_fakes import FakeResponse, make_offline_api

# Mirrors scripts/generate_docstrings.py COLLECTION_URL (the collection is never vendored).
_COLLECTION_URL = 'https://docs.api.combocurve.com/downloads/combocurve-api.postman_collection.json'

# A 24-hex ObjectId stands in for every id argument, so it is recognizable again in a sent path.
_PLACEHOLDER = '0' * 24
_ID_SEGMENT = re.compile(rf'^(?:{_PLACEHOLDER}|:.*)$')

# A method that polls would loop on the fake transport; this many requests from one call is enough
# to record its routes.
_MAX_REQUESTS_PER_CALL = 5

# Arguments that the annotation alone cannot fill: a value the method validates before it sends.
_ARGUMENT_OVERRIDES: dict[str, dict[str, Any]] = {
    'delete_company_wells': {'well_id': _PLACEHOLDER},
    'delete_project_company_wells': {'well_id': _PLACEHOLDER},
    'delete_project_wells': {'well_id': _PLACEHOLDER},
    'delete_scenarios': {'scenario_id': _PLACEHOLDER},
    'delete_type_curves': {'id': _PLACEHOLDER},
    'get_project_custom_columns': {'custom_column': 'wells'},
    'count_root_forecast_daily_volumes': {'filters': {'project': _PLACEHOLDER}},
    'count_root_forecast_monthly_volumes': {'filters': {'project': _PLACEHOLDER}},
    'get_root_forecast_daily_volumes': {'filters': {'project': _PLACEHOLDER}},
    'get_root_forecast_monthly_volumes': {'filters': {'project': _PLACEHOLDER}},
}
# A by-type method (`econ_model_type` argument) is called once per econ-model type, because it
# is the only method for some routes (the company POST/PUT/HEAD of most types).
_ECON_MODEL_TYPES = sorted({str(entry['econModelType']) for entry in ComboCurveAPI.ECON_MODELS})

# Public methods that send no request: pure helpers.
_SENDS_NOTHING_BY_DESIGN = ('extract_id', 'index_of')

# Collection operations with no method, reviewed 2026-11-12 (97: the 79 of
# docs/todo/open/published-routes-without-a-method.md, the 17 retired v1 type-curve routes, and the
# OAuth token route). Key: 'VERB /path' with `:p` for each path parameter. Value: the area.
# ComboCurve retired the v1 type-curve routes on 2026-11-07; the compatibility wrappers call v2.
_UNWRAPPED: dict[str, str] = {
    'POST /v1/directional-surveys/batch': 'Directional-survey batch',
    'DELETE /v1/econ-report-settings/:p': 'Econ report settings',
    'GET /v1/econ-report-settings': 'Econ report settings',
    'GET /v1/econ-report-settings/:p': 'Econ report settings',
    'HEAD /v1/econ-report-settings': 'Econ report settings',
    'PATCH /v1/econ-report-settings': 'Econ report settings',
    'POST /v1/econ-report-settings': 'Econ report settings',
    'PUT /v1/econ-report-settings': 'Econ report settings',
    'DELETE /v1/econ-settings/:p': 'Econ settings',
    'GET /v1/econ-settings': 'Econ settings',
    'GET /v1/econ-settings/:p': 'Econ settings',
    'HEAD /v1/econ-settings': 'Econ settings',
    'PATCH /v1/econ-settings': 'Econ settings',
    'POST /v1/econ-settings': 'Econ settings',
    'PUT /v1/econ-settings': 'Econ settings',
    'PUT /v1/projects/:p/forecasts/:p/daily-volumes': 'Forecast volumes PUT',
    'PUT /v1/projects/:p/forecasts/:p/monthly-volumes': 'Forecast volumes PUT',
    'DELETE /v1/forecast-configurations': 'Forecast-configurations DELETE',
    'DELETE /v1/formations/:p': 'Formations',
    'DELETE /v1/projects/:p/formations/:p': 'Formations',
    'GET /v1/formations': 'Formations',
    'GET /v1/formations/:p': 'Formations',
    'GET /v1/formations/:p/points': 'Formations',
    'GET /v1/formations/head': 'Formations',
    'GET /v1/formations/jobs/:p': 'Formations',
    'GET /v1/projects/:p/formations': 'Formations',
    'GET /v1/projects/:p/formations/:p': 'Formations',
    'GET /v1/projects/:p/formations/:p/points': 'Formations',
    'GET /v1/projects/:p/formations/head': 'Formations',
    'GET /v1/projects/:p/formations/jobs/:p': 'Formations',
    'HEAD /v1/formations': 'Formations',
    'HEAD /v1/projects/:p/formations': 'Formations',
    'PATCH /v1/formations': 'Formations',
    'PATCH /v1/projects/:p/formations': 'Formations',
    'PUT /v1/formations': 'Formations',
    'PUT /v1/projects/:p/formations': 'Formations',
    'POST /v1/oauth/token': 'OAuth token (auth.py posts to it directly, not through a method)',
    'GET /v1/production-comment-types': 'Production comment types',
    'PATCH /v1/production-comment-types': 'Production comment types',
    'DELETE /v1/production-comments': 'Production comments',
    'DELETE /v1/production-comments/:p': 'Production comments',
    'DELETE /v1/projects/:p/production-comments': 'Production comments',
    'DELETE /v1/projects/:p/production-comments/:p': 'Production comments',
    'GET /v1/production-comments': 'Production comments',
    'GET /v1/production-comments/:p': 'Production comments',
    'GET /v1/projects/:p/production-comments': 'Production comments',
    'GET /v1/projects/:p/production-comments/:p': 'Production comments',
    'HEAD /v1/production-comments': 'Production comments',
    'HEAD /v1/projects/:p/production-comments': 'Production comments',
    'PATCH /v1/production-comments': 'Production comments',
    'PATCH /v1/projects/:p/production-comments': 'Production comments',
    'POST /v1/production-comments': 'Production comments',
    'POST /v1/projects/:p/production-comments': 'Production comments',
    'PUT /v1/production-comments': 'Production comments',
    'PUT /v1/projects/:p/production-comments': 'Production comments',
    'PATCH /v1/projects/:p/company-wells': 'Project company-wells PATCH',
    'DELETE /v1/projects/:p/scenarios/:p/assignments/econ-models': 'Scenario econ-model assignment PUT and DELETE',
    'PUT /v1/projects/:p/scenarios/:p/assignments/econ-models': 'Scenario econ-model assignment PUT and DELETE',
    'DELETE /v1/projects/:p/shapefiles/:p': 'Shapefiles',
    'DELETE /v1/shapefiles/:p': 'Shapefiles',
    'GET /v1/projects/:p/shapefiles': 'Shapefiles',
    'GET /v1/projects/:p/shapefiles/:p': 'Shapefiles',
    'GET /v1/projects/:p/shapefiles/:p/features': 'Shapefiles',
    'GET /v1/projects/:p/shapefiles/head': 'Shapefiles',
    'GET /v1/projects/:p/shapefiles/jobs/:p': 'Shapefiles',
    'GET /v1/shapefiles': 'Shapefiles',
    'GET /v1/shapefiles/:p': 'Shapefiles',
    'GET /v1/shapefiles/:p/features': 'Shapefiles',
    'GET /v1/shapefiles/head': 'Shapefiles',
    'GET /v1/shapefiles/jobs/:p': 'Shapefiles',
    'HEAD /v1/projects/:p/shapefiles': 'Shapefiles',
    'HEAD /v1/shapefiles': 'Shapefiles',
    'PATCH /v1/shapefiles': 'Shapefiles',
    'POST /v1/projects/:p/shapefiles': 'Shapefiles',
    'POST /v1/projects/:p/shapefiles/uploads': 'Shapefiles',
    'POST /v1/projects/:p/shapefiles/uploads/:p': 'Shapefiles',
    'POST /v1/shapefiles': 'Shapefiles',
    'POST /v1/shapefiles/uploads': 'Shapefiles',
    'POST /v1/shapefiles/uploads/:p': 'Shapefiles',
    'GET /v1/projects/:p/scenarios/:p/well-assignments/incrementals': 'Well incrementals',
    'DELETE /v1/projects/:p/type-curves': 'v1 type curves (retired)',
    'DELETE /v1/projects/:p/type-curves/lookup-tables/:p': 'v1 type curves (retired)',
    'GET /v1/projects/:p/type-curves': 'v1 type curves (retired)',
    'GET /v1/projects/:p/type-curves/:p': 'v1 type curves (retired)',
    'GET /v1/projects/:p/type-curves/:p/fits/daily': 'v1 type curves (retired)',
    'GET /v1/projects/:p/type-curves/:p/fits/monthly': 'v1 type curves (retired)',
    'GET /v1/projects/:p/type-curves/:p/representative-wells': 'v1 type curves (retired)',
    'GET /v1/projects/:p/type-curves/head': 'v1 type curves (retired)',
    'GET /v1/projects/:p/type-curves/lookup-tables': 'v1 type curves (retired)',
    'GET /v1/projects/:p/type-curves/lookup-tables/:p': 'v1 type curves (retired)',
    'GET /v1/projects/:p/type-curves/lookup-tables/head': 'v1 type curves (retired)',
    'HEAD /v1/projects/:p/type-curves': 'v1 type curves (retired)',
    'HEAD /v1/projects/:p/type-curves/lookup-tables': 'v1 type curves (retired)',
    'POST /v1/projects/:p/type-curves': 'v1 type curves (retired)',
    'POST /v1/projects/:p/type-curves/lookup-tables': 'v1 type curves (retired)',
    'PUT /v1/projects/:p/type-curves': 'v1 type curves (retired)',
    'PUT /v1/projects/:p/type-curves/lookup-tables': 'v1 type curves (retired)',
}


class _TooManyRequests(Exception):
    """Stops a method that keeps sending (a poll loop) once its routes are recorded."""


class _Recorder:
    """Stands in for `requests.request`: records (VERB, normalized path) and answers 200."""

    def __init__(self) -> None:
        self.operations: set[tuple[str, tuple[str, ...]]] = set()
        self.requests_in_call = 0

    def __call__(self, method: str, url: str, **keywords: Any) -> FakeResponse:
        self.requests_in_call += 1
        if self.requests_in_call > _MAX_REQUESTS_PER_CALL:
            raise _TooManyRequests
        self.operations.add((method.upper(), _normalize(urlsplit(url).path.strip('/').split('/'))))
        body: Any = [{'id': _PLACEHOLDER, 'status': 'completed', 'jobId': _PLACEHOLDER}]
        return FakeResponse(200, body, headers={'X-Query-Count': '1', 'X-Delete-Count': '1'})


def _normalize(path_segments: list[str]) -> tuple[str, ...]:
    """Collapse id segments (the placeholder, or the collection's `:name`) to `:p`."""
    return tuple(':p' if _ID_SEGMENT.match(str(segment)) else str(segment) for segment in path_segments)


def _label(verb: str, segments: tuple[str, ...]) -> str:
    return f'{verb} /' + '/'.join(segments)


def _reaches(template: tuple[str, tuple[str, ...]], sent: set[tuple[str, tuple[str, ...]]]) -> bool:
    """True when a sent request matches the template. A template `:p` matches any one segment,
    because the collection also writes literal-valued parameters (`:econName`, `:collection`)
    that way; a literal template segment must be sent as written."""
    verb, template_segments = template
    return any(
        sent_verb == verb
        and len(sent_segments) == len(template_segments)
        and all(expected in (':p', actual) for expected, actual in zip(template_segments, sent_segments))
        for sent_verb, sent_segments in sent
    )


def _collection_operations() -> set[tuple[str, tuple[str, ...]]]:
    """Every collection operation as (VERB, normalized path segments)."""
    response = requests.get(_COLLECTION_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
    response.raise_for_status()
    operations: set[tuple[str, tuple[str, ...]]] = set()

    def walk(items: list[dict[str, Any]]) -> None:
        for item in items:
            if 'item' in item:
                walk(item['item'])
                continue
            request = item.get('request') or {}
            segments = (request.get('url') or {}).get('path')
            if segments:
                operations.add((str(request.get('method', '')).upper(), _normalize(segments)))

    walk(response.json().get('item', []))
    return operations


def _placeholder_for(parameter: inspect.Parameter) -> Any:
    """A value of the parameter's annotated type; ids and names are all the 24-hex placeholder."""
    annotation = str(parameter.annotation)
    if 'ItemList' in annotation or annotation.startswith(('list[dict', 'list[Item')):
        return [{'id': _PLACEHOLDER}]
    if 'Item' in annotation or annotation.startswith(('dict', 'Mapping')):
        return {'id': _PLACEHOLDER}
    if any(form in annotation for form in ('Sequence[str]', 'list[str]', 'Iterable[str]')):
        return [_PLACEHOLDER]
    if annotation.startswith('int'):
        return 1
    if annotation.startswith('float'):
        return 1.0
    if annotation.startswith('bool'):
        return False
    return _PLACEHOLDER


def _call_every_public_method(api: ComboCurveAPI, recorder: _Recorder) -> list[str]:
    """Call each public method (a by-type method once per type); return the names that sent nothing."""
    silent: list[str] = []
    for name, function in inspect.getmembers(ComboCurveAPI, inspect.isfunction):
        if name.startswith('_') or name.endswith('_url'):
            continue
        parameters = list(inspect.signature(function).parameters.values())
        if parameters and parameters[0].name == 'self':
            parameters = parameters[1:]
        arguments = {
            parameter.name: _placeholder_for(parameter)
            for parameter in parameters
            if parameter.default is inspect.Parameter.empty
            and parameter.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        }
        arguments.update(_ARGUMENT_OVERRIDES.get(name, {}))
        variants = (
            [{**arguments, 'econ_model_type': econ_model_type} for econ_model_type in _ECON_MODEL_TYPES]
            if 'econ_model_type' in arguments
            else [arguments]
        )
        requests_sent = 0
        for variant in variants:
            recorder.requests_in_call = 0
            try:
                result = getattr(api, name)(**variant)
                if isinstance(result, Iterator):
                    # A generator method sends only when it is consumed.
                    for _ in result:
                        pass
            except Exception:
                # The response is a placeholder, so a method may fail after it sends; its routes
                # are already recorded. A type with no such route raises before it sends.
                pass
            requests_sent += min(recorder.requests_in_call, _MAX_REQUESTS_PER_CALL)
        if requests_sent == 0:
            silent.append(name)
    return silent


def test_every_published_route_has_a_method_or_a_reviewed_entry(monkeypatch: MonkeyPatch) -> None:
    try:
        collection = _collection_operations()
    except (requests.RequestException, ValueError) as exc:
        pytest.skip(f'ComboCurve Postman collection unreachable: {exc}')

    recorder = _Recorder()
    monkeypatch.setattr(requests, 'request', recorder)
    monkeypatch.setattr('time.sleep', lambda seconds: None)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        silent = _call_every_public_method(make_offline_api(), recorder)

    assert sorted(silent) == sorted(_SENDS_NOTHING_BY_DESIGN), (
        f'public methods that sent no request (give them _ARGUMENT_OVERRIDES): {sorted(silent)}'
    )
    unwrapped = {_label(*template) for template in collection if not _reaches(template, recorder.operations)}
    new_routes = sorted(unwrapped - set(_UNWRAPPED))
    now_wrapped = sorted(set(_UNWRAPPED) - unwrapped)
    assert not new_routes, (
        'collection routes that no method sends: wrap each one, or add it to _UNWRAPPED with its area:\n'
        + '\n'.join(new_routes)
    )
    assert not now_wrapped, 'routes in _UNWRAPPED that a method now sends (remove them):\n' + '\n'.join(now_wrapped)
