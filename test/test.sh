#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo Running ruff...
echo ruff check src
ruff check $DIR/../src
echo ruff format --check src
ruff format --check $DIR/../src
echo

echo Running mypy...
echo mypy src
mypy $DIR/../src
echo
