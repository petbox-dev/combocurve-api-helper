"""A `well` list longer than the API's 100-value limit is split into requests and recombined.

The monthly and daily production routes accept at most 100 repeated `well` values per request (verified
live 2026-11-20 on dev). These tests drive the batching through a recording transport, so no live call is
made.
"""

from collections.abc import Callable

import pytest
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI, ItemList
from combocurve_api_helper.base import WELL_FILTER_LIMIT
from tests.http_fakes import V1, FakeResponse, install_recording_transport, make_offline_api, object_ids, values_in

PROJECT_ID = 'a' * 24
COMPANY_MONTHLY_URL = f'{V1}/monthly-productions'
COMPANY_DAILY_URL = f'{V1}/daily-productions'
PROJECT_MONTHLY_URL = f'{V1}/projects/{PROJECT_ID}/monthly-productions'
PROJECT_DAILY_URL = f'{V1}/projects/{PROJECT_ID}/daily-productions'


GetMethod = Callable[[ComboCurveAPI, list[str]], ItemList]
COUNT_METHODS: list[tuple[str, str, Callable[[ComboCurveAPI, list[str]], int]]] = [
    ('company monthly', COMPANY_MONTHLY_URL, lambda api, wells: api.count_company_monthly_productions({'well': wells})),
    ('company daily', COMPANY_DAILY_URL, lambda api, wells: api.count_company_daily_productions({'well': wells})),
    (
        'project monthly',
        PROJECT_MONTHLY_URL,
        lambda api, wells: api.count_project_monthly_productions(PROJECT_ID, {'well': wells}),
    ),
    (
        'project daily',
        PROJECT_DAILY_URL,
        lambda api, wells: api.count_project_daily_productions(PROJECT_ID, {'well': wells}),
    ),
]
GET_METHODS: list[tuple[str, str, GetMethod]] = [
    ('company monthly', COMPANY_MONTHLY_URL, lambda api, wells: api.get_company_monthly_productions({'well': wells})),
    ('company daily', COMPANY_DAILY_URL, lambda api, wells: api.get_company_daily_productions({'well': wells})),
    (
        'project monthly',
        PROJECT_MONTHLY_URL,
        lambda api, wells: api.get_project_monthly_productions(PROJECT_ID, {'well': wells}),
    ),
    (
        'project daily',
        PROJECT_DAILY_URL,
        lambda api, wells: api.get_project_daily_productions(PROJECT_ID, {'well': wells}),
    ),
]


def test_limit_is_the_verified_100() -> None:
    assert WELL_FILTER_LIMIT == 100


@pytest.mark.parametrize(('label', 'base_url', 'call'), GET_METHODS, ids=[entry[0] for entry in GET_METHODS])
def test_list_over_the_limit_is_split_and_the_rows_combined(
    monkeypatch: MonkeyPatch, label: str, base_url: str, call: GetMethod
) -> None:
    wells = object_ids(250)
    rows_per_batch = [[{'well': wells[0], 'date': '2020-02-01'}], [{'well': wells[100], 'date': '2020-01-01'}], []]
    recorder = install_recording_transport(monkeypatch, *(FakeResponse(200, rows) for rows in rows_per_batch))
    api = make_offline_api()

    result = call(api, wells)

    assert [len(values_in(call_.url, 'well')) for call_ in recorder.calls] == [100, 100, 50]
    assert [values_in(call_.url, 'well') for call_ in recorder.calls] == [wells[0:100], wells[100:200], wells[200:250]]
    assert all(call_.url.startswith(base_url + '?') for call_ in recorder.calls)
    assert all(call_.method == 'GET' for call_ in recorder.calls)
    # The rows of every batch come back as one list, sorted by well then date.
    assert [(row['well'], row['date']) for row in result] == [
        (wells[0], '2020-02-01'),
        (wells[100], '2020-01-01'),
    ]


@pytest.mark.parametrize(('label', 'base_url', 'call'), GET_METHODS, ids=[entry[0] for entry in GET_METHODS])
def test_list_at_the_limit_is_one_request(monkeypatch: MonkeyPatch, label: str, base_url: str, call: GetMethod) -> None:
    wells = object_ids(WELL_FILTER_LIMIT)
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, []))
    api = make_offline_api()

    call(api, wells)

    assert len(recorder.calls) == 1
    assert values_in(recorder.calls[0].url, 'well') == wells


def test_repeated_ids_are_dropped_before_batching(monkeypatch: MonkeyPatch) -> None:
    wells = object_ids(120)
    repeated = wells + wells[:30]  # 150 entries, 120 distinct
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, []), FakeResponse(200, []))
    api = make_offline_api()

    api.get_company_monthly_productions({'well': repeated})

    assert [values_in(call_.url, 'well') for call_ in recorder.calls] == [wells[0:100], wells[100:120]]


def test_other_filters_are_kept_on_every_batch(monkeypatch: MonkeyPatch) -> None:
    wells = object_ids(101)
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, []), FakeResponse(200, []))
    api = make_offline_api()

    api.get_company_monthly_productions({'well': wells, 'date[gt]': '2020-01-01'})

    assert all('2020-01-01' in call_.url for call_ in recorder.calls)
    assert [len(values_in(call_.url, 'well')) for call_ in recorder.calls] == [100, 1]


def test_a_single_well_string_is_one_request(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, []))
    api = make_offline_api()

    api.get_company_monthly_productions({'well': 'b' * 24})

    assert [call_.url for call_ in recorder.calls] == [f'{COMPANY_MONTHLY_URL}?well={"b" * 24}']


@pytest.mark.parametrize(('label', 'base_url', 'count'), COUNT_METHODS, ids=[entry[0] for entry in COUNT_METHODS])
def test_count_over_the_limit_sums_the_batches(
    monkeypatch: MonkeyPatch,
    label: str,
    base_url: str,
    count: Callable[[ComboCurveAPI, list[str]], int],
) -> None:
    wells = object_ids(250)
    recorder = install_recording_transport(
        monkeypatch,
        *(FakeResponse(200, headers={'X-Query-Count': str(total)}) for total in (5, 6, 7)),
    )
    api = make_offline_api()

    assert count(api, wells) == 18
    assert [call_.method for call_ in recorder.calls] == ['HEAD', 'HEAD', 'HEAD']
    assert [len(values_in(call_.url, 'well')) for call_ in recorder.calls] == [100, 100, 50]


FORECAST_ID = 'b' * 24
SCENARIO_ID = 'c' * 24
FORECAST_OUTPUTS_URL = f'{V1}/projects/{PROJECT_ID}/forecasts/{FORECAST_ID}/outputs'
SCENARIO_MODEL_ASSIGNMENTS_URL = f'{V1}/projects/{PROJECT_ID}/scenarios/{SCENARIO_ID}/assignments/models'


def test_forecast_outputs_list_over_the_limit_is_split_and_combined(monkeypatch: MonkeyPatch) -> None:
    wells = object_ids(150)
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, [{'well': wells[0], 'id': 'o1'}]),
        FakeResponse(200, [{'well': wells[120], 'id': 'o2'}]),
    )
    api = make_offline_api()

    outputs = api.get_forecast_outputs(PROJECT_ID, FORECAST_ID, {'well': wells})

    assert [values_in(call_.url, 'well') for call_ in recorder.calls] == [wells[0:100], wells[100:150]]
    assert all(call_.url.startswith(FORECAST_OUTPUTS_URL + '?') for call_ in recorder.calls)
    assert [output['id'] for output in outputs] == ['o1', 'o2']


def test_forecast_outputs_count_over_the_limit_sums_the_batches(monkeypatch: MonkeyPatch) -> None:
    wells = object_ids(150)
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, headers={'X-Query-Count': '4'}),
        FakeResponse(200, headers={'X-Query-Count': '9'}),
    )
    api = make_offline_api()

    assert api.count_forecast_outputs(PROJECT_ID, FORECAST_ID, {'well': wells}) == 13
    assert [call_.method for call_ in recorder.calls] == ['HEAD', 'HEAD']


def test_scenario_model_assignments_split_on_wellid_in_request_order(monkeypatch: MonkeyPatch) -> None:
    wells = object_ids(101)
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, [{'wellId': wells[0]}]),
        FakeResponse(200, [{'wellId': wells[100]}]),
    )
    api = make_offline_api()

    rows = api.get_scenario_model_assignments(PROJECT_ID, SCENARIO_ID, {'wellId': wells})

    assert [values_in(call_.url, 'wellId') for call_ in recorder.calls] == [wells[0:100], wells[100:101]]
    assert all(call_.url.startswith(SCENARIO_MODEL_ASSIGNMENTS_URL + '?') for call_ in recorder.calls)
    assert [row['wellId'] for row in rows] == [wells[0], wells[100]]


def test_scenario_model_assignments_keeps_a_non_list_filter_as_one_request(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, []))
    api = make_offline_api()

    api.get_scenario_model_assignments(PROJECT_ID, SCENARIO_ID, {'model': 'forecast'})

    assert [call_.url for call_ in recorder.calls] == [f'{SCENARIO_MODEL_ASSIGNMENTS_URL}?model=forecast']


FORECAST_DAILY_VOLUMES_URL = f'{V1}/projects/{PROJECT_ID}/forecasts/{FORECAST_ID}/daily-volumes'
ROOT_DAILY_VOLUMES_URL = f'{V1}/forecast-daily-volumes'


def test_forecast_daily_volumes_split_and_sorted_by_well(monkeypatch: MonkeyPatch) -> None:
    wells = object_ids(150)
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, [{'well': wells[120], 'resolution': 'daily'}]),
        FakeResponse(200, [{'well': wells[0], 'resolution': 'daily'}]),
    )
    api = make_offline_api()

    volumes = api.get_forecast_daily_volumes(PROJECT_ID, FORECAST_ID, {'well': wells})

    assert [values_in(call_.url, 'well') for call_ in recorder.calls] == [wells[0:100], wells[100:150]]
    assert all(call_.url.startswith(FORECAST_DAILY_VOLUMES_URL + '?') for call_ in recorder.calls)
    assert [volume['well'] for volume in volumes] == [wells[0], wells[120]]


def test_forecast_monthly_volumes_count_over_the_limit_sums_the_batches(monkeypatch: MonkeyPatch) -> None:
    wells = object_ids(150)
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, headers={'X-Query-Count': '3'}),
        FakeResponse(200, headers={'X-Query-Count': '5'}),
    )
    api = make_offline_api()

    assert api.count_forecast_monthly_volumes(PROJECT_ID, FORECAST_ID, {'well': wells}) == 8
    assert [call_.method for call_ in recorder.calls] == ['HEAD', 'HEAD']


def test_root_daily_volumes_keep_forecast_on_every_batch(monkeypatch: MonkeyPatch) -> None:
    wells = object_ids(101)
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, []), FakeResponse(200, []))
    api = make_offline_api()

    api.get_root_forecast_daily_volumes({'forecast': FORECAST_ID, 'well': wells})

    assert [values_in(call_.url, 'well') for call_ in recorder.calls] == [wells[0:100], wells[100:101]]
    assert all(call_.url.startswith(ROOT_DAILY_VOLUMES_URL + f'?forecast={FORECAST_ID}') for call_ in recorder.calls)


def test_root_monthly_volumes_count_over_the_limit_sums_the_batches(monkeypatch: MonkeyPatch) -> None:
    wells = object_ids(150)
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, headers={'X-Query-Count': '4'}),
        FakeResponse(200, headers={'X-Query-Count': '6'}),
    )
    api = make_offline_api()

    assert api.count_root_forecast_monthly_volumes({'forecast': FORECAST_ID, 'well': wells}) == 10
    assert [call_.method for call_ in recorder.calls] == ['HEAD', 'HEAD']


def test_root_volumes_still_refuse_an_unscoped_filter(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch)
    api = make_offline_api()

    with pytest.raises(ValueError, match='filters must include at least one of'):
        api.get_root_forecast_daily_volumes({'startDate': '2020-01-01'})
    assert recorder.calls == []
