:: Run tests and generate report
@echo off

echo Running flake8...
echo flake8 src
flake8 %~dp0..\src
echo.

echo Running mypy...
echo mypy src
mypy %~dp0..\src

pytest
