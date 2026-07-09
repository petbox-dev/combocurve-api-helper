"""Refresh docstring example blocks from the ComboCurve OpenAPI (Swagger 2.0) spec.

Each method docstring links to https://docs.api.combocurve.com/api/<operationId>.
This tool fetches the spec, and for every method whose docstring has that link it
rewrites the `Example response:` block from the operation's 200 example and the
`Example data:` / `Example request:` block from the request body's example, in
place. Descriptions are untouched -- only the JSON under an example marker is
replaced.

Usage:
    python scripts/generate_docstrings.py            # rewrite in place
    python scripts/generate_docstrings.py --check     # exit 1 if anything is stale (no write)
    python scripts/generate_docstrings.py --spec PATH # use a local spec instead of the URL
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

import yaml

SPEC_URL = 'https://storage.googleapis.com/beta-combocurve-api-docs/openapi-spec.yaml'
SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / 'src' / 'combocurve_api_helper'
URL_RE = re.compile(r'https://docs\.api\.combocurve\.com/api/([a-z0-9-]+)')
# marker text (stripped) -> which spec example feeds it
MARKERS = {'Example response:': 'response', 'Example data:': 'request', 'Example request:': 'request'}
METHODS = ('get', 'post', 'put', 'patch', 'delete', 'head')


def load_spec(src: str) -> dict:
    if src.startswith(('http://', 'https://')):
        raw = urllib.request.urlopen(urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'})).read()
    else:
        raw = pathlib.Path(src).read_bytes()
    return yaml.safe_load(raw)


def build_examples(spec: dict) -> dict:
    """operationId -> {'response': obj|None, 'request': obj|None} of JSON examples."""
    defs = spec.get('definitions', {})
    out: dict = {}
    for _path, item in spec.get('paths', {}).items():
        for method, op in item.items():
            if method.lower() not in METHODS or not isinstance(op, dict):
                continue
            oid = op.get('operationId')
            if not oid:
                continue
            response = None
            responses = op.get('responses', {}) or {}
            for code in ('200', '201', 'default'):
                examples = (responses.get(code) or {}).get('examples') or {}
                if 'application/json' in examples:
                    response = examples['application/json']
                    break
            request = None
            for param in op.get('parameters', []) or []:
                if param.get('in') == 'body':
                    schema = param.get('schema', {}) or {}
                    if 'example' in schema:
                        request = schema['example']
                    else:
                        ref = schema.get('$ref', '').split('/')[-1]
                        if ref and ref in defs and 'example' in defs[ref]:
                            request = defs[ref]['example']
                    break
            out[oid] = {'response': response, 'request': request}
    return out


def json_span(lines: list, marker_idx: int, hi: int) -> tuple | None:
    """Return (start, end) inclusive line indices of the JSON block after a marker,
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
    """Return [(node, operationId)] for example-bearing nodes.

    Two shapes hold example blocks:
      * a method docstring, whose operationId comes from its /api/<slug> link;
      * a module-level string constant appended to one or more methods'
        __doc__ (`Klass.method.__doc__ += const`) to share an example across
        company/project variants -- keyed to the first (representative) method
        it is appended to.
    """
    name_to_opid: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ds = ast.get_docstring(node, clean=False)
            if ds:
                m = URL_RE.search(ds)
                if m:
                    name_to_opid[node.name] = m.group(1)
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
                const_to_method.setdefault(node.value.id, tgt.value.attr)  # first append is representative

    targets = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in name_to_opid:
            targets.append((node, name_to_opid[node.name]))
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id in const_to_method:
                    opid = name_to_opid.get(const_to_method[tgt.id])
                    if opid:
                        targets.append((node, opid))
    return targets


def rewrite_file(path: pathlib.Path, examples: dict, check: bool) -> tuple:
    """Returns (changed: bool, updated: int, unsourced: list). Writes unless `check`."""
    text = path.read_text(encoding='utf-8')
    lines = text.split('\n')
    tree = ast.parse(text)
    replacements = []  # (json_start, json_end, new_lines)
    unsourced = []
    for node, opid in collect_targets(tree):
        ex = examples.get(opid)
        label = getattr(node, 'name', None) or opid
        lo, hi = node.lineno - 1, (node.end_lineno or len(lines))
        for i in range(lo, hi):
            marker = lines[i].strip()
            kind = MARKERS.get(marker)
            if kind is None:
                continue
            span = json_span(lines, i, hi)
            if span is None:
                continue
            obj = (ex or {}).get(kind)
            if obj is None:
                unsourced.append(f'{label} [{marker}]')
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
    updated = sum(1 for js, je, nj in replacements if lines[js : je + 1] != nj) if check else len(replacements)
    if changed and not check:
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(lines))
    return changed, updated, unsourced


def main() -> None:
    parser = argparse.ArgumentParser(description='Refresh docstring examples from the CC OpenAPI spec.')
    parser.add_argument('--check', action='store_true', help='report staleness and exit 1; do not write')
    parser.add_argument('--spec', default=SPEC_URL, help='spec URL or local path (default: official URL)')
    args = parser.parse_args()

    try:
        spec = load_spec(args.spec)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f'could not fetch spec ({args.spec}): {exc}', file=sys.stderr)
        sys.exit(2)  # distinct from 1 (stale) so a freshness test can skip when offline
    examples = build_examples(spec)
    any_stale = False
    all_unsourced = []
    for path in sorted(SRC_DIR.glob('*.py')):
        changed, _updated, unsourced = rewrite_file(path, examples, args.check)
        all_unsourced += [f'{path.name}:{u}' for u in unsourced]
        if changed:
            any_stale = True
            print(f'{"STALE" if args.check else "updated"}: {path.name}')
    if all_unsourced:
        print('\nno spec example (left as-is):')
        for u in all_unsourced:
            print(f'  {u}')
    if args.check and any_stale:
        print('\nDocstring examples are out of sync with the spec. Run scripts/generate_docstrings.py.')
        sys.exit(1)
    if not args.check:
        print('done.')


if __name__ == '__main__':
    main()
