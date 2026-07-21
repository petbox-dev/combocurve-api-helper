from typing import Any, Dict, List

import pytest

from combocurve_api_helper.econ_models import MAPPERS, get_mapper
from combocurve_api_helper.econ_models.actual_or_forecast import ActualOrForecastMapper
from combocurve_api_helper.econ_models.base import Context


def _no_timestamp(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """'Last Update' is sourced from the API model's updatedAt/context, never
    reconstructed by from_csv_rows (same convention as every other mapper -- see
    test_fixtures.py's compare_cols = mapper.columns[3:-1]). Round-trip comparisons
    below drop it so they compare only the model-parameter columns.
    """
    return [{k: v for k, v in r.items() if k != 'Last Update'} for r in rows]


# Real, FULL API shapes (verified live, project Sample Project A + broader
# 80-project/381-model account scan). 'Actual' and 'Forecast As Of' are the two
# fixed, non-deletable built-in model names for this econ-model type (ported from
# cc-afe-sync's ACTUAL_OR_FORECAST_ASSIGNMENTS) -- both still legacy `{}`-shaped on
# this project, never migrated to the explicit per-phase form.
ACTUAL_LEGACY_EMPTY: Dict[str, Any] = {
    'id': '000000000000000000000002',
    'name': 'Actual',
    'unique': False,
    'createdAt': '2021-07-12T17:41:11.443Z',
    'updatedAt': '2021-07-12T17:41:11.443Z',
    'econModelType': 'ActualOrForecast',
    'actualOrForecast': {},
}

FORECAST_AS_OF_LEGACY_EMPTY: Dict[str, Any] = {
    'id': '000000000000000000000003',
    'name': 'Forecast As Of',
    'unique': False,
    'createdAt': '2021-07-12T23:04:01.503Z',
    'updatedAt': '2025-01-07T20:01:18.969Z',
    'econModelType': 'ActualOrForecast',
    'actualOrForecast': {},
}

IGNORE_HISTORY: Dict[str, Any] = {
    'id': '000000000000000000000008',
    'name': 'Ignore History',
    'unique': False,
    'createdAt': '2022-07-07T17:58:24.021Z',
    'updatedAt': '2022-07-07T17:58:26.531Z',
    'econModelType': 'ActualOrForecast',
    'actualOrForecast': {'ignoreHistoryProd': True},
}

FORECAST_JULY_24: Dict[str, Any] = {
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

# Explicit modern shape for the built-ins (verified live, project Sample Project B / Sample
# Project C): once migrated, 'Actual' carries explicit {"never": true} and
# 'Forecast As Of' carries explicit {"asOfDate": true} per phase.
ACTUAL_MODERN_EXPLICIT: Dict[str, Any] = {
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

FORECAST_AS_OF_MODERN_EXPLICIT: Dict[str, Any] = {
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


def test_to_csv_rows_emits_exactly_3_rows() -> None:
    rows = ActualOrForecastMapper().to_csv_rows(FORECAST_JULY_24)
    assert len(rows) == 3
    assert [r['Key'] for r in rows] == ['oil', 'gas', 'water']


def test_forward_empty_actual_model_is_never() -> None:
    rows = ActualOrForecastMapper().to_csv_rows(ACTUAL_LEGACY_EMPTY)
    assert len(rows) == 3
    for r in rows:
        assert r['Category'] == ''
        assert r['Criteria'] == 'Never'
        assert r['Value'] == ''


def test_forward_empty_forecast_as_of_model_is_as_of_date() -> None:
    # The built-in 'Forecast As Of' model resolves its legacy empty `{}` shape to
    # "As of Date", NOT "Never" -- name-keyed fallback, verified live.
    rows = ActualOrForecastMapper().to_csv_rows(FORECAST_AS_OF_LEGACY_EMPTY)
    assert len(rows) == 3
    for r in rows:
        assert r['Criteria'] == 'As of Date'
        assert r['Value'] == ''


def test_forward_ignore_history_prod_only_is_never() -> None:
    # actualOrForecast carries ONLY ignoreHistoryProd (no replaceActualWithForecast
    # at all); a non-built-in model name still defaults to Never.
    rows = ActualOrForecastMapper().to_csv_rows(IGNORE_HISTORY)
    for r in rows:
        assert r['Criteria'] == 'Never'
        assert r['Value'] == ''


def test_forward_date_switch_iso_passthrough() -> None:
    rows = ActualOrForecastMapper().to_csv_rows(FORECAST_JULY_24)
    for r in rows:
        assert r['Criteria'] == 'Date'
        # ISO date is passed through UNCHANGED -- not reformatted to MM/DD/YYYY.
        assert r['Value'] == '2024-06-30'


def test_forward_modern_explicit_never_and_as_of_date() -> None:
    rows = ActualOrForecastMapper().to_csv_rows(ACTUAL_MODERN_EXPLICIT)
    for r in rows:
        assert r['Criteria'] == 'Never'
        assert r['Value'] == ''

    rows = ActualOrForecastMapper().to_csv_rows(FORECAST_AS_OF_MODERN_EXPLICIT)
    for r in rows:
        assert r['Criteria'] == 'As of Date'
        assert r['Value'] == ''


def test_to_csv_rows_includes_common_columns_with_context() -> None:
    ctx = Context(id=FORECAST_JULY_24['id'], created_at=FORECAST_JULY_24['createdAt'], project_name='Sample Project A')
    rows = ActualOrForecastMapper().to_csv_rows(FORECAST_JULY_24, context=ctx)
    assert rows[0]['Model Id'] == FORECAST_JULY_24['id']
    assert rows[0]['Project Name'] == 'Sample Project A'
    assert rows[0]['Model Name'] == "Forecast July '24"
    assert rows[0]['New Name'] == '' and rows[0]['Embedded Lookup Table'] == ''
    assert rows[0]['Last Update'] == '09/19/2024 00:49:09'


def test_roundtrip_date_switch_reconstructs_explicit_shape() -> None:
    m = ActualOrForecastMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(FORECAST_JULY_24))
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
    assert _no_timestamp(m.to_csv_rows(rebuilt)) == _no_timestamp(m.to_csv_rows(FORECAST_JULY_24))


def test_roundtrip_all_never_collapses_to_empty_default_shape() -> None:
    # documented limitation: ignoreHistoryProd has no CSV column and is NOT
    # recoverable -- both the legacy `{}` shape and an explicit modern
    # {"never": true}-per-phase shape render identical CSV rows, and the inverse
    # always reconstructs the real API's `{}` default (verified live: this is what
    # Sample Project A' actual 'Actual' model looks like), not the explicit form.
    m = ActualOrForecastMapper()
    for source in (ACTUAL_LEGACY_EMPTY, ACTUAL_MODERN_EXPLICIT, IGNORE_HISTORY):
        rows = m.to_csv_rows(source)
        rebuilt = m.from_csv_rows(rows)
        assert rebuilt['actualOrForecast'] == {}, source['name']
        assert _no_timestamp(m.to_csv_rows(rebuilt)) == _no_timestamp(rows)


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
    rebuilt = m.from_csv_rows(never_rows)
    assert rebuilt['actualOrForecast'] == {
        'ignoreHistoryProd': False,
        'replaceActualWithForecast': {
            'oil': {'never': True},
            'gas': {'never': True},
            'water': {'never': True},
        },
    }
    # The re-derived CSV still reads back as Never for all 3 phases (round trip holds).
    for r in m.to_csv_rows(rebuilt):
        assert r['Criteria'] == 'Never'


def test_roundtrip_forecast_as_of_default_matches_real_shape() -> None:
    m = ActualOrForecastMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(FORECAST_AS_OF_LEGACY_EMPTY))
    assert rebuilt['actualOrForecast'] == {
        'ignoreHistoryProd': False,
        'replaceActualWithForecast': {
            'oil': {'asOfDate': True},
            'gas': {'asOfDate': True},
            'water': {'asOfDate': True},
        },
    }
    assert _no_timestamp(m.to_csv_rows(rebuilt)) == _no_timestamp(m.to_csv_rows(FORECAST_AS_OF_LEGACY_EMPTY))


def test_roundtrip_mixed_phase_criteria() -> None:
    model: Dict[str, Any] = {
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
    rows = m.to_csv_rows(model)
    by_key = {r['Key']: r for r in rows}
    assert by_key['oil']['Criteria'] == 'Date' and by_key['oil']['Value'] == '2025-01-31'
    assert by_key['gas']['Criteria'] == 'Never' and by_key['gas']['Value'] == ''
    assert by_key['water']['Criteria'] == 'As of Date' and by_key['water']['Value'] == ''

    rebuilt = m.from_csv_rows(rows)
    assert rebuilt['actualOrForecast'] == model['actualOrForecast']


def test_roundtrip_unique_model_type() -> None:
    model = dict(FORECAST_JULY_24, unique=True)
    m = ActualOrForecastMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(model))
    assert rebuilt['unique'] is True


def test_ignore_history_prod_dropped_and_not_recoverable() -> None:
    # {} and {"ignoreHistoryProd": true} render IDENTICAL CSV rows -- the flag is
    # unrecoverable from the CSV round trip. This is documented, not a bug.
    m = ActualOrForecastMapper()
    empty_rows = m.to_csv_rows(dict(ACTUAL_LEGACY_EMPTY, name='X'))
    flagged_rows = m.to_csv_rows(dict(ACTUAL_LEGACY_EMPTY, name='X', actualOrForecast={'ignoreHistoryProd': True}))
    assert empty_rows == flagged_rows
    rebuilt_empty = m.from_csv_rows(empty_rows)
    rebuilt_flagged = m.from_csv_rows(flagged_rows)
    assert rebuilt_empty == rebuilt_flagged


def test_unknown_criteria_on_from_csv_rows_raises() -> None:
    m = ActualOrForecastMapper()
    rows = m.to_csv_rows(FORECAST_JULY_24)
    rows[0]['Criteria'] = 'Some Weird Criteria'
    with pytest.raises(NotImplementedError):
        m.from_csv_rows(rows)


def test_unknown_phase_shape_on_to_csv_rows_raises() -> None:
    model: Dict[str, Any] = {
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
        ActualOrForecastMapper().to_csv_rows(model)


def test_from_csv_rows_requires_exactly_3_rows() -> None:
    m = ActualOrForecastMapper()
    with pytest.raises(NotImplementedError):
        m.from_csv_rows([])

    rows = m.to_csv_rows(FORECAST_JULY_24)
    with pytest.raises(NotImplementedError):
        m.from_csv_rows(rows[:2])
    with pytest.raises(NotImplementedError):
        m.from_csv_rows(rows + [dict(rows[0])])


def test_from_csv_rows_requires_all_3_phases() -> None:
    m = ActualOrForecastMapper()
    rows = m.to_csv_rows(FORECAST_JULY_24)
    rows[2] = dict(rows[0])  # duplicate 'oil', missing 'water'
    with pytest.raises(NotImplementedError):
        m.from_csv_rows(rows)


def test_registry_get_mapper() -> None:
    mapper = get_mapper('ActualOrForecast')
    assert isinstance(mapper, ActualOrForecastMapper)
    assert mapper is MAPPERS['ActualOrForecast']
    assert mapper.econ_model_type == 'ActualOrForecast'
