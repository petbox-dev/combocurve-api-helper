"""Refresh docstring example blocks from the ComboCurve Postman collection.

Each method docstring links to https://docs.api.combocurve.com/api/<slug>, where
<slug> is the collection item name. This tool fetches the collection and, for
every method (and the shared module-level `*_response`/`*_data` constants
appended via `__doc__ +=`), rewrites the `Example response:` block from that
operation's saved 2xx response and the `Example data:` / `Example request:` block
from its request body.

The collection carries every operation (it is a superset of the OpenAPI spec),
but its example values are `<type>` placeholders. We fill those with realistic,
deterministic spoof values (numbers as numbers, bools as bools, dates as ISO
strings, ids as ObjectId-like) so the docstring shows the response's key/value
shape without a live API call. Descriptions are untouched -- only the JSON under
an example marker is replaced.

Literal (non-`<type>`) strings in the collection are enum picks or random faker
values (ObjectId-like ids, garbage dates, sentences), and the collection re-draws
them on every publish. A block that differs from the collection only in those
picks is left as committed (see `EnumLiteral`), so --check reports a block stale
only when its shape, keys or placeholder values change.

Usage:
    python scripts/generate_docstrings.py             # rewrite in place
    python scripts/generate_docstrings.py --check      # exit 1 if stale (no write)
    python scripts/generate_docstrings.py --collection PATH  # local collection JSON
"""

from __future__ import annotations

import argparse
import ast
import http.client
import json
import pathlib
import re
import sys
import urllib.request
from typing import Any, Literal, NamedTuple

COLLECTION_URL = 'https://docs.api.combocurve.com/downloads/combocurve-api.postman_collection.json'
SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / 'src' / 'combocurve_api_helper'
URL_RE = re.compile(r'https://docs\.api\.combocurve\.com/api/([a-z0-9-]+)')
TOKEN_RE = re.compile(r'<(\w+)>')

# Which of an operation's two saved bodies a given docstring marker renders.
ExampleKind = Literal['response', 'request']

# Docstring marker line -> the saved body that replaces the JSON beneath it.
MARKERS: dict[str, ExampleKind] = {
    'Example response:': 'response',
    'Example data:': 'request',
    'Example request:': 'request',
}
# Success codes to prefer for the "Example response:" body (POST creates return 207).
_RESPONSE_CODES = (200, 201, 202, 207)


class CollectionExample(NamedTuple):
    """The saved bodies for one collection operation, placeholders already filled."""

    response: Any  # parsed 2xx response body; None when the operation saved none
    request: Any  # parsed request body; None when the operation has no raw body

    def body_for(self, kind: ExampleKind) -> Any:
        """The body a marker of `kind` renders, or None when this operation has none.

        A closed lookup, not `response if kind == 'response' else request`: the
        `Literal` is erased at runtime, so the conditional form would fail OPEN and
        silently render the request body under any future marker kind added to
        `MARKERS`. This raises KeyError instead.
        """
        return {'response': self.response, 'request': self.request}[kind]


class LineReplacement(NamedTuple):
    """A rendered JSON block and the inclusive line span it replaces."""

    start: int
    end: int
    lines: list[str]


class RewriteOutcome(NamedTuple):
    """What `rewrite_file` found for one module (and applied, unless only checking)."""

    changed: bool  # at least one example block differs from the collection
    replaced: int  # marker blocks matched to a collection example
    unsourced: list[str]  # markers with no collection example, left untouched


def spoof(token: str, key: str) -> str | int | float | bool:
    """A realistic, deterministic value for a Postman `<token>` placeholder."""
    if token == 'number':
        return 123.45
    if token == 'integer':
        return 123
    if token == 'boolean':
        return True
    if token == 'date':
        return '2020-01-01'
    if token == 'dateTime':
        return '2020-01-01T00:00:00.000Z'
    if token == 'uri':
        return 'https://example.com'
    # token == 'string' (plus any unknown token): light field-name realism.
    if key == 'id' or key.endswith('Id'):
        return '5e272d38b78910dd2a1bd691'  # ObjectId-like
    if key == 'name':
        return 'Example'
    return 'string'


class EnumLiteral(str):
    """A literal (non-`<type>`) string from the collection: an enum pick or a faker value.

    The collection's generator re-draws these on every publish: a random member of
    each enum (`exportType` was `monthlyProductionVolumeExport`, `econMonthlyExport`,
    then `monthlyCombinedVolumeExport` across three publishes) and random faker
    values (ObjectId-like ids, garbage dates such as `01/0363`, sentences). Marking
    these positions lets the comparison ignore the draw, so a republish that changes
    only them does not make the docstrings stale. `json.dumps` renders it as a plain
    string.
    """


def _enum_masked(value: Any) -> str:
    """`value` rendered with every `EnumLiteral` replaced by one fixed sentinel."""

    def mask(nested: Any) -> Any:
        if isinstance(nested, EnumLiteral):
            return '<enum>'
        if isinstance(nested, dict):
            return {nested_key: mask(item) for nested_key, item in nested.items()}
        if isinstance(nested, list):
            return [mask(item) for item in nested]
        return nested

    return json.dumps(mask(value), sort_keys=True, default=str)


def fill(value: Any, key: str = '') -> Any:
    """Recursively replace `<type>` placeholder strings with spoof values, mark
    literal strings as `EnumLiteral`, and collapse arrays whose elements are all
    identical apart from enum picks (Postman doubles examples, and a random pick
    per element would otherwise defeat the collapse).

    Typed `Any` in/out: the input is an arbitrary `json.loads` result and the
    output mirrors its shape, so no narrower annotation is honest here."""
    if isinstance(value, dict):
        return {nested_key: fill(nested, nested_key) for nested_key, nested in value.items()}
    if isinstance(value, list):
        elements = [fill(element, key) for element in value]
        if len(elements) > 1:
            first_rendered = _enum_masked(elements[0])
            if all(_enum_masked(other) == first_rendered for other in elements[1:]):
                return [elements[0]]
        return elements
    if isinstance(value, str):
        token_match = TOKEN_RE.fullmatch(value)
        return spoof(token_match.group(1), key) if token_match else EnumLiteral(value)
    return value


def matches_ignoring_enums(existing: Any, body: Any) -> bool:
    """True when `existing` (a parsed docstring block) equals `body` (a filled
    collection example) everywhere except `EnumLiteral` positions, where any string
    is accepted. Key order and array length must match; scalar types must match
    exactly (so `True` never equals `1`)."""
    if isinstance(body, EnumLiteral):
        return isinstance(existing, str)
    if isinstance(body, dict):
        return (
            isinstance(existing, dict)
            and list(existing) == list(body)
            and all(matches_ignoring_enums(existing[nested_key], body[nested_key]) for nested_key in body)
        )
    if isinstance(body, list):
        return (
            isinstance(existing, list)
            and len(existing) == len(body)
            and all(matches_ignoring_enums(old, new) for old, new in zip(existing, body))
        )
    return type(existing) is type(body) and existing == body


class CollectionUnavailable(Exception):
    """The collection could not be obtained in usable form.

    Covers transport failures (offline, DNS, TLS, truncated read) AND a completed
    fetch whose body is not a usable collection. Both mean "no verdict available",
    which must not be confused with "the docstrings are stale".
    """


def load_collection(source: str) -> dict[str, Any]:
    """Parse the Postman collection from a URL or a local path.

    Raises `CollectionUnavailable` only for the URL branch (mapped to exit 2, "offline
    / no verdict"). A bad local path is a real error, not "offline": a missing file
    surfaces as the underlying OSError and a wrong-shape file as a ValueError, both of
    which reach exit 1 rather than the exit-2 skip -- so a `--collection` typo is never
    mistaken for an unreachable network.
    """
    if source.startswith(('http://', 'https://')):
        request = urllib.request.Request(source, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            raw_bytes = urllib.request.urlopen(request).read()
        except (OSError, http.client.HTTPException) as exc:
            # OSError covers urllib.error.URLError, ssl.SSLError (e.g. a malformed cert
            # in the Windows store breaking load_default_certs), timeouts and resets.
            # http.client.HTTPException does NOT derive from OSError and must be named
            # separately -- a Content-Length-framed response cut short raises
            # IncompleteRead here, and this endpoint serves Content-Length.
            # Scoped to the network branch so a bad --collection PATH still raises.
            raise CollectionUnavailable(str(exc)) from exc
        try:
            fetched = json.loads(raw_bytes)
        except ValueError as exc:
            # A captive-portal or error HTML page parses as garbage. Still a failure to
            # FETCH, so it must reach the same exit code as a dead socket -- otherwise
            # the freshness test reads the traceback's exit 1 as "docstrings are stale".
            raise CollectionUnavailable(f'malformed collection JSON: {exc}') from exc
        if not isinstance(fetched, dict):
            # Valid JSON, wrong shape (an error envelope, a bare list, `null`). Reaching
            # build_examples would raise AttributeError -> exit 1 -> a false "stale".
            raise CollectionUnavailable(f'collection JSON is {type(fetched).__name__}, expected an object')
        if not isinstance(fetched.get('item'), list):
            # A well-formed JSON object with no operation tree yields zero examples, so
            # every marker looks "unsourced" and --check exits 0 -- the test would pass
            # having verified nothing. Fail loudly as unavailable instead.
            raise CollectionUnavailable('collection JSON has no top-level `item` list')
        collection_from_url: dict[str, Any] = fetched
        return collection_from_url

    # Local path: a typo, malformed file, or valid-JSON-but-wrong-shape file is a real
    # error, not "offline". The shape check mirrors the URL branch, but raises ValueError
    # (NOT CollectionUnavailable) so it reaches exit 1, never the exit-2 offline skip --
    # otherwise a structurally invalid local file would yield zero examples and --check
    # would exit 0, a false "fresh".
    fetched = json.loads(pathlib.Path(source).read_bytes())
    if not isinstance(fetched, dict) or not isinstance(fetched.get('item'), list):
        raise ValueError(f'--collection {source} is not a Postman collection (no top-level `item` list)')
    collection: dict[str, Any] = fetched
    return collection


def build_examples(collection: dict[str, Any]) -> dict[str, CollectionExample]:
    """Map each operation's collection item name to its filled example bodies."""
    examples: dict[str, CollectionExample] = {}

    def walk(items: list[dict[str, Any]]) -> None:
        """Recurse the collection's folder tree, collecting every operation leaf."""
        for item in items:
            if 'item' in item:
                walk(item['item'])
            elif 'request' in item:
                name = item.get('name')
                if not isinstance(name, str):
                    continue  # unnamed operation: nothing for a docstring slug to match on
                saved_by_code = {
                    saved.get('code'): saved
                    for saved in (item.get('response') or [])
                    if (saved.get('body') or '').strip()
                }
                chosen = next((saved_by_code[code] for code in _RESPONSE_CODES if code in saved_by_code), None)
                if chosen is None and saved_by_code:
                    chosen = next(iter(saved_by_code.values()))
                response = None
                if chosen is not None:
                    try:
                        response = fill(json.loads(chosen['body']))
                    except (ValueError, TypeError):
                        response = None
                raw_request_body = (item['request'].get('body') or {}).get('raw')
                request = None
                if raw_request_body and raw_request_body.strip():
                    try:
                        request = fill(json.loads(raw_request_body))
                    except (ValueError, TypeError):
                        request = None
                examples[name] = CollectionExample(response=response, request=request)

    walk(collection.get('item', []))
    return examples


def json_span(lines: list[str], marker_index: int, end_line: int) -> tuple[int, int] | None:
    """(start, end) inclusive line indices of the JSON block after a marker,
    bounded by `end_line`. Bracket-matched with string awareness; None if not found."""
    start = None
    for line_index in range(marker_index + 1, end_line):
        stripped = lines[line_index].strip()
        if not stripped:
            continue
        start = line_index if stripped[0] in '[{' else None
        break
    if start is None:
        return None
    depth = 0
    in_string = False
    escaped = False
    entered = False
    for line_index in range(start, end_line):
        for character in lines[line_index]:
            if in_string:
                if escaped:
                    escaped = False
                elif character == '\\':
                    escaped = True
                elif character == '"':
                    in_string = False
            elif character == '"':
                in_string = True
            elif character in '[{':
                depth += 1
                entered = True
            elif character in ']}':
                depth -= 1
        if entered and depth == 0:
            return (start, line_index)
    return None


def collect_targets(tree: ast.Module) -> list[tuple[ast.stmt, str]]:
    """[(node, item-name)] for example-bearing nodes: method docstrings (name from
    their /api/<slug> link) and module-level example constants appended to a method
    via `Klass.method.__doc__ += const` (keyed to the first such method)."""
    name_to_slug: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node, clean=False)
            if docstring:
                slug_match = URL_RE.search(docstring)
                if slug_match:
                    name_to_slug[node.name] = slug_match.group(1)
    const_to_method: dict[str, str] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.Add):
            aug_target = stmt.target
            if (
                isinstance(aug_target, ast.Attribute)
                and aug_target.attr == '__doc__'
                and isinstance(aug_target.value, ast.Attribute)
                and isinstance(stmt.value, ast.Name)
            ):
                const_to_method.setdefault(stmt.value.id, aug_target.value.attr)

    targets: list[tuple[ast.stmt, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in name_to_slug:
            targets.append((node, name_to_slug[node.name]))
        elif isinstance(node, ast.Assign):
            for assign_target in node.targets:
                if isinstance(assign_target, ast.Name) and assign_target.id in const_to_method:
                    slug = name_to_slug.get(const_to_method[assign_target.id])
                    if slug:
                        targets.append((node, slug))
    return targets


def render_block(body: Any, indent: str) -> list[str]:
    """The docstring lines for one example body, indented under its marker."""
    return [indent + line for line in json.dumps(body, indent=4, default=str).split('\n')]


def _keeps_existing_block(existing_lines: list[str], body: Any, indent: str) -> bool:
    """True when the committed block differs from `body` only in enum picks.

    The committed block must also be exactly what this generator renders for its
    own parsed value, so a hand edit (re-indented, reordered, reformatted) is still
    reported stale and rewritten.
    """
    try:
        existing = json.loads('\n'.join(existing_lines))
    except ValueError:
        return False
    return matches_ignoring_enums(existing, body) and render_block(existing, indent) == existing_lines


def plan_replacements(
    source_text: str, examples: dict[str, CollectionExample]
) -> tuple[list[LineReplacement], list[str]]:
    """Work out which example blocks in one module would be rewritten.

    Pure -- no reads, no writes -- so the matching rules stay testable apart from
    the file handling in `rewrite_file`. Returns the replacements in discovery
    order plus a label for every marker that had no collection example.
    """
    lines = source_text.split('\n')
    replacements: list[LineReplacement] = []
    unsourced: list[str] = []
    for node, slug in collect_targets(ast.parse(source_text)):
        example = examples.get(slug)
        label: str = getattr(node, 'name', None) or slug
        first_line, end_line = node.lineno - 1, (node.end_lineno or len(lines))
        for line_index in range(first_line, end_line):
            kind = MARKERS.get(lines[line_index].strip())
            if kind is None:
                continue
            span = json_span(lines, line_index, end_line)
            if span is None:
                continue
            body = example.body_for(kind) if example is not None else None
            if body is None:
                unsourced.append(f'{label} [{lines[line_index].strip()}]')
                continue
            indent = ' ' * (len(lines[line_index]) - len(lines[line_index].lstrip()))
            existing_lines = lines[span[0] : span[1] + 1]
            if _keeps_existing_block(existing_lines, body, indent):
                rendered = existing_lines
            else:
                rendered = render_block(body, indent)
            replacements.append(LineReplacement(start=span[0], end=span[1], lines=rendered))
    return replacements, unsourced


def rewrite_file(path: pathlib.Path, examples: dict[str, CollectionExample], check: bool) -> RewriteOutcome:
    """Refresh one module's example blocks in place, or only report staleness when `check`."""
    source_text = path.read_text(encoding='utf-8')
    lines = source_text.split('\n')
    replacements, unsourced = plan_replacements(source_text, examples)

    changed = False
    # Applied bottom-up so a resized block cannot shift the line indices of the
    # replacements still pending above it.
    for replacement in sorted(replacements, key=lambda item: -item.start):
        if lines[replacement.start : replacement.end + 1] != replacement.lines:
            changed = True
            if not check:
                lines[replacement.start : replacement.end + 1] = replacement.lines
    if changed and not check:
        with open(path, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write('\n'.join(lines))
    return RewriteOutcome(changed=changed, replaced=len(replacements), unsourced=unsourced)


def main() -> None:
    """Refresh (or, with `--check`, report on) every module's docstring examples."""
    parser = argparse.ArgumentParser(description='Refresh docstring examples from the CC Postman collection.')
    parser.add_argument('--check', action='store_true', help='report staleness and exit 1; do not write')
    parser.add_argument('--collection', default=COLLECTION_URL, help='collection URL or local path')
    args = parser.parse_args()

    try:
        collection = load_collection(args.collection)
    except CollectionUnavailable as exc:
        print(f'could not fetch collection ({args.collection}): {exc}', file=sys.stderr)
        sys.exit(2)  # distinct from 1 (stale) so a freshness test can skip when offline
    examples = build_examples(collection)

    any_stale = False
    all_unsourced: list[str] = []
    total_replaced = 0
    for path in sorted(SRC_DIR.glob('*.py')):
        outcome = rewrite_file(path, examples, args.check)
        total_replaced += outcome.replaced
        all_unsourced += [f'{path.name}:{marker}' for marker in outcome.unsourced]
        if outcome.changed:
            any_stale = True
            print(f'{"STALE" if args.check else "updated"}: {path.name}')
    if all_unsourced:
        print('\nno collection example (left as-is):')
        for marker in all_unsourced:
            print(f'  {marker}')
    if total_replaced == 0:
        # No marker matched a collection example (an empty collection, or every operation renamed):
        # every block is "unsourced", and exiting 0 would pass --check having verified nothing.
        print(f'\nno docstring marker matched the collection ({args.collection}): no verdict', file=sys.stderr)
        sys.exit(2)
    if args.check and any_stale:
        print('\nDocstring examples are out of sync. Run scripts/generate_docstrings.py.')
        sys.exit(1)
    if not args.check:
        print('done.')


if __name__ == '__main__':
    main()
