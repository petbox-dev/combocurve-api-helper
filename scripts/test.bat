:: Run tests and generate report
@echo off
:: src + tests + scripts. scripts/ holds the codegen and audit tools; a stale
:: annotation there ships broken generated source.

echo Running ruff...
echo ruff check src tests scripts
ruff check %~dp0..\src %~dp0..\tests %~dp0..\scripts
if errorlevel 1 exit /b %errorlevel%
echo ruff format --check src tests scripts
ruff format --check %~dp0..\src %~dp0..\tests %~dp0..\scripts
if errorlevel 1 exit /b %errorlevel%
echo.

echo Running mypy...
echo mypy src tests scripts
mypy %~dp0..\src %~dp0..\tests %~dp0..\scripts
if errorlevel 1 exit /b %errorlevel%

pytest
exit /b %errorlevel%
