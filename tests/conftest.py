"""Shared pytest setup: load the repo's gitignored `.env` into the environment, and add the response
body of a failing `requests.HTTPError` to the test report.

The live tests (`test_api.py` and every `test_*_live.py`) read their targets (`CC_DEV_PROJECT_ID`,
`CC_DEV_SCENARIO_ID`, `CC_DEV_DATES_MODEL_ID`, `CC_DEV_TYPE_CURVE_ID`, `CC_DEV_ECON_CATEGORY`,
`CC_DEV_ECON_COLUMN_KEY`) from the environment, because a real id must not sit in this public repo.
`.env.example` lists the names.

`load_dotenv()` searches from this file's directory upward, so the repo-root `.env` is found
whatever the working directory. It never overrides a variable that is already set. This runs
before pytest imports the test modules, which read the ids at import time.

It also adds the response of a failing `requests.HTTPError` to the test report: the error message
from `raise_for_status` names only the status and the url, and the body (the ComboCurve error name)
is the evidence a live failure needs. A 404 seen once on 2026-11-13 could not be diagnosed for lack
of it.

Every test gets its own OAuth token cache directory (`_isolated_token_cache`). The live dev tests share
one session-scoped client (`dev_api`), so a run fetches at most one token for them; the setup they share
is in `tests/live_support.py`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import requests

if TYPE_CHECKING:
    from collections.abc import Generator

    from combocurve_api_helper import ComboCurveAPI

# A ComboCurve error body is a short JSON object; the cap keeps an HTML gateway page from flooding
# the report.
_MAX_BODY_CHARACTERS = 2000


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """Append an 'HTTP error response' section (status, method, url, body) when the test raised
    `requests.HTTPError`. The response attributes are read with `getattr`: the error can carry a test
    double (`tests.http_fakes.FakeResponse`), and an `AttributeError` raised here would replace the
    test's own failure with a pytest INTERNALERROR."""
    report = yield
    error = call.excinfo.value if call.excinfo is not None else None
    if isinstance(error, requests.HTTPError) and error.response is not None:
        response = error.response
        request = getattr(response, 'request', None)
        method = getattr(request, 'method', None) or ''
        report.sections.append(
            (
                'HTTP error response',
                f'{getattr(response, "status_code", "")} {method} {getattr(response, "url", "")}\n'
                f'{str(getattr(response, "text", ""))[:_MAX_BODY_CHARACTERS]}',
            )
        )
    return report


@pytest.fixture(autouse=True)
def _isolated_token_cache(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the OAuth token disk cache at a fresh directory, so no test reads or writes the user's
    `~/.combocurve/token-cache` or sees a token another test cached."""
    from combocurve_api_helper import config

    monkeypatch.setattr(config, 'TOKEN_CACHE_DIRECTORY', tmp_path_factory.mktemp('token-cache'))


@pytest.fixture(scope='session')
def dev_api(tmp_path_factory: pytest.TempPathFactory) -> ComboCurveAPI:
    """One dev client for every live test of the session. It keeps its token in memory, so a run fetches
    at most one dev token. Its disk token cache is a session temp directory, never the user's
    `~/.combocurve/token-cache`: the client reads `config.TOKEN_CACHE_DIRECTORY` when it is built, and this
    session fixture is built before the per-test `_isolated_token_cache` patch applies. Built only when a
    live test that is not skipped asks for it: constructing it reads the credential files, and sends
    nothing."""
    from combocurve_api_helper import ComboCurveAPI, config
    from tests.live_support import DEV_CREDENTIALS_DIRECTORY

    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(config, 'TOKEN_CACHE_DIRECTORY', tmp_path_factory.mktemp('dev-token-cache'))
        return ComboCurveAPI.from_credentials_directory(DEV_CREDENTIALS_DIRECTORY)


try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is a dev dependency; without it the live tests just skip
    pass
else:
    load_dotenv()
