"""The conftest hook adds a failing `requests.HTTPError`'s response to the test report."""

from types import SimpleNamespace
from typing import cast

import pytest
import requests

from tests.conftest import pytest_runtest_makereport


def _http_error(status: int, body: str) -> requests.HTTPError:
    request = requests.Request('POST', 'https://api.combocurve.com/v2/projects/p/type-curves/lookup-tables').prepare()
    response = requests.Response()
    response.status_code = status
    response._content = body.encode()
    response.url = str(request.url)
    response.request = request
    return requests.HTTPError(f'{status} Client Error', response=response)


def _sections_after(raised: BaseException) -> list[tuple[str, str]]:
    def fail() -> None:
        raise raised

    call = pytest.CallInfo.from_call(fail, 'call')
    sections: list[tuple[str, str]] = []
    report = SimpleNamespace(sections=sections)
    hook = pytest_runtest_makereport(cast('pytest.Item', None), call)
    next(hook)
    with pytest.raises(StopIteration) as stop:
        hook.send(cast('pytest.TestReport', report))
    assert stop.value.value is report
    return sections


def test_an_http_error_adds_status_method_url_and_body() -> None:
    sections = _sections_after(_http_error(404, '{"name": "LookupTableNotFoundError"}'))

    assert sections == [
        (
            'HTTP error response',
            '404 POST https://api.combocurve.com/v2/projects/p/type-curves/lookup-tables\n'
            '{"name": "LookupTableNotFoundError"}',
        )
    ]


def test_the_body_is_cut_at_2000_characters() -> None:
    sections = _sections_after(_http_error(500, 'x' * 5000))

    assert sections[0][1].endswith('\n' + 'x' * 2000)


def test_another_error_adds_nothing() -> None:
    assert _sections_after(ValueError('not http')) == []
