#!/usr/bin/env pwsh
# Regenerate every generated source file. Run after changing econModels.json, the
# mapper registry, or when the OpenAPI spec drifts. generate_docstrings.py fetches
# the live spec, so this step needs network. Bash equivalent: codegen.sh.

Write-Host 'Generating econ-model CRUD methods...'
python (Join-Path $PSScriptRoot 'generate_model_methods.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'Generating CSV convenience functions...'
python (Join-Path $PSScriptRoot 'generate_csv_functions.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'Generating docstring examples from the OpenAPI spec...'
python (Join-Path $PSScriptRoot 'generate_docstrings.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'Done.'
