"""Scenario run, scenario model assignments and forecast wells: verb, url, query, body and result.

These seven operations were published by ComboCurve between 2026-08 and 2026-10
(docs/todo/open/published-routes-without-a-method.md). The route paths and docs slugs are also
checked against the Postman collection by `test_route_paths.py` and `test_docstring_slugs.py`.
"""

from typing import Any, Optional

import pytest
import requests
from pytest import MonkeyPatch

from combocurve_api_helper.base import Item, ItemList
from tests.http_fakes import FakeResponse, make_offline_api

PROJECT_ID = '000000000000000000000001'
SCENARIO_ID = '000000000000000000000002'
FORECAST_ID = '000000000000000000000003'
JOB_ID = '000000000000000000000004'
WELL_ID = '000000000000000000000005'
SCENARIO_URL = f'/v1/projects/{PROJECT_ID}/scenarios/{SCENARIO_ID}'


class _Recorder:
    """Stands in for `requests.request`; answers with `response` and keeps every call."""

    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def __call__(self, method: str, url: str, headers: Any = None, params: Any = None, **keywords: Any) -> FakeResponse:
        self.calls.append({'method': method.upper(), 'url': url, 'params': params, 'json': keywords.get('json')})
        return self.response


def _install(monkeypatch: MonkeyPatch, response: FakeResponse) -> _Recorder:
    recorder = _Recorder(response)
    monkeypatch.setattr(requests, 'request', recorder)
    return recorder


# Scenario run


def test_scenario_run_urls() -> None:
    api = make_offline_api()
    assert api.get_scenario_run_url(PROJECT_ID, SCENARIO_ID).endswith(f'{SCENARIO_URL}/run')
    assert api.get_scenario_run_by_job_id_url(PROJECT_ID, SCENARIO_ID, JOB_ID).endswith(f'{SCENARIO_URL}/run/{JOB_ID}')


def test_post_scenario_run_sends_the_object_body_and_returns_the_job(monkeypatch: MonkeyPatch) -> None:
    recorder = _install(monkeypatch, FakeResponse(202, {'jobId': JOB_ID}))
    body: Item = {'runModels': 'economics_only', 'wellIds': [WELL_ID]}

    job = make_offline_api().post_scenario_run(PROJECT_ID, SCENARIO_ID, body)

    assert job == {'jobId': JOB_ID}
    assert len(recorder.calls) == 1
    assert recorder.calls[0]['method'] == 'POST'
    assert recorder.calls[0]['url'].endswith(f'{SCENARIO_URL}/run')
    assert recorder.calls[0]['json'] == body


def test_post_scenario_run_without_data_sends_an_empty_object(monkeypatch: MonkeyPatch) -> None:
    recorder = _install(monkeypatch, FakeResponse(202, {'jobId': JOB_ID}))

    make_offline_api().post_scenario_run(PROJECT_ID, SCENARIO_ID)

    assert recorder.calls[0]['json'] == {}


def test_post_scenario_run_raises_on_an_error_status(monkeypatch: MonkeyPatch) -> None:
    _install(monkeypatch, FakeResponse(400, {'message': 'bad'}))

    with pytest.raises(requests.HTTPError):
        make_offline_api().post_scenario_run(PROJECT_ID, SCENARIO_ID, {'runMode': 'nonsense'})


def test_get_scenario_run_by_job_id_returns_the_status_object(monkeypatch: MonkeyPatch) -> None:
    status: Item = {'jobId': JOB_ID, 'status': 'completed', 'result': {'econRunId': WELL_ID}}
    recorder = _install(monkeypatch, FakeResponse(200, status))

    result = make_offline_api().get_scenario_run_by_job_id(PROJECT_ID, SCENARIO_ID, JOB_ID)

    assert result == status
    assert recorder.calls[0]['method'] == 'GET'
    assert recorder.calls[0]['url'].endswith(f'{SCENARIO_URL}/run/{JOB_ID}')


# Scenario model assignments


def test_scenario_model_assignments_url_carries_the_filters() -> None:
    api = make_offline_api()
    assert api.get_scenario_model_assignments_url(PROJECT_ID, SCENARIO_ID).endswith(
        f'{SCENARIO_URL}/assignments/models'
    )
    filtered = api.get_scenario_model_assignments_url(PROJECT_ID, SCENARIO_ID, {'model': 'dates', 'wellId': WELL_ID})
    assert filtered.endswith(f'{SCENARIO_URL}/assignments/models?model=dates&wellId={WELL_ID}')


def test_get_scenario_model_assignments_takes_500_and_keeps_the_row_order(monkeypatch: MonkeyPatch) -> None:
    rows: ItemList = [
        {'wellId': 'b', 'incrementalIndex': 0, 'models': []},
        {'wellId': 'a', 'incrementalIndex': 0, 'models': []},
    ]
    recorder = _install(monkeypatch, FakeResponse(200, rows))

    result = make_offline_api().get_scenario_model_assignments(PROJECT_ID, SCENARIO_ID, {'model': 'dates'})

    assert result == rows
    assert recorder.calls[0]['method'] == 'GET'
    assert recorder.calls[0]['url'].endswith(f'{SCENARIO_URL}/assignments/models?model=dates')
    assert recorder.calls[0]['params'] == {'take': 500}


ASSIGNMENT_DATA: ItemList = [
    {'model': 'dates', 'qualifierName': 'default', 'incrementalIndex': 0, 'wellIds': [WELL_ID], 'modelId': JOB_ID}
]


@pytest.mark.parametrize(
    ('add_wells_to_forecast', 'expected_suffix'),
    [
        (None, '/assignments/models'),
        (False, '/assignments/models'),
        (True, '/assignments/models?addWellsToForecast=true'),
    ],
)
def test_put_scenario_model_assignments_url_and_body(
    monkeypatch: MonkeyPatch, add_wells_to_forecast: Optional[bool], expected_suffix: str
) -> None:
    results: ItemList = [{'status': 'OK', 'code': 200, 'wellsUpdated': 1, 'wellsFailed': 0}]
    recorder = _install(monkeypatch, FakeResponse(207, results))
    api = make_offline_api()

    if add_wells_to_forecast is None:
        written = api.put_scenario_model_assignments(PROJECT_ID, SCENARIO_ID, ASSIGNMENT_DATA)
    else:
        written = api.put_scenario_model_assignments(
            PROJECT_ID, SCENARIO_ID, ASSIGNMENT_DATA, add_wells_to_forecast=add_wells_to_forecast
        )

    assert written == results
    assert len(recorder.calls) == 1
    assert recorder.calls[0]['method'] == 'PUT'
    assert recorder.calls[0]['url'].endswith(f'{SCENARIO_URL}{expected_suffix}')
    assert recorder.calls[0]['json'] == ASSIGNMENT_DATA


def test_delete_scenario_model_assignments_sends_the_array_body(monkeypatch: MonkeyPatch) -> None:
    recorder = _install(monkeypatch, FakeResponse(204, None, headers={'X-Delete-Count': '1'}))

    headers = make_offline_api().delete_scenario_model_assignments(PROJECT_ID, SCENARIO_ID, ASSIGNMENT_DATA)

    assert headers['x-delete-count'] == '1'
    assert len(recorder.calls) == 1
    assert recorder.calls[0]['method'] == 'DELETE'
    assert recorder.calls[0]['url'].endswith(f'{SCENARIO_URL}/assignments/models')
    assert recorder.calls[0]['json'] == ASSIGNMENT_DATA


# Forecast wells


def test_forecast_wells_url_carries_the_filters() -> None:
    api = make_offline_api()
    plain = api.get_forecast_wells_url(PROJECT_ID, FORECAST_ID)
    assert plain.endswith(f'/v1/projects/{PROJECT_ID}/forecasts/{FORECAST_ID}/wells')
    assert api.get_forecast_wells_url(PROJECT_ID, FORECAST_ID, {'state': 'TX'}) == f'{plain}?state=TX'


def test_get_forecast_wells_takes_the_module_limit_and_sorts_by_well_name(monkeypatch: MonkeyPatch) -> None:
    rows: ItemList = [
        {'id': 'a', 'wellName': 'Sample Well 1', 'createdAt': 'c', 'updatedAt': 'u'},
    ]
    recorder = _install(monkeypatch, FakeResponse(200, rows))

    result = make_offline_api().get_forecast_wells(PROJECT_ID, FORECAST_ID, {'state': 'TX'})

    assert result == rows
    assert recorder.calls[0]['method'] == 'GET'
    assert recorder.calls[0]['url'].endswith(f'/forecasts/{FORECAST_ID}/wells?state=TX')
    assert recorder.calls[0]['params'] == {'take': 200}


def test_count_forecast_wells_reads_the_head_count(monkeypatch: MonkeyPatch) -> None:
    recorder = _install(monkeypatch, FakeResponse(200, None, headers={'X-Query-Count': '7'}))

    count = make_offline_api().count_forecast_wells(PROJECT_ID, FORECAST_ID, {'state': 'TX'})

    assert count == 7
    assert recorder.calls[0]['method'] == 'HEAD'
    assert recorder.calls[0]['url'].endswith(f'/forecasts/{FORECAST_ID}/wells?state=TX')


def test_post_forecast_wells_still_posts_to_the_unfiltered_url(monkeypatch: MonkeyPatch) -> None:
    recorder = _install(monkeypatch, FakeResponse(200, [{'id': 'x'}]))

    make_offline_api().post_forecast_wells(PROJECT_ID, FORECAST_ID, [WELL_ID])

    assert recorder.calls[0]['url'].endswith(f'/forecasts/{FORECAST_ID}/wells')
    assert recorder.calls[0]['json'] == {'wellIds': [WELL_ID]}
