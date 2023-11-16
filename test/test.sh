#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo Running flake8...
echo flake8 src
flake8 $DIR/../src
echo

echo Running mypy...
echo mypy src
mypy $DIR/../src
echo
