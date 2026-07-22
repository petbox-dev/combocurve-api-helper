#!/bin/bash
# Pre-commit checks: ruff lint + format-check, mypy, pytest (src + tests).
# PowerShell equivalent: test.ps1. cmd equivalent: test.bat.
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo Running ruff...
ruff check $DIR/../src $DIR/../tests
ruff format --check $DIR/../src $DIR/../tests
echo

echo Running mypy...
mypy $DIR/../src $DIR/../tests
echo

echo Running pytest...
pytest
