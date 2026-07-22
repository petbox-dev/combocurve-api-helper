:: Run tests and generate report
@echo off

echo Running ruff...
echo ruff check src tests
ruff check %~dp0..\src %~dp0..\tests
echo ruff format --check src tests
ruff format --check %~dp0..\src %~dp0..\tests
echo.

echo Running mypy...
echo mypy src tests
mypy %~dp0..\src %~dp0..\tests

pytest
