"""The route manifest: every operation in the ComboCurve Postman collection, and what the helper does with it.

`tests/route_manifest.json` is the committed record, one entry per collection operation. Each entry has a
`status`:

- `wrapped`: a public method sends it. `method` names the first such method, by name (see `routes_reached`).
- `gap`: ComboCurve publishes it and no public method sends it. Known, not yet wrapped.
- `retired`: ComboCurve no longer serves it; the collection still documents it. Kept by hand, with `note`.
- `not-via-method`: the helper sends it outside any public method. Kept by hand, with `note`.

`scripts/generate_route_coverage.py` rewrites the file from the live collection and from a call-based
record of what each public method sends. It keeps `retired` and `not-via-method` as they are, marks a new
unreached route `gap`, and recomputes `wrapped`. `tests/test_published_routes_are_wrapped.py` fails when the
file is stale, or when a status disagrees with what the methods send.

How a sent request is matched to a collection template (`match_score`, `routes_reached`):

- A collection parameter named `id` or `...Id` (`:projectId`, `:econModelId`) holds an id. The manifest
  writes it `:p`, and it matches only a sent id (the placeholder), never a sent literal.
- Any other collection parameter (`:econName`, `:collection`, `:customColumn`, `:phase`, `:series`) holds a
  literal value. The manifest keeps its name, and it matches any one sent segment.
- A template literal must be sent as written.
- A sent request counts only toward the matching templates with the most literal segments: a request to
  `.../one-liners/combo-names` reaches that route and not `.../one-liners/:p`, even where the parameter
  there is literal-valued.
"""

from __future__ import annotations

import collections.abc
import functools
import inspect
import io
import json
import sys
import types
import typing
import warnings
import zipfile
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union
from unittest import mock
from urllib.parse import urlsplit

import requests

from combocurve_api_helper import ComboCurveAPI, base
from tests.http_fakes import FakeResponse, make_offline_api
from tests.postman_collection import PLACEHOLDER, Operation, _operations_in, normalized_segments

ROUTE_MANIFEST_PATH = Path(__file__).with_name('route_manifest.json')

STATUSES = ('wrapped', 'gap', 'retired', 'not-via-method')
# Set by hand; the generator carries them over rather than recomputing them.
HAND_KEPT_STATUSES = ('retired', 'not-via-method')

# The manifest's spelling of an id-valued path parameter.
ID_PARAMETER = ':p'

# A method that polls would loop on the fake transport; this many requests from one call is enough
# to record its routes. A call that reaches the cap is reported (`MethodCalls.capped`), because a
# route it would send from a later request is not recorded.
_MAX_REQUESTS_PER_CALL = 5


def _placeholder_shapefile_zip() -> bytes:
    """A zip holding empty `layer.shp`, `.shx` and `.dbf`: the member set the shapefile upload checks."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for suffix in ('shp', 'shx', 'dbf'):
            archive.writestr(f'layer.{suffix}', b'')
    return buffer.getvalue()


_SHAPEFILE_ZIP = _placeholder_shapefile_zip()

# Arguments that the annotation alone cannot fill: a value the method validates before it sends.
ARGUMENT_OVERRIDES: dict[str, dict[str, Any]] = {
    'delete_company_wells': {'well_id': PLACEHOLDER},
    'delete_project_company_wells': {'well_id': PLACEHOLDER},
    'delete_project_wells': {'well_id': PLACEHOLDER},
    'delete_scenarios': {'scenario_id': PLACEHOLDER},
    'delete_scenario_model_assignments': {'data': [{'id': PLACEHOLDER, 'allWells': True}]},
    'delete_scenario_econ_model_assignments': {'data': [{'id': PLACEHOLDER, 'allWells': True}]},
    'delete_type_curves': {'id': PLACEHOLDER},
    'get_project_custom_columns': {'custom_column': 'wells'},
    'count_root_forecast_daily_volumes': {'filters': {'project': PLACEHOLDER}},
    'count_root_forecast_monthly_volumes': {'filters': {'project': PLACEHOLDER}},
    'get_root_forecast_daily_volumes': {'filters': {'project': PLACEHOLDER}},
    'get_root_forecast_monthly_volumes': {'filters': {'project': PLACEHOLDER}},
    'put_shapefile_upload_file': {
        'upload': {'uploadUrl': 'https://storage.example.invalid/upload.zip'},
        'zip_file': _SHAPEFILE_ZIP,
    },
    'delete_company_production_comments': {'production_comment_id': PLACEHOLDER},
    'delete_project_production_comments': {'production_comment_id': PLACEHOLDER},
    'upload_company_shapefile': {'zip_file': _SHAPEFILE_ZIP},
    'upload_project_shapefile': {'zip_file': _SHAPEFILE_ZIP},
}
# A by-type method (`econ_model_type` argument) is called once per econ-model type, because it
# is the only method for some routes (the company POST/PUT/HEAD of most types).
ECON_MODEL_TYPES = sorted({str(entry['econModelType']) for entry in ComboCurveAPI.ECON_MODELS})

# Public methods that send no request: pure helpers.
SENDS_NOTHING_BY_DESIGN = ('extract_id', 'index_of')

# Every (method, exception type) that `sent_by_method` sees, reviewed. A pair not listed here, or a
# listed pair that no longer occurs, fails `tests/test_route_manifest_tooling.py`: a method that crashes
# on the fake transport may stop before it sends a route, and that route would then read `gap` or
# credit another method without anyone noticing.
EXPECTED_EXCEPTIONS: frozenset[tuple[str, str]] = frozenset(
    {
        # The placeholder body is a list of objects; these post-process it as strings (combo names)
        # or read `results` from it. Each fails after its last request, so no route is lost.
        ('get_econ_run_by_id', 'TypeError'),
        ('get_econ_run_combo_names', 'TypeError'),
        ('get_econ_runs', 'TypeError'),
        ('update_econ_run_combo_names', 'TypeError'),
        ('get_econ_run_monthly_export', 'KeyError'),
        ('get_stream_econ_run_monthly_export', 'KeyError'),
        # By-type methods refuse, before they send, a type they have no route for: AssertionError for
        # an `ECON_MODELS` type that is not an econ model (Forecast, Network, PSeries, Schedule);
        # ValueError on a company route for a type with no company route (Emission, FluidModel).
        ('count_company_econ_models_by_type', 'AssertionError'),
        ('count_company_econ_models_by_type', 'ValueError'),
        ('count_econ_model_assignments_by_type_by_id', 'AssertionError'),
        ('count_econ_models_by_type', 'AssertionError'),
        ('delete_company_econ_model_by_type_by_id', 'AssertionError'),
        ('delete_company_econ_model_by_type_by_id', 'ValueError'),
        ('delete_econ_model_assignments_by_type_by_id', 'AssertionError'),
        ('delete_econ_model_by_type_by_id', 'AssertionError'),
        ('get_company_econ_model_by_type_by_id', 'AssertionError'),
        ('get_company_econ_model_by_type_by_id', 'ValueError'),
        ('get_company_econ_models_by_type', 'AssertionError'),
        ('get_company_econ_models_by_type', 'ValueError'),
        ('get_econ_model_assignments_by_type_by_id', 'AssertionError'),
        ('get_econ_model_by_type_by_id', 'AssertionError'),
        ('get_econ_models_by_type', 'AssertionError'),
        ('post_company_econ_models_by_type', 'AssertionError'),
        ('post_company_econ_models_by_type', 'ValueError'),
        ('post_econ_model_assignments_by_type_by_id', 'AssertionError'),
        ('post_econ_models_by_type', 'AssertionError'),
        ('put_company_econ_models_by_type', 'AssertionError'),
        ('put_company_econ_models_by_type', 'ValueError'),
        ('put_econ_model_assignments_by_type_by_id', 'AssertionError'),
        ('put_econ_models_by_type', 'AssertionError'),
        # The upload flow reads `uploadUrl` from the step-1 ticket; the placeholder body has none, so it
        # stops with ValueError after step 1 has sent its route.
        ('upload_company_shapefile', 'ValueError'),
        ('upload_project_shapefile', 'ValueError'),
    }
)

# Public methods expected to reach `_MAX_REQUESTS_PER_CALL` (a poll loop). Any other method that reaches
# it fails the tooling test: raise the cap, or give it an argument that ends the loop.
EXPECTED_CAPPED: frozenset[str] = frozenset()

# (VERB, path segments). For a collection template: id parameters as `:p`, literal-valued parameters as
# `:name`. For a sent request: as `normalized_segments` returns them (the placeholder id as `:p`).
Template = tuple[str, tuple[str, ...]]


@dataclass(frozen=True)
class Route:
    """One collection operation and its status."""

    verb: str
    path: str  # '/v1/projects/:p/econ-models/:econName/:p/assignments': ids as ':p', see `template_segments`
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


def is_id_parameter(name: str) -> bool:
    """True for a collection path parameter that holds an id: `id`, or a name ending in `Id`."""
    return name == 'id' or name.endswith('Id')


def template_segments(raw_segments: Iterable[Any]) -> tuple[str, ...]:
    """A collection path as the manifest writes it: an id parameter (`:projectId`) as `:p`, a
    literal-valued parameter (`:econName`) kept by name, a literal as written."""
    segments: list[str] = []
    for raw_segment in raw_segments:
        segment = str(raw_segment)
        if segment.startswith(':') and is_id_parameter(segment[1:]):
            segments.append(ID_PARAMETER)
        else:
            segments.append(segment)
    return tuple(segments)


def match_score(template_segments_: tuple[str, ...], sent_segments: tuple[str, ...]) -> int | None:
    """How specifically one sent path matches one template path: the number of template literals it
    matches, or None for no match. `:p` matches only a sent id; another `:name` matches any one sent
    segment; a literal must be sent as written.

    Because `:p` never matches a sent literal, every request that reaches a template matches it the same
    way, and no tie-break between methods is needed beyond the name."""
    if len(template_segments_) != len(sent_segments):
        return None
    literals = 0
    for expected, actual in zip(template_segments_, sent_segments):
        if expected == ID_PARAMETER:
            if actual != ID_PARAMETER:
                return None
        elif expected.startswith(':'):
            continue
        elif expected == actual:
            literals += 1
        else:
            return None
    return literals


def routes_reached(templates: Iterable[Template], sent: Mapping[str, set[Template]]) -> dict[Template, list[str]]:
    """Template -> the methods that reach it, by name. A sent request counts only toward the matching
    templates with the most literal segments, so a request to a literal route (`.../combo-names`) never
    also reaches a sibling with a literal-valued parameter in that place."""
    templates_by_shape: dict[tuple[str, int], list[Template]] = {}
    for template in templates:
        templates_by_shape.setdefault((template[0], len(template[1])), []).append(template)
    reached: dict[Template, set[str]] = {}
    for method, requests_sent in sent.items():
        for verb, segments in requests_sent:
            candidates: list[tuple[int, Template]] = []
            for template in templates_by_shape.get((verb, len(segments)), []):
                literals = match_score(template[1], segments)
                if literals is not None:
                    candidates.append((literals, template))
            if not candidates:
                continue
            most_literals = max(literals for literals, _ in candidates)
            for literals, template in candidates:
                if literals == most_literals:
                    reached.setdefault(template, set()).add(method)
    return {template: sorted(methods) for template, methods in reached.items()}


def label(verb: str, segments: tuple[str, ...]) -> str:
    """'VERB /seg/seg', the form a route's `path` takes in the manifest."""
    return f'{verb} /' + '/'.join(segments)


# Names an annotation string may use without the defining module importing them at run time (they sit
# under `if TYPE_CHECKING:` there). The module's own globals take precedence.
_ANNOTATION_NAMESPACE: dict[str, Any] = {
    **{name: getattr(typing, name) for name in typing.__all__},
    **{name: getattr(collections.abc, name) for name in collections.abc.__all__},
    **{name: value for name, value in vars(base).items() if not name.startswith('__')},
}
_UNION_TYPES: tuple[Any, ...] = (Union, getattr(types, 'UnionType', Union))


def _resolved_annotation(function: Any, parameter: inspect.Parameter) -> Any:
    """The parameter's annotation as a type, or None when it cannot be evaluated. Evaluated one
    parameter at a time: `typing.get_type_hints` fails for the whole function when any annotation (often
    the return) names a type imported only under `TYPE_CHECKING`."""
    annotation = parameter.annotation
    if not isinstance(annotation, str):
        return annotation
    module = sys.modules.get(function.__module__)
    namespace = {**_ANNOTATION_NAMESPACE, **(vars(module) if module is not None else {})}
    try:
        # The text is an annotation from this package's own source, not outside input.
        return eval(annotation, namespace)
    except Exception:
        return None


def _placeholder_for_type(hint: Any) -> Any:
    """A value of the type `hint`: the first arm of a union, the first value of a `Literal`, a one-element
    list of a sequence, `{'id': placeholder}` for a mapping, and the placeholder for a string or anything
    else."""
    origin = typing.get_origin(hint)
    arguments = typing.get_args(hint)
    if origin in _UNION_TYPES:
        arms = [arm for arm in arguments if arm is not type(None)]
        return _placeholder_for_type(arms[0]) if arms else None
    if origin is typing.Literal:
        return arguments[0]
    if hint is bool:
        return False
    if hint is int:
        return 1
    if hint is float:
        return 1.0
    if hint is dict or origin in (dict, collections.abc.Mapping, collections.abc.MutableMapping):
        return {'id': PLACEHOLDER}
    if origin in (
        list,
        tuple,
        set,
        frozenset,
        collections.abc.Sequence,
        collections.abc.Iterable,
        collections.abc.Collection,
    ):
        return [_placeholder_for_type(arguments[0]) if arguments else PLACEHOLDER]
    return PLACEHOLDER


def _placeholder_for_annotation_text(annotation: str) -> Any:
    """The fallback for an annotation that cannot be evaluated: match its text. It reads only the outer
    form, so a nested or unusual annotation (an alias it does not know) gets the placeholder string."""
    if annotation.startswith(('ItemList', 'list[dict', 'list[Item', 'Sequence[Item', 'Sequence[dict')):
        return [{'id': PLACEHOLDER}]
    if annotation.startswith(('Sequence[str]', 'list[str]', 'Iterable[str]')):
        return [PLACEHOLDER]
    if annotation.startswith(('Item', 'dict', 'Mapping')):
        return {'id': PLACEHOLDER}
    if annotation.startswith('int'):
        return 1
    if annotation.startswith('float'):
        return 1.0
    if annotation.startswith('bool'):
        return False
    return PLACEHOLDER


def _placeholder_for(function: Any, parameter: inspect.Parameter) -> Any:
    """A value of the parameter's annotated type; ids and names are all the 24-hex placeholder."""
    hint = _resolved_annotation(function, parameter)
    if hint is not None and hint is not inspect.Parameter.empty:
        return _placeholder_for_type(hint)
    return _placeholder_for_annotation_text(str(parameter.annotation))


@dataclass
class MethodCalls:
    """What calling every public method on the fake transport recorded."""

    # method -> every (VERB, normalized path) it sent
    sent: dict[str, set[Template]] = field(default_factory=dict)
    # methods that sent nothing
    silent: list[str] = field(default_factory=list)
    # (method, exception type name) for every call that raised, the poll-loop stop excepted
    exceptions: set[tuple[str, str]] = field(default_factory=set)
    # methods with a call that reached `_MAX_REQUESTS_PER_CALL`
    capped: set[str] = field(default_factory=set)


def public_method_names() -> list[str]:
    """Every public `ComboCurveAPI` method, by name; `*_url` builders excluded."""
    return [
        name
        for name, _ in inspect.getmembers(ComboCurveAPI, inspect.isfunction)
        if not name.startswith('_') and not name.endswith('_url')
    ]


def _call_arguments(name: str, function: Any) -> list[dict[str, Any]]:
    """The keyword arguments for each call of one method: one call, or one per econ-model type."""
    parameters = list(inspect.signature(function).parameters.values())
    if parameters and parameters[0].name == 'self':
        parameters = parameters[1:]
    arguments = {
        parameter.name: _placeholder_for(function, parameter)
        for parameter in parameters
        if parameter.default is inspect.Parameter.empty
        and parameter.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }
    arguments.update(ARGUMENT_OVERRIDES.get(name, {}))
    if 'econ_model_type' in arguments:
        return [{**arguments, 'econ_model_type': econ_model_type} for econ_model_type in ECON_MODEL_TYPES]
    return [arguments]


@functools.lru_cache(maxsize=1)
def sent_by_method() -> MethodCalls:
    """Call each public method on a fake transport; record what each one sends, which send nothing, which
    raise (and what), and which reach the request cap. A method that raises after it sends keeps what it
    sent; a by-type method is called once per econ-model type. Cached: the calls do not depend on the
    collection, and the tests ask for them more than once."""
    api = make_offline_api()
    calls = MethodCalls()
    with recording_requests() as recorder, warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for name in public_method_names():
            function = getattr(ComboCurveAPI, name)
            recorder.operations = set()
            for arguments in _call_arguments(name, function):
                recorder.begin_call()
                try:
                    result = getattr(api, name)(**arguments)
                    if isinstance(result, Iterator):
                        # A generator method sends only when it is consumed.
                        for _ in result:
                            pass
                except _TooManyRequests:
                    calls.capped.add(name)
                except Exception as error:
                    # The response is a placeholder, so a method may fail after it sends; its routes
                    # are already recorded. `EXPECTED_EXCEPTIONS` lists every failure reviewed.
                    calls.exceptions.add((name, type(error).__name__))
            calls.sent[name] = set(recorder.operations)
            if not recorder.operations:
                calls.silent.append(name)
    return calls


def area_of(segments: tuple[str, ...]) -> str:
    """The resource a route is about: the first literal segment after `/v1` and any `projects/:p` scope.
    The collection's folder names are not used: they mix resources with ids (`{id}`) and sub-actions (`head`)."""
    rest = list(segments[1:]) if segments[:1] == ('v1',) else list(segments)
    if rest[:1] == ['projects'] and len(rest) >= 2:
        rest = rest[2:]
    literal = [segment for segment in rest if not segment.startswith(':')]
    return literal[0] if literal else 'projects'


def collection_operations(payload: Mapping[str, Any]) -> list[Operation]:
    """(item name, request) for every operation of a collection document; empty when it has no `item` list."""
    items = payload.get('item')
    return _operations_in(items) if isinstance(items, list) else []


def operations_from_collection(items: list[Operation]) -> list[tuple[str, str, str, tuple[str, ...]]]:
    """(name, area, VERB, template path segments) per collection operation, from (item name, request) rows.
    A request with no path is skipped."""
    operations: list[tuple[str, str, str, tuple[str, ...]]] = []
    for name, request in items:
        raw_segments = (request.get('url') or {}).get('path')
        if raw_segments:
            segments = template_segments(raw_segments)
            operations.append((name, area_of(segments), str(request.get('method', '')).upper(), segments))
    return operations


def load_manifest() -> list[Route]:
    """The committed manifest; empty when the file does not exist yet."""
    if not ROUTE_MANIFEST_PATH.exists():
        return []
    records = json.loads(ROUTE_MANIFEST_PATH.read_text(encoding='utf-8'))
    return [Route.from_json(record) for record in records['routes']]


def _key_with_every_parameter_as_id(verb: str, path: str) -> tuple[str, str]:
    """(VERB, path) with every `:name` written `:p`: finds a hand-kept entry written before literal-valued
    parameters kept their names."""
    return (verb, '/'.join(ID_PARAMETER if segment.startswith(':') else segment for segment in path.split('/')))


def build_manifest(
    operations: list[tuple[str, str, str, tuple[str, ...]]],
    sent: Mapping[str, set[Template]],
    previous: list[Route],
) -> list[Route]:
    """One Route per collection operation, sorted by path then verb. A route that a method sends is
    `wrapped` (the first method `routes_reached` lists); an unreached route keeps its hand-set status
    when it has one, else it is `gap`."""
    previous_by_key = {_key_with_every_parameter_as_id(*route.key): route for route in previous}
    reached = routes_reached(((verb, segments) for _, _, verb, segments in operations), sent)
    routes: list[Route] = []
    for name, area, verb, segments in operations:
        path = '/' + '/'.join(segments)
        reaching = reached.get((verb, segments), [])
        earlier = previous_by_key.get(_key_with_every_parameter_as_id(verb, path))
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
