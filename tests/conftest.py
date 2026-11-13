"""Shared pytest setup: load the repo's gitignored `.env` into the environment.

The live tests (`test_api.py`, `test_assignments_live.py`) read their dev target ids
(`CC_DEV_PROJECT_ID`, `CC_DEV_SCENARIO_ID`, `CC_DEV_DATES_MODEL_ID`) from the environment,
because a real id must not sit in this public repo. `.env.example` lists the names.

`load_dotenv()` searches from this file's directory upward, so the repo-root `.env` is found
whatever the working directory. It never overrides a variable that is already set. This runs
before pytest imports the test modules, which read the ids at import time.

It also adds the response of a failing `requests.HTTPError` to the test report: the error message
from `raise_for_status` names only the status and the url, and the body (the ComboCurve error name)
is the evidence a live failure needs. A 404 seen once on 2026-11-13 could not be diagnosed for lack
of it.
"""

from collections.abc import Generator

import pytest
import requests

_MAX_BODY_CHARACTERS = 2000


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    report = yield
    error = call.excinfo.value if call.excinfo is not None else None
    if isinstance(error, requests.HTTPError) and error.response is not None:
        response = error.response
        report.sections.append(
            (
                'HTTP error response',
                f'{response.status_code} {response.request.method if response.request else ""} {response.url}\n'
                f'{response.text[:_MAX_BODY_CHARACTERS]}',
            )
        )
    return report


try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is a dev dependency; without it the live tests just skip
    pass
else:
    load_dotenv()
