"""Type-checker test: the `get_project_custom_columns` overloads refuse a call with no custom column.

Until 3.x the signature was `custom_column: Optional[str] = None`, so `mypy --strict` accepted
`api.get_project_custom_columns(project_id)` and the `TypeError` came only at run time (a downstream
caller shipped that call). The overloads make `custom_column` required for the type checker, and mark
the `collection=` alias as deprecated. This runs mypy on a small snippet against `src/`, with its own
cache directory so that it does not share `.mypy_cache` with a concurrent run.
"""

import re
from pathlib import Path

from mypy import api as mypy_api

SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / 'src'

# `<path>snippet.py:<line>: error: <message>  [<error code>]`; the message itself can hold colons.
ERROR_LINE_PATTERN = re.compile(r'snippet\.py:(\d+): error: .*\[([a-z-]+)\]\s*$', re.MULTILINE)

SNIPPET = """\
from combocurve_api_helper import ComboCurveAPI


def use(api: ComboCurveAPI) -> None:
    api.get_project_custom_columns('P', 'headers')
    api.get_project_custom_columns('P', custom_column='headers', filters={'key': 'value'})
    api.get_project_custom_columns_url('P', 'headers')
    api.get_project_custom_columns('P')  # line 8
    api.get_project_custom_columns_url('P')  # line 9
    api.get_project_custom_columns('P', collection='headers')  # line 10
    api.get_project_custom_columns_url('P', collection='headers')  # line 11
"""


def test_mypy_refuses_a_call_without_a_custom_column_and_flags_the_deprecated_alias(tmp_path: Path) -> None:
    snippet_path = tmp_path / 'snippet.py'
    snippet_path.write_text(SNIPPET, encoding='utf-8')
    # `mypy_path` puts `src/` ahead of any installed copy of the package in site-packages.
    config_path = tmp_path / 'mypy.ini'
    config_path.write_text(f'[mypy]\nmypy_path = {SOURCE_DIRECTORY.as_posix()}\n', encoding='utf-8')

    stdout, stderr, exit_status = mypy_api.run(
        [
            '--config-file',
            str(config_path),
            '--cache-dir',
            str(tmp_path / 'mypy-cache'),
            '--strict',
            '--enable-error-code',
            'deprecated',
            '--no-error-summary',
            '--hide-error-context',
            str(snippet_path),
        ]
    )

    assert exit_status == 1, stdout + stderr
    error_lines = sorted((int(match.group(1)), match.group(2)) for match in ERROR_LINE_PATTERN.finditer(stdout))
    assert error_lines == [
        (8, 'call-overload'),
        (9, 'call-overload'),
        (10, 'deprecated'),
        (11, 'deprecated'),
    ], stdout
