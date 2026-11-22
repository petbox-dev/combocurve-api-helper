"""`QueryFilters`, the two call sites that used to build their urls by hand, and the single-object requests.

No live call: every request goes through a recording transport.
"""

import warnings
from urllib.parse import parse_qsl, urlsplit

from pytest import MonkeyPatch

from combocurve_api_helper import type_curves_v1_compatibility
from combocurve_api_helper.base import WELL_FILTER_LIMIT, APIBase, QueryFilters, WellFilters
from combocurve_api_helper.forecasts import GET_LIMIT_OUTPUTS_ARIES
from tests.http_fakes import V1, V2, FakeResponse, install_recording_transport, make_offline_api

PROJECT_ID = 'a' * 24
FORECAST_ID = 'b' * 24
SCENARIO_ID = 'c' * 24


def well_ids(count: int) -> list[str]:
    """`count` distinct 24-hex ObjectId-like strings."""
    return [f'{index:024x}' for index in range(1, count + 1)]


def query_pairs(url: str) -> list[tuple[str, str]]:
    """The query of `url` as (key, value) pairs, in the order sent."""
    return parse_qsl(urlsplit(url).query)


# QueryFilters


def test_well_filters_is_the_query_filters_alias() -> None:
    assert WellFilters is QueryFilters


def test_query_filters_render_strings_ints_sequences_and_drop_none() -> None:
    filters: QueryFilters = {'take': 50, 'skip': '10', 'well': ['w1', 'w2'], 'cursor': None}

    assert APIBase._build_params_string(filters) == '?take=50&skip=10&well=w1&well=w2'


def test_an_int_filter_value_is_one_batch() -> None:
    filters: QueryFilters = {'well': 'w1', 'take': 50}

    assert APIBase._filter_value_batches(filters, 'take') == [filters]


def test_econ_settings_take_an_int_take(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, []))

    make_offline_api().get_econ_settings({'take': 5, 'skip': 0})

    assert query_pairs(recorder.calls[0].url) == [('take', '5'), ('skip', '0')]


def test_widened_builders_repeat_a_sequence_value() -> None:
    api = make_offline_api()

    econ_model_grid = api.get_scenario_econ_model_assignments_url(PROJECT_ID, SCENARIO_ID, {'wellId': ['w1', 'w2']})
    type_curves = api.get_type_curves_url(PROJECT_ID, {'id': ['t1', 't2']})

    assert econ_model_grid == (
        f'{V1}/projects/{PROJECT_ID}/scenarios/{SCENARIO_ID}/assignments/econ-models?wellId=w1&wellId=w2'
    )
    assert type_curves == f'{V2}/projects/{PROJECT_ID}/type-curves?id=t1&id=t2'


# The two sites that bypassed their builders


def test_delete_scenario_qualifiers_sends_the_qualifiers_builder_url(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(204, headers={'X-Delete-Count': '1'}))

    headers = make_offline_api().delete_scenario_qualifiers(PROJECT_ID, SCENARIO_ID, 'capex,pricing', 'Seller Case')

    assert recorder.methods_and_urls == [
        (
            'DELETE',
            f'{V1}/projects/{PROJECT_ID}/scenarios/{SCENARIO_ID}/qualifiers'
            '?econNames=capex,pricing&qualifierNames=Seller%20Case',
        )
    ]
    assert headers['X-Delete-Count'] == '1'


def test_compatibility_forecast_outputs_use_the_builder_and_the_forecasts_page_size(
    monkeypatch: MonkeyPatch,
) -> None:
    wells = well_ids(WELL_FILTER_LIMIT + 1)
    recorder = install_recording_transport(
        monkeypatch, FakeResponse(200, [{'id': 'o1'}]), FakeResponse(200, [{'id': 'o2'}])
    )

    outputs = make_offline_api()._forecast_outputs_for_wells(PROJECT_ID, FORECAST_ID, wells)

    outputs_url = f'{V1}/projects/{PROJECT_ID}/forecasts/{FORECAST_ID}/outputs?'
    assert [call_.method for call_ in recorder.calls] == ['GET', 'GET']
    assert all(call_.url.startswith(outputs_url) for call_ in recorder.calls)
    assert [[value for key, value in query_pairs(call_.url) if key == 'well'] for call_ in recorder.calls] == [
        wells[:WELL_FILTER_LIMIT],
        wells[WELL_FILTER_LIMIT:],
    ]
    assert [call_.params for call_ in recorder.calls] == [{'take': GET_LIMIT_OUTPUTS_ARIES}] * 2
    assert [output['id'] for output in outputs] == ['o1', 'o2']


def test_compatibility_forecast_outputs_send_nothing_for_no_wells(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch)

    assert make_offline_api()._forecast_outputs_for_wells(PROJECT_ID, FORECAST_ID, []) == []
    assert recorder.calls == []


def test_compatibility_page_size_names_stay_bound() -> None:
    assert type_curves_v1_compatibility.FORECAST_OUTPUTS_GET_LIMIT == GET_LIMIT_OUTPUTS_ARIES == 1000
    assert type_curves_v1_compatibility.FORECAST_OUTPUTS_WELLS_PER_REQUEST == WELL_FILTER_LIMIT


# Single-object requests through `_send_for_item`


def test_single_object_writes_send_one_request_and_return_the_object(monkeypatch: MonkeyPatch) -> None:
    survey_id = 'd' * 24
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, {'chosenID': 'one'}),
        FakeResponse(200, {'chosenID': 'two'}),
        FakeResponse(200, {'name': 'renamed'}),
        FakeResponse(200, {'productionCommentTypes': []}),
    )
    api = make_offline_api()

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        created = api.post_directional_surveys({'chosenID': 'one'})
        replaced = api.put_directional_survey_by_id(survey_id, {'dataSource': 'other'})
        patched = api.patch_forecast_by_id(PROJECT_ID, FORECAST_ID, {'name': 'renamed'})
        comment_types = api.patch_production_comment_types(
            [{'key': 'prod_comment_type_0', 'label': 'Label', 'color': '#000000'}]
        )

    assert [(call_.method, call_.body) for call_ in recorder.calls] == [
        ('POST', {'chosenID': 'one'}),
        ('PUT', {'dataSource': 'other'}),
        ('PATCH', {'name': 'renamed'}),
        ('PATCH', {'productionCommentTypes': [{'key': 'prod_comment_type_0', 'label': 'Label', 'color': '#000000'}]}),
    ]
    assert recorder.calls[1].url.endswith(f'/directional-surveys/{survey_id}')
    assert recorder.calls[2].url == f'{V1}/projects/{PROJECT_ID}/forecasts/{FORECAST_ID}'
    assert (created, replaced, patched, comment_types) == (
        {'chosenID': 'one'},
        {'chosenID': 'two'},
        {'name': 'renamed'},
        {'productionCommentTypes': []},
    )
