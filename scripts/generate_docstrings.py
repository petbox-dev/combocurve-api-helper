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

Usage:
    python scripts/generate_docstrings.py             # rewrite in place
    python scripts/generate_docstrings.py --check      # exit 1 if stale (no write)
    python scripts/generate_docstrings.py --collection PATH  # local collection JSON
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

COLLECTION_URL = 'https://docs.api.combocurve.com/downloads/combocurve-api.postman_collection.json'
SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / 'src' / 'combocurve_api_helper'
URL_RE = re.compile(r'https://docs\.api\.combocurve\.com/api/([a-z0-9-]+)')
TOKEN_RE = re.compile(r'<(\w+)>')
MARKERS = {'Example response:': 'response', 'Example data:': 'request', 'Example request:': 'request'}
# Success codes to prefer for the "Example response:" body (POST creates return 207).
_RESPONSE_CODES = (200, 201, 202, 207)


def spoof(token: str, key: str):  # noqa: ANN201 - returns a JSON scalar
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


def fill(obj, key: str = ''):  # noqa: ANN001,ANN201
    """Recursively replace `<type>` placeholder strings with spoof values, and
    collapse arrays whose elements are all identical (Postman doubles examples)."""
    if isinstance(obj, dict):
        return {k: fill(v, k) for k, v in obj.items()}
    if isinstance(obj, list):
        items = [fill(v, key) for v in obj]
        if len(items) > 1:
            first = json.dumps(items[0], sort_keys=True, default=str)
            if all(json.dumps(x, sort_keys=True, default=str) == first for x in items[1:]):
                return [items[0]]
        return items
    if isinstance(obj, str):
        m = TOKEN_RE.fullmatch(obj)
        return spoof(m.group(1), key) if m else obj
    return obj


def load_collection(src: str) -> dict:
    if src.startswith(('http://', 'https://')):
        raw = urllib.request.urlopen(urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'})).read()
    else:
        raw = pathlib.Path(src).read_bytes()
    return json.loads(raw)


def build_examples(collection: dict) -> dict:
    """item name -> {'response': obj|None, 'request': obj|None}, placeholders filled."""
    out: dict = {}

    def walk(items):
        for it in items:
            if 'item' in it:
                walk(it['item'])
            elif 'request' in it:
                cands = {r.get('code'): r for r in (it.get('response') or []) if (r.get('body') or '').strip()}
                resp = next((cands[c] for c in _RESPONSE_CODES if c in cands), None)
                if resp is None and cands:
                    resp = next(iter(cands.values()))
                response = None
                if resp is not None:
                    try:
                        response = fill(json.loads(resp['body']))
                    except (ValueError, TypeError):
                        response = None
                raw = (it['request'].get('body') or {}).get('raw')
                request = None
                if raw and raw.strip():
                    try:
                        request = fill(json.loads(raw))
                    except (ValueError, TypeError):
                        request = None
                out[it.get('name')] = {'response': response, 'request': request}

    walk(collection.get('item', []))
    return out


def json_span(lines: list, marker_idx: int, hi: int) -> tuple | None:
    """(start, end) inclusive line indices of the JSON block after a marker,
    bounded by `hi`. Bracket-matched with string awareness; None if not found."""
    start = None
    for i in range(marker_idx + 1, hi):
        stripped = lines[i].strip()
        if not stripped:
            continue
        start = i if stripped[0] in '[{' else None
        break
    if start is None:
        return None
    depth = 0
    in_str = False
    esc = False
    entered = False
    for i in range(start, hi):
        for ch in lines[i]:
            if in_str:
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch in '[{':
                depth += 1
                entered = True
            elif ch in ']}':
                depth -= 1
        if entered and depth == 0:
            return (start, i)
    return None


def collect_targets(tree: ast.AST) -> list:
    """[(node, item-name)] for example-bearing nodes: method docstrings (name from
    their /api/<slug> link) and module-level example constants appended to a method
    via `Klass.method.__doc__ += const` (keyed to the first such method)."""
    name_to_slug: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ds = ast.get_docstring(node, clean=False)
            if ds:
                m = URL_RE.search(ds)
                if m:
                    name_to_slug[node.name] = m.group(1)
    const_to_method: dict = {}
    for node in getattr(tree, 'body', []):
        if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
            tgt = node.target
            if (
                isinstance(tgt, ast.Attribute)
                and tgt.attr == '__doc__'
                and isinstance(tgt.value, ast.Attribute)
                and isinstance(node.value, ast.Name)
            ):
                const_to_method.setdefault(node.value.id, tgt.value.attr)

    targets = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in name_to_slug:
            targets.append((node, name_to_slug[node.name]))
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id in const_to_method:
                    slug = name_to_slug.get(const_to_method[tgt.id])
                    if slug:
                        targets.append((node, slug))
    return targets


def rewrite_file(path: pathlib.Path, examples: dict, check: bool) -> tuple:
    """Returns (changed, updated, unsourced). Writes unless `check`."""
    text = path.read_text(encoding='utf-8')
    lines = text.split('\n')
    tree = ast.parse(text)
    replacements = []
    unsourced = []
    for node, slug in collect_targets(tree):
        ex = examples.get(slug)
        label = getattr(node, 'name', None) or slug
        lo, hi = node.lineno - 1, (node.end_lineno or len(lines))
        for i in range(lo, hi):
            kind = MARKERS.get(lines[i].strip())
            if kind is None:
                continue
            span = json_span(lines, i, hi)
            if span is None:
                continue
            obj = (ex or {}).get(kind)
            if obj is None:
                unsourced.append(f'{label} [{lines[i].strip()}]')
                continue
            indent = ' ' * (len(lines[i]) - len(lines[i].lstrip()))
            new_json = [indent + ln for ln in json.dumps(obj, indent=4, default=str).split('\n')]
            replacements.append((span[0], span[1], new_json))

    changed = False
    for js, je, new_json in sorted(replacements, key=lambda r: -r[0]):
        if lines[js : je + 1] != new_json:
            changed = True
            if not check:
                lines[js : je + 1] = new_json
    if changed and not check:
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(lines))
    return changed, len(replacements), unsourced


def main() -> None:
    parser = argparse.ArgumentParser(description='Refresh docstring examples from the CC Postman collection.')
    parser.add_argument('--check', action='store_true', help='report staleness and exit 1; do not write')
    parser.add_argument('--collection', default=COLLECTION_URL, help='collection URL or local path')
    args = parser.parse_args()

    try:
        collection = load_collection(args.collection)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f'could not fetch collection ({args.collection}): {exc}', file=sys.stderr)
        sys.exit(2)  # distinct from 1 (stale) so a freshness test can skip when offline
    examples = build_examples(collection)

    any_stale = False
    all_unsourced = []
    for path in sorted(SRC_DIR.glob('*.py')):
        changed, _updated, unsourced = rewrite_file(path, examples, args.check)
        all_unsourced += [f'{path.name}:{u}' for u in unsourced]
        if changed:
            any_stale = True
            print(f'{"STALE" if args.check else "updated"}: {path.name}')
    if all_unsourced:
        print('\nno collection example (left as-is):')
        for u in all_unsourced:
            print(f'  {u}')
    if args.check and any_stale:
        print('\nDocstring examples are out of sync. Run scripts/generate_docstrings.py.')
        sys.exit(1)
    if not args.check:
        print('done.')


if __name__ == '__main__':
    main()
