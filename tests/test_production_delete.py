"""The production delete endpoints take their filters as query parameters.

Sending `well` / `startDate` / `endDate` as a request body returns
`400 Bad Request` -- verified live 2026-08-06 against a project monthly delete.
These tests pin the url the wrapper builds and the guard that refuses an
unfiltered delete, so a regression to a body payload fails here rather than
against the API.
"""

from __future__ import annotations

from typing import Any, ClassVar
from urllib.parse import parse_qs, urlsplit

import pytest

from combocurve_api_helper.production import Production, _delete_filters

PROJECT_ID = '000000000000000000000001'
WELL_ID = '000000000000000000000002'


class _StubResponse:
    """Stands in for the single `requests.Response` a delete returns."""

    headers: ClassVar[dict[str, str]] = {'X-Delete-Count': '1'}


class _RecordingProduction(Production):
    """A `Production` that records the delete url instead of issuing a request.

    Deliberately does not call `APIBase.__init__`; these tests exercise url
    construction and the filter guard, neither of which needs auth.
    """

    def __init__(self) -> None:
        self.deleted_urls: list[str] = []
        self.deleted_bodies: list[Any] = []

    def _delete_responses(  # type: ignore[override]
        self, url: str, data: Any, chunksize: int | None = None
    ) -> list[Any]:
        self.deleted_urls.append(url)
        self.deleted_bodies.append(data)

        return [_StubResponse()]


@pytest.fixture
def api() -> _RecordingProduction:
    return _RecordingProduction()


def _query(url: str) -> dict[str, list[str]]:
    return parse_qs(urlsplit(url).query)


@pytest.mark.parametrize(
    ('method', 'args'),
    [
        ('delete_company_monthly_productions', ()),
        ('delete_company_daily_productions', ()),
        ('delete_project_monthly_productions', (PROJECT_ID,)),
        ('delete_project_daily_productions', (PROJECT_ID,)),
    ],
)
def test_filters_go_in_the_query_string_not_the_body(
    api: _RecordingProduction, method: str, args: tuple[str, ...]
) -> None:
    headers = getattr(api, method)(*args, well_id=WELL_ID, start_date='2020-01-01', end_date='2020-12-31')

    assert _query(api.deleted_urls[0]) == {
        'well': [WELL_ID],
        'startDate': ['2020-01-01'],
        'endDate': ['2020-12-31'],
    }
    # The body must stay empty: the endpoint rejects a payload outright.
    assert api.deleted_bodies == [[]]
    assert headers['X-Delete-Count'] == '1'


@pytest.mark.parametrize(
    ('method', 'args'),
    [
        ('delete_company_monthly_productions', ()),
        ('delete_company_daily_productions', ()),
        ('delete_project_monthly_productions', (PROJECT_ID,)),
        ('delete_project_daily_productions', (PROJECT_ID,)),
    ],
)
def test_unfiltered_delete_is_refused(api: _RecordingProduction, method: str, args: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match='at least one'):
        getattr(api, method)(*args)

    assert api.deleted_urls == []


def test_a_single_filter_is_enough() -> None:
    assert _delete_filters(WELL_ID, None, None) == {'well': WELL_ID}
    assert _delete_filters(None, '2020-01-01', None) == {'startDate': '2020-01-01'}
    assert _delete_filters(None, None, '2020-12-31') == {'endDate': '2020-12-31'}


def test_project_url_keeps_the_project_id(api: _RecordingProduction) -> None:
    api.delete_project_monthly_productions(PROJECT_ID, well_id=WELL_ID)

    path = urlsplit(api.deleted_urls[0]).path
    assert path.endswith(f'/projects/{PROJECT_ID}/monthly-productions')
