#!/usr/bin/env pwsh
# Pre-commit checks: ruff lint + format-check, mypy, pytest (src + tests + scripts).
# scripts/ is included: it holds the codegen and audit tools, and a stale annotation
# there ships broken generated source.
# Bash equivalent: test.sh. cmd equivalent: test.bat.

$repo = Split-Path -Parent $PSScriptRoot
$src = Join-Path $repo 'src'
$tests = Join-Path $repo 'tests'
$scripts = Join-Path $repo 'scripts'

Write-Host 'Running ruff...'
ruff check $src $tests $scripts
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
ruff format --check $src $tests $scripts
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'Running mypy...'
mypy $src $tests $scripts
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'Running pytest...'
pytest
exit $LASTEXITCODE
