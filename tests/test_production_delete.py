"""The production delete endpoints take their filters as query parameters.

Sending `well` / `startDate` / `endDate` as a request body returns
`400 Bad Request` -- verified live 2026-08-06 against a project monthly delete.
These tests pin the url the wrapper builds and the guard that refuses an
unfiltered delete, so a regression to a body payload fails here rather than
against the API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlsplit

import pytest
from requests.structures import CaseInsensitiveDict

from combocurve_api_helper.production import Production, _delete_filters

if TYPE_CHECKING:
    from combocurve_api_helper.base import ItemList

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


class _StubResponse:
    """Stands in for the single `requests.Response` a delete returns.

    `headers` is a real `CaseInsensitiveDict`, not a plain dict: the delete methods are
    annotated `-> CaseInsensitiveDict[str]` and tell callers to read `X-Delete-Count`,
    so a plain dict would let a case-sensitive lookup pass here and fail against the
    real response. Built per instance rather than as a shared class attribute.
    """

    def __init__(self, delete_count: str = '1') -> None:
        self.headers: CaseInsensitiveDict[str] = CaseInsensitiveDict({'X-Delete-Count': delete_count})


class _RecordingProduction(Production):
    """A `Production` that records the delete url instead of issuing a request.

    Deliberately does not call `APIBase.__init__`; these tests exercise url
    construction and the filter guard, neither of which needs auth.
    """

    def __init__(self) -> None:
        self.deleted_urls: list[str] = []
        self.deleted_bodies: list[Any] = []

    # `data` is concrete; the return stays `list[Any]` because `_StubResponse` is not a
    # `requests.Response` and a narrower type would not satisfy the base signature.
    def _delete_responses(self, url: str, data: ItemList, chunksize: int | None = None) -> list[Any]:
        self.deleted_urls.append(url)
        self.deleted_bodies.append(data)

        return [_StubResponse()]


@pytest.fixture
def api() -> _RecordingProduction:
    return _RecordingProduction()


def _query(url: str) -> dict[str, list[str]]:
    return parse_qs(urlsplit(url).query)


@pytest.mark.parametrize(('method', 'args', 'path'), DELETE_METHODS)
def test_filters_go_in_the_query_string_not_the_body(
    api: _RecordingProduction, method: str, args: tuple[str, ...], path: str
) -> None:
    headers = getattr(api, method)(*args, well_id=WELL_ID, start_date='2020-01-01', end_date='2020-12-31')

    # The PATH matters as much as the query: a method wired to the wrong builder would
    # delete daily records while the caller believed they deleted monthly ones.
    assert urlsplit(api.deleted_urls[0]).path == path
    assert _query(api.deleted_urls[0]) == {
        'well': [WELL_ID],
        'startDate': ['2020-01-01'],
        'endDate': ['2020-12-31'],
    }
    # The body must stay empty: the endpoint rejects a payload outright.
    assert api.deleted_bodies == [[]]
    assert headers['X-Delete-Count'] == '1'


@pytest.mark.parametrize(('method', 'args', 'path'), DELETE_METHODS)
@pytest.mark.parametrize('missing_well', ['', None])
def test_delete_without_a_well_is_refused(
    api: _RecordingProduction, method: str, args: tuple[str, ...], path: str, missing_well: str | None
) -> None:
    """`well` is `required: true` in the spec, so a date-only delete never leaves the process.

    `''` is covered alongside `None` because it is the shape a caller gets from an
    unresolved lookup, and it would otherwise build `?well=` and reach the API.
    """
    with pytest.raises(ValueError, match='well_id is required'):
        getattr(api, method)(*args, well_id=missing_well, start_date='2020-01-01')

    assert api.deleted_urls == []


def test_dates_are_optional_but_the_well_is_not() -> None:
    assert _delete_filters(WELL_ID, None, None) == {'well': WELL_ID}
    assert _delete_filters(WELL_ID, '2020-01-01', None) == {'well': WELL_ID, 'startDate': '2020-01-01'}
    assert _delete_filters(WELL_ID, None, '2020-12-31') == {'well': WELL_ID, 'endDate': '2020-12-31'}


def test_the_old_positional_data_call_never_reaches_the_api(api: _RecordingProduction) -> None:
    """The 2.1.0 shape was `delete_*(data: ItemList)`; that list must not become a filter.

    It is truthy, so a falsy-only guard would let it stringify into `?well=[{...}]` and
    issue a real DELETE. mypy rejects the call, but untyped callers exist.
    """
    with pytest.raises(ValueError, match='must be a well id string'):
        api.delete_company_daily_productions([{'well': WELL_ID, 'date': '2020-01-01'}])  # type: ignore[arg-type]

    assert api.deleted_urls == []


def test_delete_count_is_read_case_insensitively(api: _RecordingProduction) -> None:
    """Callers are told to read `X-Delete-Count`; an HTTP/2 server may send it lowercased."""
    headers = api.delete_project_monthly_productions(PROJECT_ID, well_id=WELL_ID)

    assert headers['X-Delete-Count'] == headers['x-delete-count'] == '1'
