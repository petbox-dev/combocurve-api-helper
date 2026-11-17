"""Shared pytest setup: load the repo's gitignored `.env` into the environment, and add the response
body of a failing `requests.HTTPError` to the test report.

The live tests (`test_api.py`, `test_assignments_live.py`, `test_embedded_lookup_tables_live.py`,
`test_type_curves_v2_live.py`) read their target ids (`CC_DEV_PROJECT_ID`, `CC_DEV_SCENARIO_ID`,
`CC_DEV_DATES_MODEL_ID`, `CC_TC2_PROJECT_ID`, `CC_TC2_TYPE_CURVE_ID`) from the environment, because a
real id must not sit in this public repo. `.env.example` lists the names.

`load_dotenv()` searches from this file's directory upward, so the repo-root `.env` is found
whatever the working directory. It never overrides a variable that is already set. This runs
before pytest imports the test modules, which read the ids at import time.

It also adds the response of a failing `requests.HTTPError` to the test report: the error message
from `raise_for_status` names only the status and the url, and the body (the ComboCurve error name)
is the evidence a live failure needs. A 404 seen once on 2026-11-13 could not be diagnosed for lack
of it.

Every test gets its own OAuth token cache directory (`_isolated_token_cache`).
"""

from collections.abc import Generator

import pytest
import requests

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


try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is a dev dependency; without it the live tests just skip
    pass
else:
    load_dotenv()
