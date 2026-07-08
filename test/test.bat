:: Run tests and generate report
@echo off

echo Running ruff...
echo ruff check src
ruff check %~dp0..\src
echo ruff format --check src
ruff format --check %~dp0..\src
echo.

echo Running mypy...
echo mypy src
mypy %~dp0..\src

pytest
