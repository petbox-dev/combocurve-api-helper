#!/bin/bash
# Pre-commit checks: ruff lint + format-check, mypy, pytest (src + tests + scripts).
# scripts/ is included: it holds the codegen and audit tools, and a stale annotation
# there ships broken generated source. Excluding it is how a `Dict[...]` literal
# survived the typing sweep.
# PowerShell equivalent: test.ps1. cmd equivalent: test.bat.
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo Running ruff...
ruff check $DIR/../src $DIR/../tests $DIR/../scripts
ruff format --check $DIR/../src $DIR/../tests $DIR/../scripts
echo

echo Running mypy...
mypy $DIR/../src $DIR/../tests $DIR/../scripts
echo

echo Running pytest...
pytest
