"""Offline tests for the `--check` verdicts of `scripts/generate_docstrings.py`.

Exit codes: 0 fresh, 1 stale or unsourced, 2 no verdict. They run `main` against a synthetic
`src/` directory and a synthetic collection, so no network is used.
"""

import importlib.util
import json
import pathlib
import urllib.request
from types import ModuleType
from typing import Optional

import pytest

GEN = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'generate_docstrings.py'


def _load_generator() -> ModuleType:
    specification = importlib.util.spec_from_file_location('generate_docstrings_check_under_test', GEN)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


generator = _load_generator()

SOURCE_WITH_TWO_MARKERS = '''class Sample:
    def get_sample(self) -> None:
        """Get a sample.

        https://docs.api.combocurve.com/api/get-sample

        Example response:
        {{
            "a": 1
        }}
        """

    def delete_sample(self) -> None:
        """Delete a sample.

        https://docs.api.combocurve.com/api/{second_slug}

        Example response:
        {{}}
        """
'''


def _collection(operations: list[dict[str, object]]) -> dict[str, object]:
    return {'item': operations}


def _operation(name: str, response_body: Optional[str]) -> dict[str, object]:
    saved = [{'code': 200, 'body': response_body}] if response_body is not None else []
    return {'name': name, 'request': {'method': 'GET'}, 'response': saved}


def _run_check(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    collection: object,
    *,
    second_slug: str = 'delete-sample',
    allowlist: frozenset[str] = frozenset(),
) -> int:
    source_directory = tmp_path / 'src'
    source_directory.mkdir()
    (source_directory / 'sample.py').write_text(
        SOURCE_WITH_TWO_MARKERS.format(second_slug=second_slug), encoding='utf-8'
    )
    body = json.dumps(collection).encode('utf-8')

    class FetchedCollection:
        """The fetched collection, as `urlopen` returns it (only `read` is used)."""

        def read(self) -> bytes:
            return body

    # Served as the live collection (the URL branch), so a malformed tree takes the exit-2 path a fetch takes.
    monkeypatch.setattr(urllib.request, 'urlopen', lambda request, timeout=None: FetchedCollection())
    monkeypatch.setattr(generator, 'SRC_DIR', source_directory)
    monkeypatch.setattr(generator, 'ALLOWED_UNSOURCED_MARKERS', allowlist)
    monkeypatch.setattr('sys.argv', ['generate_docstrings.py', '--check', '--collection', generator.COLLECTION_URL])
    try:
        generator.main()
    except SystemExit as exit_request:
        assert isinstance(exit_request.code, int)
        return exit_request.code
    return 0


FRESH_SAMPLE = _operation('get-sample', '{"a": 1}')
UNSOURCED_LABEL = 'sample.py:delete_sample [Example response:]'


def test_all_markers_sourced_exits_zero(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    collection = _collection([FRESH_SAMPLE, _operation('delete-sample', '{}')])
    assert _run_check(monkeypatch, tmp_path, collection) == 0


def test_unsourced_marker_not_on_the_allowlist_exits_one_and_is_named(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    collection = _collection([FRESH_SAMPLE, _operation('delete-sample', None)])
    assert _run_check(monkeypatch, tmp_path, collection) == 1
    assert UNSOURCED_LABEL in capsys.readouterr().out


def test_renamed_slug_is_unsourced_not_silently_skipped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """The collection renamed the operation: the docstring's slug no longer matches anything."""
    collection = _collection([FRESH_SAMPLE, _operation('delete-sample-renamed', '{}')])
    assert _run_check(monkeypatch, tmp_path, collection) == 1


def test_allowlisted_unsourced_marker_exits_zero(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    collection = _collection([FRESH_SAMPLE, _operation('delete-sample', None)])
    assert _run_check(monkeypatch, tmp_path, collection, allowlist=frozenset({UNSOURCED_LABEL})) == 0


def test_allowlist_entry_that_gained_an_example_exits_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    collection = _collection([FRESH_SAMPLE, _operation('delete-sample', '{}')])
    assert _run_check(monkeypatch, tmp_path, collection, allowlist=frozenset({UNSOURCED_LABEL})) == 1
    assert 'now has a collection example' in capsys.readouterr().out


def test_allowlist_entry_whose_marker_is_gone_exits_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    collection = _collection([FRESH_SAMPLE, _operation('delete-sample', '{}')])
    gone = frozenset({'sample.py:removed_method [Example response:]'})
    assert _run_check(monkeypatch, tmp_path, collection, allowlist=gone) == 1
    assert 'marker not found' in capsys.readouterr().out


def test_stale_block_still_exits_one(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    collection = _collection([_operation('get-sample', '{"a": 1, "b": 2}'), _operation('delete-sample', '{}')])
    assert _run_check(monkeypatch, tmp_path, collection) == 1


@pytest.mark.parametrize(
    'operations',
    [
        ['not an object'],
        [{'name': 'folder', 'item': [7]}],
        [{'name': 'op', 'request': 'GET /x', 'response': []}],
        [{'name': 'op', 'request': {}, 'response': ['text']}],
        [{'name': 'op', 'request': {}, 'response': {'code': 200}}],
    ],
    ids=[
        'entry-is-a-string',
        'nested-entry-is-a-number',
        'request-is-a-string',
        'response-entry-is-a-string',
        'response-is-an-object',
    ],
)
def test_malformed_item_shapes_give_no_verdict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, operations: list[object]
) -> None:
    """Exit 2, never a traceback (exit 1, which the freshness test reads as "stale")."""
    assert _run_check(monkeypatch, tmp_path, {'item': operations}) == 2


def test_a_malformed_local_collection_raises_rather_than_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A local `--collection PATH` with a malformed tree is a real error (exit 1), never "offline"."""
    collection_path = tmp_path / 'collection.json'
    collection_path.write_text(json.dumps({'item': ['not an object']}), encoding='utf-8')
    monkeypatch.setattr('sys.argv', ['generate_docstrings.py', '--check', '--collection', str(collection_path)])
    with pytest.raises(ValueError, match='not a usable Postman collection'):
        generator.main()


def test_build_examples_raises_collection_unavailable_for_a_non_object_item() -> None:
    with pytest.raises(generator.CollectionUnavailable):
        generator.build_examples({'item': ['text']})


def test_fetch_passes_a_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    received: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: object = None) -> object:
        received['timeout'] = timeout
        raise TimeoutError('timed out')

    monkeypatch.setattr(urllib.request, 'urlopen', fake_urlopen)
    with pytest.raises(generator.CollectionUnavailable):
        generator.load_collection('https://example.com/collection.json')
    assert received['timeout'] == generator.FETCH_TIMEOUT_SECONDS


def test_fetch_timeout_gives_no_verdict(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def fake_urlopen(request: object, timeout: object = None) -> object:
        raise TimeoutError('timed out')

    monkeypatch.setattr(urllib.request, 'urlopen', fake_urlopen)
    monkeypatch.setattr('sys.argv', ['generate_docstrings.py', '--check', '--collection', 'https://example.com/c.json'])
    with pytest.raises(SystemExit) as exit_request:
        generator.main()
    assert exit_request.value.code == 2
    assert 'timed out' in capsys.readouterr().err
