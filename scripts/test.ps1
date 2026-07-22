#!/usr/bin/env pwsh
# Pre-commit checks: ruff lint + format-check, mypy, pytest (src + tests).
# Bash equivalent: test.sh. cmd equivalent: test.bat.

$repo = Split-Path -Parent $PSScriptRoot
$src = Join-Path $repo 'src'
$tests = Join-Path $repo 'tests'

Write-Host 'Running ruff...'
ruff check $src $tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
ruff format --check $src $tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'Running mypy...'
mypy $src $tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'Running pytest...'
pytest
exit $LASTEXITCODE
