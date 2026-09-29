from typing import Any

import pytest

from combocurve_api_helper.econ_models import MAPPERS, get_mapper
from combocurve_api_helper.econ_models.actual_or_forecast import ActualOrForecastMapper
from combocurve_api_helper.econ_models.base import Context


def _no_timestamp(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """'Last Update' is sourced from the API model's updatedAt/context, never
    reconstructed by from_row_dicts (same convention as every other mapper -- see
    test_fixtures.py's compare_cols = mapper.columns[3:-1]). Round-trip comparisons
    below drop it so they compare only the model-parameter columns.
    """
    return [{k: v for k, v in r.items() if k != 'Last Update'} for r in rows]


# Real, FULL API shapes. 'Actual' and 'Forecast As Of' are the two fixed,
# non-deletable built-in model names for this econ-model type (ported from
# cc-afe-sync's ACTUAL_OR_FORECAST_ASSIGNMENTS) -- both still legacy `{}`-shaped,
# never migrated to the explicit per-phase form.
ACTUAL_LEGACY_EMPTY: dict[str, Any] = {
    'id': '000000000000000000000002',
    'name': 'Actual',
    'unique': False,
    'createdAt': '2021-07-12T17:41:11.443Z',
    'updatedAt': '2021-07-12T17:41:11.443Z',
    'econModelType': 'ActualOrForecast',
    'actualOrForecast': {},
}

FORECAST_AS_OF_LEGACY_EMPTY: dict[str, Any] = {
    'id': '000000000000000000000003',
    'name': 'Forecast As Of',
    'unique': False,
    'createdAt': '2021-07-12T23:04:01.503Z',
    'updatedAt': '2025-01-07T20:01:18.969Z',
    'econModelType': 'ActualOrForecast',
    'actualOrForecast': {},
}

IGNORE_HISTORY: dict[str, Any] = {
    'id': '000000000000000000000008',
    'name': 'Ignore History',
    'unique': False,
    'createdAt': '2022-07-07T17:58:24.021Z',
    'updatedAt': '2022-07-07T17:58:26.531Z',
    'econModelType': 'ActualOrForecast',
    'actualOrForecast': {'ignoreHistoryProd': True},
}

FORECAST_ONLY_IGNORE_HIST_PROD: dict[str, Any] = {
    'id': '000000000000000000000014',
    'name': 'Forecast Only',
    'unique': False,
    'createdAt': '2024-12-09T22:16:39.000Z',
    'updatedAt': '2024-12-09T22:16:39.000Z',
    'econModelType': 'ActualOrForecast',
    # Verified live 2026-09-29 against the ComboCurve screen: all three rows read "Ignore Hist Prod".
    'actualOrForecast': {
        'ignoreHistoryProd': False,
        'replaceActualWithForecast': {'oil': {}, 'gas': {}, 'water': {}},
    },
}

FORECAST_JULY_24: dict[str, Any] = {
    'id': '000000000000000000000013',
    'name': "Forecast July '24",
    'unique': False,
    'createdAt': '2024-09-19T00:39:44.879Z',
    'updatedAt': '2024-09-19T00:49:09.171Z',
    'econModelType': 'ActualOrForecast',
    'actualOrForecast': {
        'ignoreHistoryProd': False,
        'replaceActualWithForecast': {
            'oil': {'date': '2024-06-30'},
            'gas': {'date': '2024-06-30'},
            'water': {'date': '2024-06-30'},
        },
    },
}

# Explicit modern shape for the built-ins: once migrated, 'Actual' carries explicit
# {"never": true} and 'Forecast As Of' carries explicit {"asOfDate": true} per phase.
ACTUAL_MODERN_EXPLICIT: dict[str, Any] = {
    'id': '000000000000000000000010',
    'name': 'Actual',
    'unique': False,
    'createdAt': '2022-12-06T15:46:11.964Z',
    'updatedAt': '2022-12-06T15:46:11.964Z',
    'econModelType': 'ActualOrForecast',
    'actualOrForecast': {
        'ignoreHistoryProd': False,
        'replaceActualWithForecast': {
            'oil': {'never': True},
            'gas': {'never': True},
            'water': {'never': True},
        },
    },
}

FORECAST_AS_OF_MODERN_EXPLICIT: dict[str, Any] = {
    'id': '000000000000000000000009',
    'name': 'Forecast As Of',
    'unique': False,
    'createdAt': '2022-12-06T15:45:57.294Z',
    'updatedAt': '2026-04-28T17:03:21.738Z',
    'econModelType': 'ActualOrForecast',
    'actualOrForecast': {
        'ignoreHistoryProd': False,
        'replaceActualWithForecast': {
            'oil': {'asOfDate': True},
            'gas': {'asOfDate': True},
            'water': {'asOfDate': True},
        },
    },
}


def test_to_row_dicts_emits_exactly_3_rows() -> None:
    rows = ActualOrForecastMapper().to_row_dicts(FORECAST_JULY_24)
    assert len(rows) == 3
    assert [r['Key'] for r in rows] == ['oil', 'gas', 'water']


def test_forward_empty_actual_model_is_never() -> None:
    rows = ActualOrForecastMapper().to_row_dicts(ACTUAL_LEGACY_EMPTY)
    assert len(rows) == 3
    for r in rows:
        assert r['Category'] == ''
        assert r['Criteria'] == 'Never'
        assert r['Value'] == ''


def test_forward_empty_forecast_as_of_model_is_as_of_date() -> None:
    # The built-in 'Forecast As Of' model resolves its legacy empty `{}` shape to
    # "As of Date", NOT "Never" -- name-keyed fallback.
    rows = ActualOrForecastMapper().to_row_dicts(FORECAST_AS_OF_LEGACY_EMPTY)
    assert len(rows) == 3
    for r in rows:
        assert r['Criteria'] == 'As of Date'
        assert r['Value'] == ''


def test_forward_model_level_ignore_history_flag_is_ignore_hist_prod() -> None:
    # actualOrForecast carries ONLY ignoreHistoryProd (no replaceActualWithForecast
    # at all); the flag reads as Ignore Hist Prod on every phase.
    rows = ActualOrForecastMapper().to_row_dicts(IGNORE_HISTORY)
    for r in rows:
        assert r['Criteria'] == 'Ignore Hist Prod'
        assert r['Value'] == ''


def test_forward_date_switch_iso_passthrough() -> None:
    rows = ActualOrForecastMapper().to_row_dicts(FORECAST_JULY_24)
    for r in rows:
        assert r['Criteria'] == 'Date'
        # ISO date is passed through UNCHANGED -- not reformatted to MM/DD/YYYY.
        assert r['Value'] == '2024-06-30'


def test_forward_modern_explicit_never_and_as_of_date() -> None:
    rows = ActualOrForecastMapper().to_row_dicts(ACTUAL_MODERN_EXPLICIT)
    for r in rows:
        assert r['Criteria'] == 'Never'
        assert r['Value'] == ''

    rows = ActualOrForecastMapper().to_row_dicts(FORECAST_AS_OF_MODERN_EXPLICIT)
    for r in rows:
        assert r['Criteria'] == 'As of Date'
        assert r['Value'] == ''


def test_to_row_dicts_includes_common_columns_with_context() -> None:
    ctx = Context(id=FORECAST_JULY_24['id'], created_at=FORECAST_JULY_24['createdAt'], project_name='Sample Project A')
    rows = ActualOrForecastMapper().to_row_dicts(FORECAST_JULY_24, context=ctx)
    assert rows[0]['Model Id'] == FORECAST_JULY_24['id']
    assert rows[0]['Project Name'] == 'Sample Project A'
    assert rows[0]['Model Name'] == "Forecast July '24"
    assert rows[0]['New Name'] == '' and rows[0]['Embedded Lookup Table'] == ''
    assert rows[0]['Last Update'] == '09/19/2024 00:49:09'


def test_roundtrip_date_switch_reconstructs_explicit_shape() -> None:
    m = ActualOrForecastMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(FORECAST_JULY_24))
    assert rebuilt['name'] == FORECAST_JULY_24['name']
    assert rebuilt['unique'] == FORECAST_JULY_24['unique']
    assert rebuilt['actualOrForecast'] == {
        'ignoreHistoryProd': False,
        'replaceActualWithForecast': {
            'oil': {'date': '2024-06-30'},
            'gas': {'date': '2024-06-30'},
            'water': {'date': '2024-06-30'},
        },
    }
    # Round trip is exact at the CSV level (excluding 'Last Update').
    assert _no_timestamp(m.to_row_dicts(rebuilt)) == _no_timestamp(m.to_row_dicts(FORECAST_JULY_24))


def test_roundtrip_all_never_collapses_to_empty_default_shape() -> None:
    # Both the legacy `{}` shape and an explicit modern {"never": true}-per-phase shape
    # render identical CSV rows, and the inverse always reconstructs the real API's `{}`
    # default, not the explicit form.
    m = ActualOrForecastMapper()
    for source in (ACTUAL_LEGACY_EMPTY, ACTUAL_MODERN_EXPLICIT):
        rows = m.to_row_dicts(source)
        rebuilt = m.from_row_dicts(rows)
        assert rebuilt['actualOrForecast'] == {}, source['name']
        assert _no_timestamp(m.to_row_dicts(rebuilt)) == _no_timestamp(rows)


def test_roundtrip_model_level_ignore_flag_rebuilds_to_empty_phase_nodes() -> None:
    m = ActualOrForecastMapper()
    rows = m.to_row_dicts(IGNORE_HISTORY)
    rebuilt = m.from_row_dicts(rows)
    assert rebuilt['actualOrForecast'] == {
        'ignoreHistoryProd': False,
        'replaceActualWithForecast': {'oil': {}, 'gas': {}, 'water': {}},
    }
    assert _no_timestamp(m.to_row_dicts(rebuilt)) == _no_timestamp(rows)


def test_forward_empty_phase_node_under_present_key_is_ignore_hist_prod() -> None:
    rows = ActualOrForecastMapper().to_row_dicts(FORECAST_ONLY_IGNORE_HIST_PROD)
    assert [r['Key'] for r in rows] == ['oil', 'gas', 'water']
    for r in rows:
        assert r['Criteria'] == 'Ignore Hist Prod'
        assert r['Value'] == ''


def test_roundtrip_ignore_hist_prod_reconstructs_empty_phase_nodes() -> None:
    m = ActualOrForecastMapper()
    rows = m.to_row_dicts(FORECAST_ONLY_IGNORE_HIST_PROD)
    rebuilt = m.from_row_dicts(rows)
    assert rebuilt['actualOrForecast'] == FORECAST_ONLY_IGNORE_HIST_PROD['actualOrForecast']
    assert _no_timestamp(m.to_row_dicts(rebuilt)) == _no_timestamp(rows)


def test_roundtrip_mixed_ignore_hist_prod_and_explicit_phases() -> None:
    model: dict[str, Any] = {
        'name': 'Mixed Ignore',
        'unique': False,
        'actualOrForecast': {
            'ignoreHistoryProd': False,
            'replaceActualWithForecast': {
                'oil': {},
                'gas': {'never': True},
                'water': {'asOfDate': True},
            },
        },
    }
    m = ActualOrForecastMapper()
    by_key = {r['Key']: r for r in m.to_row_dicts(model)}
    assert by_key['oil']['Criteria'] == 'Ignore Hist Prod'
    assert by_key['gas']['Criteria'] == 'Never'
    assert by_key['water']['Criteria'] == 'As of Date'
    assert m.from_row_dicts(m.to_row_dicts(model))['actualOrForecast'] == model['actualOrForecast']


def test_roundtrip_forecast_as_of_all_never_does_not_collapse_to_empty() -> None:
    # A model literally named 'Forecast As Of' that has been customized to Never on
    # every phase must NOT reconstruct to `{}` -- `{}` for that specific built-in
    # name resolves back to "As of Date" (see _phase_criteria), which would silently
    # flip the round trip. It must keep the explicit per-phase {"never": true} shape.
    m = ActualOrForecastMapper()
    never_rows = [
        {
            'Model Name': 'Forecast As Of',
            'Model Type': 'project',
            'Key': phase,
            'Category': '',
            'Criteria': 'Never',
            'Value': '',
        }
        for phase in ('oil', 'gas', 'water')
    ]
    rebuilt = m.from_row_dicts(never_rows)
    assert rebuilt['actualOrForecast'] == {
        'ignoreHistoryProd': False,
        'replaceActualWithForecast': {
            'oil': {'never': True},
            'gas': {'never': True},
            'water': {'never': True},
        },
    }
    # The re-derived CSV still reads back as Never for all 3 phases (round trip holds).
    for r in m.to_row_dicts(rebuilt):
        assert r['Criteria'] == 'Never'


def test_roundtrip_forecast_as_of_default_matches_real_shape() -> None:
    m = ActualOrForecastMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(FORECAST_AS_OF_LEGACY_EMPTY))
    assert rebuilt['actualOrForecast'] == {
        'ignoreHistoryProd': False,
        'replaceActualWithForecast': {
            'oil': {'asOfDate': True},
            'gas': {'asOfDate': True},
            'water': {'asOfDate': True},
        },
    }
    assert _no_timestamp(m.to_row_dicts(rebuilt)) == _no_timestamp(m.to_row_dicts(FORECAST_AS_OF_LEGACY_EMPTY))


def test_roundtrip_mixed_phase_criteria() -> None:
    model: dict[str, Any] = {
        'name': 'Mixed',
        'unique': False,
        'actualOrForecast': {
            'ignoreHistoryProd': False,
            'replaceActualWithForecast': {
                'oil': {'date': '2025-01-31'},
                'gas': {'never': True},
                'water': {'asOfDate': True},
            },
        },
    }
    m = ActualOrForecastMapper()
    rows = m.to_row_dicts(model)
    by_key = {r['Key']: r for r in rows}
    assert by_key['oil']['Criteria'] == 'Date' and by_key['oil']['Value'] == '2025-01-31'
    assert by_key['gas']['Criteria'] == 'Never' and by_key['gas']['Value'] == ''
    assert by_key['water']['Criteria'] == 'As of Date' and by_key['water']['Value'] == ''

    rebuilt = m.from_row_dicts(rows)
    assert rebuilt['actualOrForecast'] == model['actualOrForecast']


def test_roundtrip_unique_model_type() -> None:
    model = dict(FORECAST_JULY_24, unique=True)
    m = ActualOrForecastMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(model))
    assert rebuilt['unique'] is True


def test_model_level_flag_reads_differently_from_legacy_empty_node() -> None:
    # Whole-node `{}` (legacy Never) and `{"ignoreHistoryProd": true}` (Ignore Hist Prod)
    # now render DIFFERENT rows.
    m = ActualOrForecastMapper()
    empty_rows = m.to_row_dicts(dict(ACTUAL_LEGACY_EMPTY, name='X'))
    flagged_rows = m.to_row_dicts(dict(ACTUAL_LEGACY_EMPTY, name='X', actualOrForecast={'ignoreHistoryProd': True}))
    assert empty_rows != flagged_rows
    assert {r['Criteria'] for r in empty_rows} == {'Never'}
    assert {r['Criteria'] for r in flagged_rows} == {'Ignore Hist Prod'}


def test_explicit_node_model_flag_value_is_not_recoverable() -> None:
    # What is still unrecoverable: the flag itself (no CSV column). A flag-True model reads as
    # Ignore Hist Prod on every phase and reconstructs with the flag False and empty phase nodes.
    m = ActualOrForecastMapper()
    phases = {'oil': {'never': True}, 'gas': {'never': True}, 'water': {'never': True}}
    flag_false = dict(
        ACTUAL_MODERN_EXPLICIT,
        actualOrForecast={'ignoreHistoryProd': False, 'replaceActualWithForecast': phases},
    )
    flag_true = dict(
        ACTUAL_MODERN_EXPLICIT,
        actualOrForecast={'ignoreHistoryProd': True, 'replaceActualWithForecast': phases},
    )
    rows_false = m.to_row_dicts(flag_false)
    rows_true = m.to_row_dicts(flag_true)
    # The model-level flag wins over explicit nodes in the forward pass.
    assert {r['Criteria'] for r in rows_false} == {'Never'}
    assert {r['Criteria'] for r in rows_true} == {'Ignore Hist Prod'}
    assert m.from_row_dicts(rows_true)['actualOrForecast']['ignoreHistoryProd'] is False


def test_unknown_criteria_on_from_row_dicts_raises() -> None:
    m = ActualOrForecastMapper()
    rows = m.to_row_dicts(FORECAST_JULY_24)
    rows[0]['Criteria'] = 'Some Weird Criteria'
    with pytest.raises(NotImplementedError):
        m.from_row_dicts(rows)


def test_unknown_phase_shape_on_to_row_dicts_raises() -> None:
    model: dict[str, Any] = {
        'name': 'Bad',
        'unique': False,
        'actualOrForecast': {
            'ignoreHistoryProd': False,
            'replaceActualWithForecast': {
                'oil': {'someNewCriteria': True},
                'gas': {'never': True},
                'water': {'never': True},
            },
        },
    }
    with pytest.raises(NotImplementedError):
        ActualOrForecastMapper().to_row_dicts(model)


def test_from_row_dicts_requires_exactly_3_rows() -> None:
    m = ActualOrForecastMapper()
    with pytest.raises(NotImplementedError):
        m.from_row_dicts([])

    rows = m.to_row_dicts(FORECAST_JULY_24)
    with pytest.raises(NotImplementedError):
        m.from_row_dicts(rows[:2])
    with pytest.raises(NotImplementedError):
        m.from_row_dicts([*rows, dict(rows[0])])


def test_from_row_dicts_requires_all_3_phases() -> None:
    m = ActualOrForecastMapper()
    rows = m.to_row_dicts(FORECAST_JULY_24)
    rows[2] = dict(rows[0])  # duplicate 'oil', missing 'water'
    with pytest.raises(NotImplementedError):
        m.from_row_dicts(rows)


def test_registry_get_mapper() -> None:
    mapper = get_mapper('ActualOrForecast')
    assert isinstance(mapper, ActualOrForecastMapper)
    assert mapper is MAPPERS['ActualOrForecast']
    assert mapper.econ_model_type == 'ActualOrForecast'
