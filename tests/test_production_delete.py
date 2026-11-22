"""The production delete endpoints take their filters as query parameters.

Sending `well` / `startDate` / `endDate` as a request body returns
`400 Bad Request` -- verified live 2026-08-06 against a project monthly delete.
These tests pin the url the wrapper builds and the guard that refuses an
unfiltered delete, so a regression to a body payload fails here rather than
against the API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlsplit

import pytest

from combocurve_api_helper.production import _delete_filters
from tests.http_fakes import FakeResponse, RecordingTransport, install_responding_transport, make_offline_api

if TYPE_CHECKING:
    from combocurve_api_helper import ComboCurveAPI

PROJECT_ID = '000000000000000000000001'
WELL_ID = '000000000000000000000002'

# Every production delete, with the leading positional args its url needs. Shared so a
# fifth endpoint is added once rather than to each parametrize list independently.
DELETE_METHODS: list[tuple[str, tuple[str, ...], str]] = [
    ('delete_company_monthly_productions', (), '/v1/monthly-productions'),
    ('delete_company_daily_productions', (), '/v1/daily-productions'),
    ('delete_project_monthly_productions', (PROJECT_ID,), f'/v1/projects/{PROJECT_ID}/monthly-productions'),
    ('delete_project_daily_productions', (PROJECT_ID,), f'/v1/projects/{PROJECT_ID}/daily-productions'),
]


@pytest.fixture
def transport(monkeypatch: pytest.MonkeyPatch) -> RecordingTransport:
    """Records every request and answers each with `X-Delete-Count: 1`. `FakeResponse.headers` is a
    `CaseInsensitiveDict`, as on the real response, so a case-sensitive lookup cannot pass here and
    fail against the API."""
    return install_responding_transport(
        monkeypatch, lambda call: FakeResponse(200, [], headers={'X-Delete-Count': '1'})
    )


@pytest.fixture
def api(transport: RecordingTransport) -> ComboCurveAPI:
    return make_offline_api()


def _query(url: str) -> dict[str, list[str]]:
    return parse_qs(urlsplit(url).query)


@pytest.mark.parametrize(('method', 'args', 'path'), DELETE_METHODS)
def test_filters_go_in_the_query_string_not_the_body(
    api: ComboCurveAPI, transport: RecordingTransport, method: str, args: tuple[str, ...], path: str
) -> None:
    headers = getattr(api, method)(*args, well_id=WELL_ID, start_date='2020-01-01', end_date='2020-12-31')

    # The PATH matters as much as the query: a method wired to the wrong builder would
    # delete daily records while the caller believed they deleted monthly ones.
    (call,) = transport.calls
    assert call.method == 'DELETE'
    assert urlsplit(call.url).path == path
    assert _query(call.url) == {
        'well': [WELL_ID],
        'startDate': ['2020-01-01'],
        'endDate': ['2020-12-31'],
    }
    # No body is sent: the endpoint rejects a payload outright.
    assert call.body is None
    assert headers['X-Delete-Count'] == '1'


@pytest.mark.parametrize(('method', 'args', 'path'), DELETE_METHODS)
@pytest.mark.parametrize('missing_well', ['', None])
def test_delete_without_a_well_is_refused(
    api: ComboCurveAPI,
    transport: RecordingTransport,
    method: str,
    args: tuple[str, ...],
    path: str,
    missing_well: str | None,
) -> None:
    """`well` is `required: true` in the spec, so a date-only delete never leaves the process.

    `''` is covered alongside `None` because it is the shape a caller gets from an
    unresolved lookup, and it would otherwise build `?well=` and reach the API.
    """
    with pytest.raises(ValueError, match='well_id is required'):
        getattr(api, method)(*args, well_id=missing_well, start_date='2020-01-01')

    assert transport.calls == []


def test_dates_are_optional_but_the_well_is_not() -> None:
    assert _delete_filters(WELL_ID, None, None) == {'well': WELL_ID}
    assert _delete_filters(WELL_ID, '2020-01-01', None) == {'well': WELL_ID, 'startDate': '2020-01-01'}
    assert _delete_filters(WELL_ID, None, '2020-12-31') == {'well': WELL_ID, 'endDate': '2020-12-31'}
    # An empty-string date (the shape an unset config value takes) is DROPPED, like `None`,
    # rather than sent as `?startDate=` -- the dates guard on falsiness, not `is not None`.
    assert _delete_filters(WELL_ID, '', '') == {'well': WELL_ID}
    assert _delete_filters(WELL_ID, '', '2020-12-31') == {'well': WELL_ID, 'endDate': '2020-12-31'}


def test_the_old_positional_data_call_never_reaches_the_api(api: ComboCurveAPI, transport: RecordingTransport) -> None:
    """The 2.1.0 shape was `delete_*(data: ItemList)`; that list must not become a filter.

    It is truthy, so a falsy-only guard would let it stringify into `?well=[{...}]` and
    issue a real DELETE. mypy rejects the call, but untyped callers exist.
    """
    with pytest.raises(ValueError, match='must be a well id string'):
        api.delete_company_daily_productions([{'well': WELL_ID, 'date': '2020-01-01'}])  # type: ignore[arg-type]

    assert transport.calls == []


def test_delete_count_is_read_case_insensitively(api: ComboCurveAPI, transport: RecordingTransport) -> None:
    """Callers are told to read `X-Delete-Count`; an HTTP/2 server may send it lowercased."""
    headers = api.delete_project_monthly_productions(PROJECT_ID, well_id=WELL_ID)

    assert headers['X-Delete-Count'] == headers['x-delete-count'] == '1'
