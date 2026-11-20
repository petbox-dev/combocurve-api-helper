"""The route manifest: every operation in the ComboCurve Postman collection, and what the helper does with it.

`tests/route_manifest.json` is the committed record, one entry per collection operation. Each entry has a
`status`:

- `wrapped`: a public method sends it. `method` names the first public method that does.
- `gap`: ComboCurve publishes it and no public method sends it. Known, not yet wrapped.
- `retired`: ComboCurve no longer serves it; the collection still documents it. Kept by hand, with `note`.
- `not-via-method`: the helper sends it outside any public method. Kept by hand, with `note`.

`scripts/generate_route_coverage.py` rewrites the file from the live collection and from a call-based
record of what each public method sends. It keeps `retired` and `not-via-method` as they are, marks a new
unreached route `gap`, and recomputes `wrapped`. `tests/test_published_routes_are_wrapped.py` fails when the
file is stale, or when a status disagrees with what the methods send.

A collection path parameter (`:name`) matches any one sent segment, because the collection also writes
literal-valued parameters that way (`:econName`, `:collection`). A template literal must be sent as written.
"""

from __future__ import annotations

import inspect
import json
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest import mock
from urllib.parse import urlsplit

import requests

from combocurve_api_helper import ComboCurveAPI
from tests.http_fakes import FakeResponse, make_offline_api
from tests.postman_collection import PLACEHOLDER, normalized_segments

ROUTE_MANIFEST_PATH = Path(__file__).with_name('route_manifest.json')

STATUSES = ('wrapped', 'gap', 'retired', 'not-via-method')
# Set by hand; the generator carries them over rather than recomputing them.
HAND_KEPT_STATUSES = ('retired', 'not-via-method')

# A method that polls would loop on the fake transport; this many requests from one call is enough
# to record its routes.
_MAX_REQUESTS_PER_CALL = 5

# Arguments that the annotation alone cannot fill: a value the method validates before it sends.
ARGUMENT_OVERRIDES: dict[str, dict[str, Any]] = {
    'delete_company_wells': {'well_id': PLACEHOLDER},
    'delete_project_company_wells': {'well_id': PLACEHOLDER},
    'delete_project_wells': {'well_id': PLACEHOLDER},
    'delete_scenarios': {'scenario_id': PLACEHOLDER},
    'delete_type_curves': {'id': PLACEHOLDER},
    'get_project_custom_columns': {'custom_column': 'wells'},
    'count_root_forecast_daily_volumes': {'filters': {'project': PLACEHOLDER}},
    'count_root_forecast_monthly_volumes': {'filters': {'project': PLACEHOLDER}},
    'get_root_forecast_daily_volumes': {'filters': {'project': PLACEHOLDER}},
    'get_root_forecast_monthly_volumes': {'filters': {'project': PLACEHOLDER}},
}
# A by-type method (`econ_model_type` argument) is called once per econ-model type, because it
# is the only method for some routes (the company POST/PUT/HEAD of most types).
ECON_MODEL_TYPES = sorted({str(entry['econModelType']) for entry in ComboCurveAPI.ECON_MODELS})

# Public methods that send no request: pure helpers.
SENDS_NOTHING_BY_DESIGN = ('extract_id', 'index_of')

# (VERB, normalized path segments), as `normalized_segments` returns them.
Template = tuple[str, tuple[str, ...]]


@dataclass(frozen=True)
class Route:
    """One collection operation and its status."""

    verb: str
    path: str  # '/v1/projects/:p/formations', ids as ':p'
    name: str  # the collection item name, the docstring slug
    area: str  # the collection folder the operation sits in
    status: str
    method: str | None = None
    note: str | None = None

    @property
    def key(self) -> tuple[str, str]:
        return (self.verb, self.path)

    def template(self) -> Template:
        return (self.verb, tuple(self.path.strip('/').split('/')))

    def to_json(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            'verb': self.verb,
            'path': self.path,
            'name': self.name,
            'area': self.area,
            'status': self.status,
        }
        if self.method is not None:
            record['method'] = self.method
        if self.note is not None:
            record['note'] = self.note
        return record

    @staticmethod
    def from_json(record: dict[str, Any]) -> Route:
        return Route(
            verb=str(record['verb']),
            path=str(record['path']),
            name=str(record['name']),
            area=str(record['area']),
            status=str(record['status']),
            method=record.get('method'),
            note=record.get('note'),
        )


class _TooManyRequests(Exception):
    """Stops a method that keeps sending (a poll loop) once its routes are recorded."""


class Recorder:
    """Stands in for `requests.request`: records (VERB, normalized path) and answers 200."""

    def __init__(self) -> None:
        # Every (VERB, normalized path) the method being called has sent so far.
        self.operations: set[Template] = set()
        # Requests sent since `begin_call`; caps a poll loop at `_MAX_REQUESTS_PER_CALL`.
        self.requests_in_call = 0

    def begin_call(self) -> None:
        self.requests_in_call = 0

    def __call__(self, method: str, url: str, **keywords: Any) -> FakeResponse:
        self.requests_in_call += 1
        if self.requests_in_call > _MAX_REQUESTS_PER_CALL:
            raise _TooManyRequests
        self.operations.add((method.upper(), normalized_segments(urlsplit(url).path.strip('/').split('/'))))
        body: Any = [{'id': PLACEHOLDER, 'status': 'completed', 'jobId': PLACEHOLDER}]
        return FakeResponse(200, body, headers={'X-Query-Count': '1', 'X-Delete-Count': '1'})


@contextmanager
def recording_requests() -> Iterator[Recorder]:
    """Route every request to a `Recorder` and make retry pauses instant, for the duration of the block."""
    recorder = Recorder()
    with mock.patch.object(requests, 'request', recorder), mock.patch('time.sleep', lambda seconds: None):
        yield recorder


def template_reached_by(template: Template, sent: set[Template]) -> bool:
    """True when a sent request matches the template. A template `:p` matches any one segment; a
    template literal must be sent as written."""
    verb, template_segments = template
    return any(
        sent_verb == verb
        and len(sent_segments) == len(template_segments)
        and all(expected in (':p', actual) for expected, actual in zip(template_segments, sent_segments))
        for sent_verb, sent_segments in sent
    )


def label(verb: str, segments: tuple[str, ...]) -> str:
    """'VERB /seg/seg', the form a route's `path` takes in the manifest."""
    return f'{verb} /' + '/'.join(segments)


def _placeholder_for(parameter: inspect.Parameter) -> Any:
    """A value of the parameter's annotated type; ids and names are all the 24-hex placeholder."""
    annotation = str(parameter.annotation)
    if 'ItemList' in annotation or annotation.startswith(('list[dict', 'list[Item')):
        return [{'id': PLACEHOLDER}]
    if 'Item' in annotation or annotation.startswith(('dict', 'Mapping')):
        return {'id': PLACEHOLDER}
    if any(form in annotation for form in ('Sequence[str]', 'list[str]', 'Iterable[str]')):
        return [PLACEHOLDER]
    if annotation.startswith('int'):
        return 1
    if annotation.startswith('float'):
        return 1.0
    if annotation.startswith('bool'):
        return False
    return PLACEHOLDER


def sent_by_method() -> tuple[dict[str, set[Template]], list[str]]:
    """Call each public method on a fake transport; return what each one sends, and the names that sent
    nothing. A method that raises after it sends keeps what it sent; a by-type method is called once per
    econ-model type."""
    api = make_offline_api()
    with recording_requests() as recorder:
        sent: dict[str, set[Template]] = {}
        silent: list[str] = []
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
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
                arguments.update(ARGUMENT_OVERRIDES.get(name, {}))
                variants = (
                    [{**arguments, 'econ_model_type': econ_model_type} for econ_model_type in ECON_MODEL_TYPES]
                    if 'econ_model_type' in arguments
                    else [arguments]
                )
                recorder.operations = set()
                for variant in variants:
                    recorder.begin_call()
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
                sent[name] = set(recorder.operations)
                if not recorder.operations:
                    silent.append(name)
    return sent, silent


def area_of(segments: tuple[str, ...]) -> str:
    """The resource a route is about: the first literal segment after `/v1` and any `projects/:p` scope.
    The collection's folder names are not used: they mix resources with ids (`{id}`) and sub-actions (`head`)."""
    rest = list(segments[1:]) if segments[:1] == ('v1',) else list(segments)
    if rest[:1] == ['projects'] and len(rest) >= 2:
        rest = rest[2:]
    literal = [segment for segment in rest if segment != ':p']
    return literal[0] if literal else 'projects'


def operations_from_collection(items: list[tuple[str, dict[str, Any]]]) -> list[tuple[str, str, str, tuple[str, ...]]]:
    """(name, area, VERB, normalized path segments) per collection operation, from (item name, request) rows.
    A request with no path is skipped."""
    operations: list[tuple[str, str, str, tuple[str, ...]]] = []
    for name, request in items:
        segments = (request.get('url') or {}).get('path')
        if segments:
            normalized = normalized_segments(segments)
            operations.append((name, area_of(normalized), str(request.get('method', '')).upper(), normalized))
    return operations


def load_manifest() -> list[Route]:
    """The committed manifest; empty when the file does not exist yet."""
    if not ROUTE_MANIFEST_PATH.exists():
        return []
    records = json.loads(ROUTE_MANIFEST_PATH.read_text(encoding='utf-8'))
    return [Route.from_json(record) for record in records['routes']]


def build_manifest(
    operations: list[tuple[str, str, str, tuple[str, ...]]],
    sent: dict[str, set[Template]],
    previous: list[Route],
) -> list[Route]:
    """One Route per collection operation, sorted by path then verb. A route that a method sends is
    `wrapped` (the first such method, by name); an unreached route keeps its hand-set status when it has
    one, else it is `gap`."""
    previous_by_key = {route.key: route for route in previous}
    routes: list[Route] = []
    for name, area, verb, segments in operations:
        template = (verb, segments)
        path = '/' + '/'.join(segments)
        reaching = sorted(
            method for method, operations_sent in sent.items() if template_reached_by(template, operations_sent)
        )
        earlier = previous_by_key.get((verb, path))
        if reaching:
            routes.append(Route(verb, path, name, area, 'wrapped', method=reaching[0]))
        elif earlier is not None and earlier.status in HAND_KEPT_STATUSES:
            routes.append(Route(verb, path, name, area, earlier.status, note=earlier.note))
        else:
            routes.append(Route(verb, path, name, area, 'gap'))
    return sorted(routes, key=lambda route: (route.path, route.verb))


def render_manifest(routes: list[Route], collection_url: str) -> str:
    """The manifest file's text: stable order, two-space indent, trailing newline."""
    document = {
        'collection': collection_url,
        'counts': {status: sum(1 for route in routes if route.status == status) for status in STATUSES},
        'routes': [route.to_json() for route in routes],
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + '\n'
