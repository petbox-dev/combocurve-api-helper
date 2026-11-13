"""The conftest hook adds a failing `requests.HTTPError`'s response to the test report."""

from types import SimpleNamespace
from typing import cast

import pytest
import requests

from tests.conftest import _MAX_BODY_CHARACTERS, pytest_runtest_makereport
from tests.http_fakes import FakeResponse


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


def test_the_body_is_cut_at_the_maximum() -> None:
    sections = _sections_after(_http_error(500, 'x' * (_MAX_BODY_CHARACTERS * 2)))

    assert sections[0][1].endswith('\n' + 'x' * _MAX_BODY_CHARACTERS)
    assert not sections[0][1].endswith('x' * (_MAX_BODY_CHARACTERS + 1))


def test_a_response_without_a_request_reports_no_method() -> None:
    error = _http_error(400, 'bad')
    assert error.response is not None
    error.response.request = None  # as on a hand-built `requests.Response`

    sections = _sections_after(error)

    assert sections[0][1].startswith('400  https://api.combocurve.com/')


def test_an_error_from_the_fake_response_is_reported_not_an_internal_error() -> None:
    """The offline tests raise `HTTPError` through `FakeResponse`; the hook must not crash on it."""
    with pytest.raises(requests.HTTPError) as raised:
        FakeResponse(404, text='{"name": "ProjectNotFoundError"}').raise_for_status()

    assert _sections_after(raised.value) == [('HTTP error response', '404  \n{"name": "ProjectNotFoundError"}')]


def test_a_response_with_only_a_status_is_reported_not_an_internal_error() -> None:
    """A response-like double with no `request`, `url` or `text` must not crash the hook."""
    error = requests.HTTPError('502 error', response=cast('requests.Response', SimpleNamespace(status_code=502)))

    assert _sections_after(error) == [('HTTP error response', '502  \n')]


def test_another_error_adds_nothing() -> None:
    assert _sections_after(ValueError('not http')) == []
