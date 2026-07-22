#!/bin/bash
# Regenerate every generated source file. Run after changing econModels.json, the
# mapper registry, or when the OpenAPI spec drifts. generate_docstrings.py fetches
# the live spec, so this step needs network. PowerShell equivalent: codegen.ps1.
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo Generating econ-model CRUD methods...
python $DIR/generate_model_methods.py

echo Generating CSV convenience functions...
python $DIR/generate_csv_functions.py

echo Generating docstring examples from the OpenAPI spec...
python $DIR/generate_docstrings.py

echo Done.
