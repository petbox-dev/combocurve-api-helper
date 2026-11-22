"""Offline tests for the per-forecast read of the root volume listings -- no live API.

ComboCurve's root volume listing filtered by `project` alone repeats and drops (forecast, well) rows above
one page, and can end early on a short page, while its count stays right (dev 2026-11-21;
`docs/todo/open/project-scoped-root-volumes-repeat-and-drop-rows.md`). The `forecast` scope was exact on
every dev forecast. So `get_root_forecast_{daily,monthly}_volumes` read a `project` scope one forecast at a
time and check the total against the project count.
"""

from collections.abc import Callable, Mapping
from typing import Optional
from urllib.parse import parse_qs

import pytest
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI, ItemList
from combocurve_api_helper.base import QueryFilters
from tests.http_fakes import (
    V1,
    FakeResponse,
    RecordedCall,
    RecordingTransport,
    install_responding_transport,
    make_offline_api,
)

ListVolumes = Callable[[ComboCurveAPI, Optional[QueryFilters]], ItemList]

GETTERS: list[tuple[str, ListVolumes]] = [
    ('forecast-monthly-volumes', ComboCurveAPI.get_root_forecast_monthly_volumes),
    ('forecast-daily-volumes', ComboCurveAPI.get_root_forecast_daily_volumes),
]

# The forecast list arrives as B, A; `get_forecasts` sorts it by name, so the reads go A (`F2`), then B (`F1`).
FORECASTS: ItemList = [
    {'createdAt': '2020-01-01', 'id': 'F1', 'name': 'Forecast B', 'updatedAt': '2020-01-01'},
    {'createdAt': '2020-01-01', 'id': 'F2', 'name': 'Forecast A', 'updatedAt': '2020-01-01'},
]
ROWS_BY_FORECAST: Mapping[str, ItemList] = {
    'F1': [{'forecast': 'F1', 'well': 'W1'}, {'forecast': 'F1', 'well': 'W2'}],
    'F2': [{'forecast': 'F2', 'well': 'W1'}, {'forecast': 'F2', 'well': 'W3'}, {'forecast': 'F2', 'well': 'W4'}],
}


def _install_project(monkeypatch: MonkeyPatch, project_count: int) -> RecordingTransport:
    """Answer the project count (HEAD), the forecast list of project `P`, and each forecast-scoped listing,
    filtered by its `well` values when it carries any."""

    def respond(call: RecordedCall) -> FakeResponse:
        if call.method == 'HEAD':
            return FakeResponse(200, None, headers={'X-Query-Count': str(project_count)})
        path, _, query = call.url.partition('?')
        if path == f'{V1}/projects/P/forecasts':
            return FakeResponse(200, FORECASTS)
        query_values = parse_qs(query)
        rows = ROWS_BY_FORECAST[query_values['forecast'][0]]
        wells = query_values.get('well')
        return FakeResponse(200, [row for row in rows if wells is None or row['well'] in wells])

    return install_responding_transport(monkeypatch, respond)


@pytest.mark.parametrize(('route', 'list_volumes'), GETTERS)
def test_project_scope_is_read_one_forecast_at_a_time(
    monkeypatch: MonkeyPatch, route: str, list_volumes: ListVolumes
) -> None:
    transport = _install_project(monkeypatch, project_count=5)

    rows = list_volumes(make_offline_api(), {'project': 'P'})

    assert [(row['forecast'], row['well']) for row in rows] == [
        ('F2', 'W1'),
        ('F2', 'W3'),
        ('F2', 'W4'),
        ('F1', 'W1'),
        ('F1', 'W2'),
    ]
    assert transport.methods_and_urls == [
        ('HEAD', f'{V1}/{route}?project=P'),
        ('GET', f'{V1}/projects/P/forecasts'),
        ('GET', f'{V1}/{route}?forecast=F2'),
        ('GET', f'{V1}/{route}?forecast=F1'),
    ]
    assert [call.params for call in transport.calls[1:]] == [{'take': 200}] * 3


@pytest.mark.parametrize(('route', 'list_volumes'), GETTERS)
def test_a_row_total_that_differs_from_the_count_raises(
    monkeypatch: MonkeyPatch, route: str, list_volumes: ListVolumes
) -> None:
    _install_project(monkeypatch, project_count=6)

    with pytest.raises(RuntimeError, match='returned 5 volume rows, but the project count is 6'):
        list_volumes(make_offline_api(), {'project': 'P'})


@pytest.mark.parametrize(('route', 'list_volumes'), GETTERS)
@pytest.mark.parametrize('filters', [{'project': 'P'}, {'project': 'P', 'well': ['W1', 'W2', 'W3']}])
def test_a_repeated_pair_raises_even_when_the_total_matches(
    monkeypatch: MonkeyPatch, route: str, list_volumes: ListVolumes, filters: QueryFilters
) -> None:
    """The server defect repeats some (forecast, well) pairs and drops as many others, so a total equal to the
    count proves nothing: one row per pair is checked too, also on a narrowed read (which has no count)."""
    repeated = {'F1': [{'forecast': 'F1', 'well': 'W1'}, {'forecast': 'F1', 'well': 'W1'}]}
    monkeypatch.setattr(f'{__name__}.ROWS_BY_FORECAST', {**ROWS_BY_FORECAST, **repeated})
    _install_project(monkeypatch, project_count=5)

    with pytest.raises(RuntimeError, match=r"repeats the \(forecast, well\) pair \('F1', 'W1'\)"):
        list_volumes(make_offline_api(), filters)


@pytest.mark.parametrize(('route', 'list_volumes'), GETTERS)
def test_take_keeps_the_count_check(monkeypatch: MonkeyPatch, route: str, list_volumes: ListVolumes) -> None:
    """`take` is a page size, not a narrowing filter: the count is still sent and checked."""
    transport = _install_project(monkeypatch, project_count=4)

    with pytest.raises(RuntimeError, match='returned 5 volume rows, but the project count is 4'):
        list_volumes(make_offline_api(), {'project': 'P', 'take': 50})

    assert transport.methods_and_urls[0] == ('HEAD', f'{V1}/{route}?project=P')
    assert transport.methods_and_urls[2] == ('GET', f'{V1}/{route}?take=50&forecast=F2')


@pytest.mark.parametrize(('route', 'list_volumes'), GETTERS)
def test_well_with_project_is_read_per_forecast_without_the_count(
    monkeypatch: MonkeyPatch, route: str, list_volumes: ListVolumes
) -> None:
    """`well` with `project` is refused by the API, so it goes out with each `forecast` instead. The project
    count does not apply to the narrowed rows, so it is not sent (the count of 999 would fail the check)."""
    transport = _install_project(monkeypatch, project_count=999)

    rows = list_volumes(make_offline_api(), {'project': 'P', 'well': ['W1', 'W2']})

    assert [(row['forecast'], row['well']) for row in rows] == [('F2', 'W1'), ('F1', 'W1'), ('F1', 'W2')]
    assert transport.methods_and_urls == [
        ('GET', f'{V1}/projects/P/forecasts'),
        ('GET', f'{V1}/{route}?well=W1&well=W2&forecast=F2'),
        ('GET', f'{V1}/{route}?well=W1&well=W2&forecast=F1'),
    ]


@pytest.mark.parametrize(('route', 'list_volumes'), GETTERS)
@pytest.mark.parametrize('narrowing', [{'startDate': '2025-01-01'}, {'endDate': '2030-01-01'}])
def test_a_narrowing_filter_skips_the_count_check(
    monkeypatch: MonkeyPatch, route: str, list_volumes: ListVolumes, narrowing: dict[str, str]
) -> None:
    transport = _install_project(monkeypatch, project_count=999)

    rows = list_volumes(make_offline_api(), {'project': 'P', **narrowing})

    assert len(rows) == 5
    assert 'HEAD' not in [method for method, _ in transport.methods_and_urls]


@pytest.mark.parametrize(('route', 'list_volumes'), GETTERS)
def test_a_large_well_list_is_split_per_forecast(
    monkeypatch: MonkeyPatch, route: str, list_volumes: ListVolumes
) -> None:
    """The 100-well split (`_get_items_in_value_batches`) applies inside each forecast."""
    transport = _install_project(monkeypatch, project_count=999)
    wells = ['W1', *[f'X{i}' for i in range(150)]]

    list_volumes(make_offline_api(), {'project': 'P', 'well': wells})

    listing_calls = [call for call in transport.calls if call.url.startswith(f'{V1}/{route}')]
    assert [parse_qs(call.url.partition('?')[2])['forecast'][0] for call in listing_calls] == ['F2', 'F2', 'F1', 'F1']
    assert [len(parse_qs(call.url.partition('?')[2])['well']) for call in listing_calls] == [100, 51, 100, 51]


@pytest.mark.parametrize(('route', 'list_volumes'), GETTERS)
def test_forecast_scope_is_one_listing_as_before(
    monkeypatch: MonkeyPatch, route: str, list_volumes: ListVolumes
) -> None:
    """With `forecast` (with or without `project`) nothing is listed or counted first."""
    transport = _install_project(monkeypatch, project_count=999)

    rows = list_volumes(make_offline_api(), {'project': 'P', 'forecast': 'F1'})

    assert len(rows) == 2
    assert transport.methods_and_urls == [('GET', f'{V1}/{route}?project=P&forecast=F1')]


@pytest.mark.parametrize(('route', 'list_volumes'), GETTERS)
@pytest.mark.parametrize('paging', [{'skip': 10}, {'skip': '5'}, {'cursor': 'C'}])
def test_paging_filters_are_refused_with_the_project_scope(
    monkeypatch: MonkeyPatch, route: str, list_volumes: ListVolumes, paging: dict[str, object]
) -> None:
    transport = _install_project(monkeypatch, project_count=5)

    with pytest.raises(ValueError, match='project-scoped root volume read'):
        list_volumes(make_offline_api(), {'project': 'P', **paging})  # type: ignore[dict-item]

    assert transport.calls == []


@pytest.mark.parametrize(('route', 'list_volumes'), GETTERS)
def test_a_skip_of_zero_is_not_refused(monkeypatch: MonkeyPatch, route: str, list_volumes: ListVolumes) -> None:
    _install_project(monkeypatch, project_count=5)

    assert len(list_volumes(make_offline_api(), {'project': 'P', 'skip': 0})) == 5


@pytest.mark.parametrize(('route', 'list_volumes'), GETTERS)
def test_a_project_list_is_refused(monkeypatch: MonkeyPatch, route: str, list_volumes: ListVolumes) -> None:
    transport = _install_project(monkeypatch, project_count=5)

    with pytest.raises(ValueError, match='one project id string'):
        list_volumes(make_offline_api(), {'project': ['P', 'Q']})

    assert transport.calls == []


@pytest.mark.parametrize(
    ('route', 'count_volumes'),
    [
        ('forecast-monthly-volumes', ComboCurveAPI.count_root_forecast_monthly_volumes),
        ('forecast-daily-volumes', ComboCurveAPI.count_root_forecast_daily_volumes),
    ],
)
def test_the_project_count_is_one_head_as_before(
    monkeypatch: MonkeyPatch, route: str, count_volumes: Callable[[ComboCurveAPI, Optional[QueryFilters]], int]
) -> None:
    transport = _install_project(monkeypatch, project_count=5)

    assert count_volumes(make_offline_api(), {'project': 'P'}) == 5
    assert transport.methods_and_urls == [('HEAD', f'{V1}/{route}?project=P')]


@pytest.mark.parametrize(('route', 'list_volumes'), GETTERS)
def test_a_well_named_twice_is_requested_once_per_forecast(
    monkeypatch: MonkeyPatch, route: str, list_volumes: ListVolumes
) -> None:
    """A repeated well id would read its rows twice, which the repeated-pair check reads as the server defect."""
    transport = _install_project(monkeypatch, project_count=5)

    list_volumes(make_offline_api(), {'project': 'P', 'well': ['W1', 'W1']})

    listings = [call.url for call in transport.calls if call.url.startswith(f'{V1}/{route}')]
    assert [parse_qs(url.partition('?')[2])['well'] for url in listings] == [['W1'], ['W1']]
