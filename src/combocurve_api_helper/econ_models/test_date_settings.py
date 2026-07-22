import copy
from typing import Any, Dict

import pytest

from combocurve_api_helper.econ_models import MAPPERS, get_mapper
from combocurve_api_helper.econ_models.base import Context
from combocurve_api_helper.econ_models.date_settings import DateSettingsMapper

# ABD exercises the 'years from as of' (non-cash-flow) Cut Off Criteria with an explicit,
# full-schema cutOff (minLife/triggerEclCapex/tolerateNegativeCF all present).
ABD: Dict[str, Any] = {
    'id': '000000000000000000000021',
    'name': 'ABD',
    'unique': False,
    'createdAt': '2026-05-27T14:56:36.648Z',
    'updatedAt': '2026-05-27T14:56:59.511Z',
    'econModelType': 'Dates',
    'dateSetting': {
        'maxWellLife': 0,
        'asOfDate': {'date': '2026-06-01'},
        'discountDate': {'date': '2026-06-01'},
        'cashFlowPriorAsOfDate': False,
        'productionDataResolution': 'same_as_forecast',
        'fpdSourceHierarchy': {
            'firstFpdSource': {'wellHeader': True},
            'secondFpdSource': {'productionData': True},
            'thirdFpdSource': {'forecast': True},
            'fourthFpdSource': {'notUsed': True},
            'useForecastSchedule': False,
        },
    },
    'cutOff': {
        'yearsFromAsOf': 0,
        'minLife': {'none': True},
        'triggerEclCapex': True,
        'includeCapex': False,
        'discount': 0,
        'econLimitDelay': 12,
        'alignDependentPhases': True,
        'tolerateNegativeCF': 0,
    },
}

# 'no cut off' criterion with a non-'none' minLife criterion ('as of').
HISTORICAL: Dict[str, Any] = {
    'id': '000000000000000000000023',
    'name': 'Historical',
    'unique': False,
    'createdAt': '2026-06-29T23:28:39.490Z',
    'updatedAt': '2026-06-29T23:28:47.449Z',
    'econModelType': 'Dates',
    'dateSetting': {
        'maxWellLife': 50,
        'asOfDate': {'date': '2020-01-01'},
        'discountDate': {'date': '2020-01-01'},
        'cashFlowPriorAsOfDate': False,
        'productionDataResolution': 'same_as_forecast',
        'fpdSourceHierarchy': {
            'firstFpdSource': {'wellHeader': True},
            'secondFpdSource': {'productionData': True},
            'thirdFpdSource': {'forecast': True},
            'fourthFpdSource': {'notUsed': True},
            'useForecastSchedule': False,
        },
    },
    'cutOff': {
        'noCutOff': True,
        'minLife': {'asOf': 12},
        'triggerEclCapex': True,
        'includeCapex': False,
        'discount': 0,
        'econLimitDelay': 12,
        'alignDependentPhases': False,
        'tolerateNegativeCF': 0,
    },
}

# 'max cum' (cash-flow) criterion, LEGACY schema: no minLife/triggerEclCapex/tolerateNegativeCF
# keys at all (absent, not null).
ARIES_LEGACY: Dict[str, Any] = {
    'id': '000000000000000000000019',
    'name': 'SAMPLE_DATES_MODEL_0001',
    'unique': False,
    'createdAt': '2026-05-27T00:04:52.843Z',
    'updatedAt': '2026-05-27T00:04:52.843Z',
    'econModelType': 'Dates',
    'dateSetting': {
        'maxWellLife': 50.583200000000005,
        'asOfDate': {'date': '2026-06-01'},
        'discountDate': {'date': '2026-06-01'},
        'cashFlowPriorAsOfDate': False,
        'productionDataResolution': 'same_as_forecast',
        'fpdSourceHierarchy': {
            'firstFpdSource': {'forecast': True},
            'secondFpdSource': {'productionData': True},
            'thirdFpdSource': {'wellHeader': True},
            'fourthFpdSource': {'notUsed': True},
            'useForecastSchedule': False,
        },
    },
    'cutOff': {
        'maxCumCashFlow': True,
        'includeCapex': False,
        'discount': 0,
        'econLimitDelay': 0,
        'alignDependentPhases': False,
    },
}

# 'last positive' (cash-flow) criterion: Discount is NEVER rendered for this criterion even
# though the API carries a real (occasionally non-zero) value.
INJ: Dict[str, Any] = {
    'id': '000000000000000000000022',
    'name': 'INJ',
    'unique': False,
    'createdAt': '2026-05-27T15:54:13.560Z',
    'updatedAt': '2026-05-27T15:54:25.537Z',
    'econModelType': 'Dates',
    'dateSetting': {
        'maxWellLife': 50,
        'asOfDate': {'date': '2026-06-01'},
        'discountDate': {'date': '2026-06-01'},
        'cashFlowPriorAsOfDate': False,
        'productionDataResolution': 'same_as_forecast',
        'fpdSourceHierarchy': {
            'firstFpdSource': {'forecast': True},
            'secondFpdSource': {'productionData': True},
            'thirdFpdSource': {'wellHeader': True},
            'fourthFpdSource': {'notUsed': True},
            'useForecastSchedule': False,
        },
    },
    'cutOff': {
        'lastPositiveCashFlow': True,
        'minLife': {'none': True},
        'triggerEclCapex': True,
        'includeCapex': False,
        'discount': 0,
        'econLimitDelay': 0,
        'alignDependentPhases': False,
        'tolerateNegativeCF': 0,
    },
}

# 'max cum' criterion, FULL schema, with every field fully round-trippable through the CSV --
# NONE of the 5 "extra" cutOff columns lose information.
LOCATION: Dict[str, Any] = {
    'id': '000000000000000000000020',
    'name': 'Location',
    'unique': False,
    'createdAt': '2026-05-27T14:49:18.623Z',
    'updatedAt': '2026-05-27T14:50:23.275Z',
    'econModelType': 'Dates',
    'dateSetting': {
        'maxWellLife': 50,
        'asOfDate': {'date': '2026-06-01'},
        'discountDate': {'date': '2026-06-01'},
        'cashFlowPriorAsOfDate': False,
        'productionDataResolution': 'same_as_forecast',
        'fpdSourceHierarchy': {
            'firstFpdSource': {'forecast': True},
            'secondFpdSource': {'productionData': True},
            'thirdFpdSource': {'wellHeader': True},
            'fourthFpdSource': {'notUsed': True},
            'useForecastSchedule': False,
        },
    },
    'cutOff': {
        'maxCumCashFlow': True,
        'minLife': {'none': True},
        'triggerEclCapex': True,
        'includeCapex': False,
        'discount': 15,
        'econLimitDelay': 12,
        'alignDependentPhases': True,
        'tolerateNegativeCF': 0,
    },
}

# --- Drift-audit fixtures -- the shapes below crashed the mapper before the DateSettings
# drift-audit fix. ---

# 'date' cutOff criterion: the Cut Off Value IS the ISO date string, not a plain flag.
# alignDependentPhases and minLife are both fully present here (contrast BID_TO_LAST_PROD below,
# which omits alignDependentPhases and has a date-valued minLife).
DATE_CUTOFF: Dict[str, Any] = {
    'id': '000000000000000000000007',
    'name': "Jan '22 - Dec '22",
    'unique': False,
    'createdAt': '2022-05-10T21:00:33.909Z',
    'updatedAt': '2023-02-09T21:17:36.576Z',
    'econModelType': 'Dates',
    'dateSetting': {
        'maxWellLife': 50,
        'asOfDate': {'date': '2022-01-01'},
        'discountDate': {'date': '2022-01-01'},
        'cashFlowPriorAsOfDate': False,
        'fpdSourceHierarchy': {
            'firstFpdSource': {'wellHeader': True},
            'secondFpdSource': {'productionData': True},
            'thirdFpdSource': {'forecast': True},
            'fourthFpdSource': {'notUsed': True},
            'useForecastSchedule': True,
        },
    },
    'cutOff': {
        'date': '2022-12-31',
        'minLife': {'asOf': 12},
        'triggerEclCapex': True,
        'includeCapex': False,
        'discount': 0,
        'econLimitDelay': 0,
        'alignDependentPhases': True,
    },
}

# 'firstNegativeCashFlow' cutOff criterion -- the ONLY criterion where CC's CSV export renders a
# real 'Tolerant Negative CF' value instead of always blanking it.
FIRST_NEGATIVE: Dict[str, Any] = {
    'id': '000000000000000000000017',
    'name': "Jan '26 (no min life)",
    'unique': False,
    'createdAt': '2026-02-17T21:40:22.832Z',
    'updatedAt': '2026-02-17T21:40:22.832Z',
    'econModelType': 'Dates',
    'dateSetting': {
        'maxWellLife': 50,
        'asOfDate': {'date': '2026-01-01'},
        'discountDate': {'date': '2026-01-01'},
        'cashFlowPriorAsOfDate': False,
        'productionDataResolution': 'same_as_forecast',
        'fpdSourceHierarchy': {
            'firstFpdSource': {'wellHeader': True},
            'secondFpdSource': {'productionData': True},
            'thirdFpdSource': {'forecast': True},
            'fourthFpdSource': {'notUsed': True},
            'useForecastSchedule': True,
        },
    },
    'cutOff': {
        'firstNegativeCashFlow': True,
        'minLife': {'none': True},
        'triggerEclCapex': False,
        'includeCapex': False,
        'discount': 0,
        'econLimitDelay': 1,
        'alignDependentPhases': True,
        'tolerateNegativeCF': 0,
    },
}

# 'lastPositiveCashFlow' cutOff with `discount` genuinely ABSENT from the API payload (some
# 'last positive' models omit it entirely).
SAMPLE_LASTPOS_NO_DISCOUNT: Dict[str, Any] = {
    'id': '000000000000000000000018',
    'name': 'SAMPLE_0022',
    'unique': False,
    'createdAt': '2026-05-08T14:17:59.974Z',
    'updatedAt': '2026-05-08T14:17:59.974Z',
    'econModelType': 'Dates',
    'dateSetting': {
        'maxWellLife': 38.083400000000005,
        'asOfDate': {'date': '2026-04-01'},
        'discountDate': {'date': '2026-04-01'},
        'cashFlowPriorAsOfDate': False,
        'productionDataResolution': 'same_as_forecast',
        'fpdSourceHierarchy': {
            'firstFpdSource': {'wellHeader': True},
            'secondFpdSource': {'productionData': True},
            'thirdFpdSource': {'forecast': True},
            'fourthFpdSource': {'notUsed': True},
            'useForecastSchedule': False,
        },
    },
    'cutOff': {
        'lastPositiveCashFlow': True,
        'minLife': {'asOf': 0},
        'triggerEclCapex': True,
        'includeCapex': False,
        'econLimitDelay': 0,
        'alignDependentPhases': False,
        # 'discount' genuinely absent -- not present as a key at all.
    },
}

# 'date' cutOff criterion with `alignDependentPhases` genuinely ABSENT (some 'date' models omit
# it) AND a date-valued `minLife` (`{'date': '2027-03-31'}` -- happens to equal the cutOff date
# here, but is an independent value).
BID_TO_LAST_PROD: Dict[str, Any] = {
    'id': '000000000000000000000004',
    'name': 'Bid to Last Prod',
    'unique': False,
    'createdAt': '2021-05-18T20:50:41.532Z',
    'updatedAt': '2023-11-30T14:48:51.068Z',
    'econModelType': 'Dates',
    'dateSetting': {
        'maxWellLife': 50,
        'asOfDate': {'date': '2021-03-01'},
        'discountDate': {'date': '2021-03-01'},
        'cashFlowPriorAsOfDate': False,
        'fpdSourceHierarchy': {
            'firstFpdSource': {'wellHeader': True},
            'secondFpdSource': {'productionData': True},
            'thirdFpdSource': {'forecast': True},
            'fourthFpdSource': {'notUsed': True},
            'useForecastSchedule': True,
        },
    },
    'cutOff': {
        'date': '2027-03-31',
        'minLife': {'date': '2027-03-31'},
        'triggerEclCapex': True,
        'includeCapex': False,
        'discount': 10,
        'econLimitDelay': 0,
        # 'alignDependentPhases' genuinely absent -- not present as a key at all.
    },
}

# 'date' cutOff criterion whose fourthFpdSource is ALSO date-valued (`{'date': '2021-09-01'}`,
# matching the cutOff date here) instead of one of the 4 fixed flag keys. Every other field is
# present (full schema), so this round-trips exactly (see
# test_roundtrip_exact_post_close_afe_date_fpd_source below).
POST_CLOSE_AFE: Dict[str, Any] = {
    'id': '000000000000000000000011',
    'name': 'Sample AFE Model',
    'unique': False,
    'createdAt': '2023-05-01T18:13:35.128Z',
    'updatedAt': '2023-05-01T18:14:20.599Z',
    'econModelType': 'Dates',
    'dateSetting': {
        'maxWellLife': 0,
        'asOfDate': {'date': '2021-09-01'},
        'discountDate': {'date': '2021-09-01'},
        'cashFlowPriorAsOfDate': False,
        'productionDataResolution': 'same_as_forecast',
        'fpdSourceHierarchy': {
            'firstFpdSource': {'wellHeader': True},
            'secondFpdSource': {'productionData': True},
            'thirdFpdSource': {'forecast': True},
            'fourthFpdSource': {'date': '2021-09-01'},
            'useForecastSchedule': True,
        },
    },
    'cutOff': {
        'date': '2021-09-01',
        'minLife': {'none': True},
        'triggerEclCapex': False,
        'includeCapex': False,
        'discount': 0,
        'econLimitDelay': 0,
        'alignDependentPhases': False,
        'tolerateNegativeCF': 0,
    },
}

# 'date' minLife criterion (`cutOff.minLife == {'date': '2026-03-01'}`) paired with the ORDINARY
# 'max cum' cutOff criterion, isolating the minLife-date shape from the 'date' cutOff-criterion
# shape above. Full schema (every fixed key present), so this round-trips exactly (see
# test_roundtrip_exact_minlife_date_full_schema below).
MINLIFE_DATE_FULL: Dict[str, Any] = {
    'id': '000000000000000000000024',
    'name': 'Historical (Sample Project E)',
    'unique': False,
    'createdAt': '2026-07-01T19:07:48.347Z',
    'updatedAt': '2026-07-01T19:11:28.939Z',
    'econModelType': 'Dates',
    'dateSetting': {
        'maxWellLife': 50,
        'asOfDate': {'date': '2020-01-01'},
        'discountDate': {'date': '2020-01-01'},
        'cashFlowPriorAsOfDate': False,
        'productionDataResolution': 'same_as_forecast',
        'fpdSourceHierarchy': {
            'firstFpdSource': {'wellHeader': True},
            'secondFpdSource': {'productionData': True},
            'thirdFpdSource': {'forecast': True},
            'fourthFpdSource': {'notUsed': True},
            'useForecastSchedule': True,
        },
    },
    'cutOff': {
        'maxCumCashFlow': True,
        'minLife': {'date': '2026-03-01'},
        'triggerEclCapex': False,
        'includeCapex': False,
        'discount': 0,
        'econLimitDelay': 0,
        'alignDependentPhases': False,
        'tolerateNegativeCF': 0,
    },
}


def test_to_csv_rows_emits_exactly_one_row() -> None:
    rows = DateSettingsMapper().to_csv_rows(ABD)
    assert len(rows) == 1


def test_to_csv_rows_abd_years_from_as_of() -> None:
    row = DateSettingsMapper().to_csv_rows(ABD)[0]
    assert row['Max Econ Life (Years)'] == '0'
    assert row['As of Date'] == '2026-06-01'
    assert row['Discount Date'] == '2026-06-01'
    assert row['CF Prior To As Of Date'] == 'no'
    assert row['Prod Data Resolution'] == 'same as forecast'
    assert row['1st FPD Source'] == 'well header'
    assert row['2nd FPD Source'] == 'production data'
    assert row['3rd FPD Source'] == 'forecast'
    assert row['4th FPD Source'] == 'not used'
    assert row['Use Forecast/Schedule When No Prod'] == 'no'
    assert row['Cut Off Criteria'] == 'years from as of'
    assert row['Cut Off Value'] == '0'
    assert row['Align Dependent Phases'] == 'yes'
    assert row['Min Life Criteria'] == 'none'
    assert row['Min Life Value'] == ''
    # Non-cash-flow criterion: all 5 "extra" columns blank, EVEN THOUGH the real API cutOff
    # carries non-default values for all of them (econLimitDelay=12, triggerEclCapex=True) --
    # see DateSettingsMapper's class docstring (KNOWN RESIDUAL).
    assert row['Include CAPEX'] == ''
    assert row['Discount'] == ''
    assert row['Econ Limit Delay'] == ''
    assert row['Trigger ECL CAPEX (Unecon)'] == ''
    assert row['Tolerant Negative CF'] == ''
    assert row['Model Type'] == 'project'
    assert row['Model Name'] == 'ABD'


def test_to_csv_rows_includes_common_columns_with_context() -> None:
    ctx = Context(id='ds-abd', created_at=ABD['createdAt'], project_name='Sample Project D | NonOp | MultiBasin')
    row = DateSettingsMapper().to_csv_rows(ABD, context=ctx)[0]
    assert row['Model Id'] == 'ds-abd'
    assert row['Project Name'] == 'Sample Project D | NonOp | MultiBasin'
    assert row['New Name'] == ''
    assert row['Embedded Lookup Table'] == ''
    assert row['Last Update'] == '05/27/2026 14:56:59'


def test_to_csv_rows_historical_no_cut_off_with_min_life_as_of() -> None:
    row = DateSettingsMapper().to_csv_rows(HISTORICAL)[0]
    assert row['Cut Off Criteria'] == 'no cut off'
    assert row['Cut Off Value'] == ''
    assert row['Min Life Criteria'] == 'as of'
    assert row['Min Life Value'] == '12'
    assert row['Align Dependent Phases'] == 'no'
    # non-cash-flow criterion -> extra columns blank despite real underlying values
    assert row['Include CAPEX'] == ''
    assert row['Econ Limit Delay'] == ''
    assert row['Trigger ECL CAPEX (Unecon)'] == ''


def test_to_csv_rows_max_cum_legacy_schema_no_min_life_trigger_tolerate_keys() -> None:
    row = DateSettingsMapper().to_csv_rows(ARIES_LEGACY)[0]
    assert row['Max Econ Life (Years)'] == '50.583200000000005'
    assert row['1st FPD Source'] == 'forecast'
    assert row['2nd FPD Source'] == 'production data'
    assert row['3rd FPD Source'] == 'well header'
    assert row['Cut Off Criteria'] == 'max cum'
    assert row['Cut Off Value'] == ''
    assert row['Min Life Criteria'] == 'none'
    assert row['Min Life Value'] == ''
    # cash-flow criterion -> extra columns DO render, defaulting absent triggerEclCapex to False
    assert row['Include CAPEX'] == 'no'
    assert row['Discount'] == '0'
    assert row['Econ Limit Delay'] == '0'
    assert row['Trigger ECL CAPEX (Unecon)'] == 'no'
    assert row['Tolerant Negative CF'] == ''
    assert row['Align Dependent Phases'] == 'no'


def test_to_csv_rows_last_positive_discount_never_renders() -> None:
    row = DateSettingsMapper().to_csv_rows(INJ)[0]
    assert row['Cut Off Criteria'] == 'last positive'
    assert row['Include CAPEX'] == 'no'
    assert row['Econ Limit Delay'] == '0'
    assert row['Trigger ECL CAPEX (Unecon)'] == 'yes'
    # Discount is a real 0 in the API but 'last positive' NEVER renders it.
    assert row['Discount'] == ''
    assert row['Tolerant Negative CF'] == ''


def test_to_csv_rows_location_max_cum_full_schema() -> None:
    row = DateSettingsMapper().to_csv_rows(LOCATION)[0]
    assert row['Cut Off Criteria'] == 'max cum'
    assert row['Align Dependent Phases'] == 'yes'
    assert row['Include CAPEX'] == 'no'
    assert row['Discount'] == '15'
    assert row['Econ Limit Delay'] == '12'
    assert row['Trigger ECL CAPEX (Unecon)'] == 'yes'
    assert row['Tolerant Negative CF'] == ''


def test_to_csv_rows_unique_model_type() -> None:
    model = dict(ABD, unique=True)
    row = DateSettingsMapper().to_csv_rows(model)[0]
    assert row['Model Type'] == 'unique'


def test_to_csv_rows_unknown_cutoff_criterion_raises() -> None:
    model = dict(ABD, cutOff=dict(ABD['cutOff']))
    model['cutOff'].pop('yearsFromAsOf')
    model['cutOff']['someNewCriterion'] = True
    with pytest.raises(NotImplementedError):
        DateSettingsMapper().to_csv_rows(model)


def test_from_csv_rows_requires_exactly_one_row() -> None:
    m = DateSettingsMapper()
    with pytest.raises(NotImplementedError):
        m.from_csv_rows([])

    row = m.to_csv_rows(ABD)[0]
    with pytest.raises(NotImplementedError):
        m.from_csv_rows([row, dict(row)])


def test_roundtrip_exact_location_fully_recoverable() -> None:
    """'Location' (max cum, full schema) is a shape where ALL fields survive a CSV round trip
    exactly -- see DateSettingsMapper's KNOWN RESIDUAL writeup for why ABD/Historical/INJ do not.
    """
    m = DateSettingsMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(LOCATION))
    assert set(rebuilt) == {'name', 'unique', 'dateSetting', 'cutOff'}
    assert rebuilt['name'] == LOCATION['name']
    assert rebuilt['unique'] == LOCATION['unique']
    assert rebuilt['dateSetting'] == LOCATION['dateSetting']
    assert rebuilt['cutOff'] == LOCATION['cutOff']


def test_roundtrip_exact_location_unique_model() -> None:
    model = dict(LOCATION, unique=True)
    m = DateSettingsMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(model))
    assert rebuilt['unique'] is True
    assert rebuilt['cutOff'] == model['cutOff']


def test_roundtrip_documented_residual_abd_loses_non_cashflow_cutoff_extras() -> None:
    """KNOWN RESIDUAL: ABD's Cut Off Criteria is 'years from as of' (non-cash-flow), so CC's own
    CSV export never carries econLimitDelay/triggerEclCapex/discount/tolerateNegativeCF for it
    (see DateSettingsMapper docstring) -- the CSV round trip CANNOT recover ABD's true values
    (12/True/0/0) and instead reconstructs the CC-implied defaults (0/False/0/0). dateSetting and
    the criterion/minLife/alignDependentPhases fields are unaffected and DO round-trip exactly.
    """
    m = DateSettingsMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(ABD))

    assert rebuilt['dateSetting'] == ABD['dateSetting']
    assert rebuilt['cutOff']['yearsFromAsOf'] == ABD['cutOff']['yearsFromAsOf']
    assert rebuilt['cutOff']['minLife'] == ABD['cutOff']['minLife']
    assert rebuilt['cutOff']['alignDependentPhases'] == ABD['cutOff']['alignDependentPhases']

    # The lossy fields: real ABD values vs. what a CSV round trip can actually reconstruct.
    assert ABD['cutOff']['econLimitDelay'] == 12
    assert rebuilt['cutOff']['econLimitDelay'] == 0
    assert ABD['cutOff']['triggerEclCapex'] is True
    assert rebuilt['cutOff']['triggerEclCapex'] is False
    assert ABD['cutOff']['tolerateNegativeCF'] == 0
    assert rebuilt['cutOff']['tolerateNegativeCF'] == 0  # coincidentally matches here (both 0)


@pytest.mark.parametrize(
    'model, expected_criteria, expected_min_life',
    [
        (ABD, 'yearsFromAsOf', 'none'),
        (HISTORICAL, 'noCutOff', 'asOf'),
        (ARIES_LEGACY, 'maxCumCashFlow', 'none'),
        (INJ, 'lastPositiveCashFlow', 'none'),
        (LOCATION, 'maxCumCashFlow', 'none'),
        (DATE_CUTOFF, 'date', 'asOf'),
        (FIRST_NEGATIVE, 'firstNegativeCashFlow', 'none'),
        (SAMPLE_LASTPOS_NO_DISCOUNT, 'lastPositiveCashFlow', 'asOf'),
        (BID_TO_LAST_PROD, 'date', 'date'),
        (POST_CLOSE_AFE, 'date', 'none'),
        (MINLIFE_DATE_FULL, 'maxCumCashFlow', 'date'),
    ],
)
def test_roundtrip_criterion_and_min_life_keys_always_recoverable(
    model: Dict[str, Any], expected_criteria: str, expected_min_life: str
) -> None:
    """The Cut Off criterion key and the minLife criterion key are NEVER lossy -- unlike the 5
    'extra' cutOff columns, these always render (and thus always round-trip) regardless of
    which Cut Off Criteria is active."""
    m = DateSettingsMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(model))
    assert expected_criteria in rebuilt['cutOff']
    assert expected_min_life in rebuilt['cutOff']['minLife']


def test_legacy_model_missing_production_data_resolution() -> None:
    """Regression: legacy models pre-date `productionDataResolution` and omit it. The forward
    mapper must render them (blank 'Prod Data Resolution') instead of raising ValidationError,
    and the inverse must reconstruct the field as ABSENT (not '') to match the real API shape."""
    import copy

    legacy = copy.deepcopy(ABD)
    del legacy['dateSetting']['productionDataResolution']

    m = DateSettingsMapper()
    rows = m.to_csv_rows(legacy)
    assert rows[0]['Prod Data Resolution'] == ''

    rebuilt = m.from_csv_rows(rows)
    assert 'productionDataResolution' not in rebuilt['dateSetting']


def test_to_csv_rows_date_cutoff_criterion() -> None:
    """'date' cutOff criterion: Cut Off Value is the ISO date string itself, not a numeric or
    blank flag. Non-cash-flow like 'years from as of'/'no cut off': all 5 extra columns blank."""
    row = DateSettingsMapper().to_csv_rows(DATE_CUTOFF)[0]
    assert row['Cut Off Criteria'] == 'date'
    assert row['Cut Off Value'] == '2022-12-31'
    assert row['Align Dependent Phases'] == 'yes'
    assert row['Min Life Criteria'] == 'as of'
    assert row['Min Life Value'] == '12'
    assert row['Include CAPEX'] == ''
    assert row['Discount'] == ''
    assert row['Econ Limit Delay'] == ''
    assert row['Trigger ECL CAPEX (Unecon)'] == ''
    assert row['Tolerant Negative CF'] == ''


def test_roundtrip_documented_residual_date_cutoff_loses_non_cashflow_extras() -> None:
    """Like ABD ('years from as of'), 'date' is non-cash-flow, so triggerEclCapex is lossy on
    round trip (True -> reconstructed False). date/minLife/alignDependentPhases/dateSetting are
    unaffected and DO round-trip exactly."""
    m = DateSettingsMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(DATE_CUTOFF))

    assert rebuilt['dateSetting'] == DATE_CUTOFF['dateSetting']
    assert rebuilt['cutOff']['date'] == DATE_CUTOFF['cutOff']['date']
    assert rebuilt['cutOff']['minLife'] == DATE_CUTOFF['cutOff']['minLife']
    assert rebuilt['cutOff']['alignDependentPhases'] == DATE_CUTOFF['cutOff']['alignDependentPhases']

    assert DATE_CUTOFF['cutOff']['triggerEclCapex'] is True
    assert rebuilt['cutOff']['triggerEclCapex'] is False


def test_to_csv_rows_first_negative_cash_flow_criterion() -> None:
    """'firstNegativeCashFlow' cutOff criterion: behaves like the other cash-flow criteria for
    Include CAPEX/Econ Limit Delay/Trigger ECL CAPEX (they render), like 'last positive' for
    Discount (never renders), and UNIQUELY renders a real 'Tolerant Negative CF' value."""
    row = DateSettingsMapper().to_csv_rows(FIRST_NEGATIVE)[0]
    assert row['Cut Off Criteria'] == 'first negative'
    assert row['Cut Off Value'] == ''
    assert row['Min Life Criteria'] == 'none'
    assert row['Include CAPEX'] == 'no'
    assert row['Discount'] == ''
    assert row['Econ Limit Delay'] == '1'
    assert row['Trigger ECL CAPEX (Unecon)'] == 'no'
    assert row['Tolerant Negative CF'] == '0'


def test_roundtrip_exact_first_negative_cash_flow() -> None:
    """Unlike the other cash-flow criteria, EVERY field of FIRST_NEGATIVE round-trips exactly --
    'first negative' is the only criterion where 'Tolerant Negative CF' is recoverable from the
    CSV rather than reconstructed as a residual default."""
    m = DateSettingsMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(FIRST_NEGATIVE))
    assert rebuilt['dateSetting'] == FIRST_NEGATIVE['dateSetting']
    assert rebuilt['cutOff'] == FIRST_NEGATIVE['cutOff']


def test_to_csv_rows_lastpositive_missing_discount_key_does_not_raise() -> None:
    """Regression: SAMPLE_LASTPOS_NO_DISCOUNT has NO 'discount' key at all (not null) -- the
    forward mapper must render it instead of raising ValidationError. 'Discount' is blank
    regardless (documented residual for 'last positive'), so this is unobservable in the CSV --
    the fix is that the mapper doesn't crash."""
    row = DateSettingsMapper().to_csv_rows(SAMPLE_LASTPOS_NO_DISCOUNT)[0]
    assert row['Cut Off Criteria'] == 'last positive'
    assert row['Discount'] == ''
    assert row['Include CAPEX'] == 'no'
    assert row['Econ Limit Delay'] == '0'
    assert row['Trigger ECL CAPEX (Unecon)'] == 'yes'
    assert row['Min Life Criteria'] == 'as of'
    assert row['Min Life Value'] == '0'


def test_roundtrip_documented_residual_flash_lastpositive_missing_discount_key() -> None:
    """KNOWN RESIDUAL: `discount` is genuinely ABSENT (not 0) on the real API payload, but CC's
    CSV never carries Discount for 'last positive' regardless, so `from_csv_rows` cannot
    distinguish "absent" from "0" and reconstructs the CC-implied default 0 -- present, not
    absent, in the rebuilt dict. minLife/triggerEclCapex/includeCapex/econLimitDelay/
    alignDependentPhases/dateSetting are all present in the real payload and DO round-trip
    exactly."""
    m = DateSettingsMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(SAMPLE_LASTPOS_NO_DISCOUNT))

    assert rebuilt['dateSetting'] == SAMPLE_LASTPOS_NO_DISCOUNT['dateSetting']
    assert rebuilt['cutOff']['minLife'] == SAMPLE_LASTPOS_NO_DISCOUNT['cutOff']['minLife']
    assert rebuilt['cutOff']['triggerEclCapex'] == SAMPLE_LASTPOS_NO_DISCOUNT['cutOff']['triggerEclCapex']
    assert rebuilt['cutOff']['includeCapex'] == SAMPLE_LASTPOS_NO_DISCOUNT['cutOff']['includeCapex']
    assert rebuilt['cutOff']['econLimitDelay'] == SAMPLE_LASTPOS_NO_DISCOUNT['cutOff']['econLimitDelay']
    assert rebuilt['cutOff']['alignDependentPhases'] == SAMPLE_LASTPOS_NO_DISCOUNT['cutOff']['alignDependentPhases']

    assert 'discount' not in SAMPLE_LASTPOS_NO_DISCOUNT['cutOff']
    assert rebuilt['cutOff']['discount'] == 0


def test_to_csv_rows_date_cutoff_missing_align_dependent_phases_does_not_raise() -> None:
    """Regression: BID_TO_LAST_PROD has NO 'alignDependentPhases' key at all (not null/false) --
    the forward mapper must render it (as 'no') instead of raising ValidationError. Also
    exercises a date-valued minLife alongside a date-valued cutOff criterion."""
    row = DateSettingsMapper().to_csv_rows(BID_TO_LAST_PROD)[0]
    assert row['Cut Off Criteria'] == 'date'
    assert row['Cut Off Value'] == '2027-03-31'
    assert row['Align Dependent Phases'] == 'no'
    assert row['Min Life Criteria'] == 'date'
    assert row['Min Life Value'] == '2027-03-31'
    assert row['Discount'] == ''


def test_roundtrip_documented_residual_bid_to_last_prod_missing_align_dependent_phases() -> None:
    """KNOWN RESIDUAL: `alignDependentPhases` is genuinely ABSENT (not False) on the real API
    payload, but the CSV renders 'no' for it regardless (`formats.yes_no(None) == 'no'`), so
    `from_csv_rows` cannot distinguish "absent" from "False" and reconstructs an explicit False.
    The date-valued minLife (`{'date': '2027-03-31'}`) and dateSetting DO round-trip exactly.
    """
    m = DateSettingsMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(BID_TO_LAST_PROD))

    assert rebuilt['dateSetting'] == BID_TO_LAST_PROD['dateSetting']
    assert rebuilt['cutOff']['date'] == BID_TO_LAST_PROD['cutOff']['date']
    assert rebuilt['cutOff']['minLife'] == BID_TO_LAST_PROD['cutOff']['minLife']

    assert 'alignDependentPhases' not in BID_TO_LAST_PROD['cutOff']
    assert rebuilt['cutOff']['alignDependentPhases'] is False


def test_to_csv_rows_date_valued_fpd_source() -> None:
    """A date-valued fpdSourceHierarchy slot (`{'date': 'YYYY-MM-DD'}`) renders as the raw date
    string itself, not one of the 4 fixed labels."""
    row = DateSettingsMapper().to_csv_rows(POST_CLOSE_AFE)[0]
    assert row['4th FPD Source'] == '2021-09-01'
    assert row['1st FPD Source'] == 'well header'
    assert row['2nd FPD Source'] == 'production data'
    assert row['3rd FPD Source'] == 'forecast'


def test_roundtrip_exact_post_close_afe_date_fpd_source() -> None:
    """POST_CLOSE_AFE is a full-schema 'date' cutOff model whose fourthFpdSource is ALSO
    date-valued -- every field (including the date-valued FPD source and the 'date' cutOff
    criterion) round-trips exactly."""
    m = DateSettingsMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(POST_CLOSE_AFE))
    assert set(rebuilt) == {'name', 'unique', 'dateSetting', 'cutOff'}
    assert rebuilt['dateSetting'] == POST_CLOSE_AFE['dateSetting']
    assert rebuilt['cutOff'] == POST_CLOSE_AFE['cutOff']


def test_to_csv_rows_minlife_date_criterion() -> None:
    """'date' minLife criterion (`cutOff.minLife == {'date': 'YYYY-MM-DD'}`), paired with the
    ordinary 'max cum' cutOff criterion -- isolates the minLife-date shape from the 'date'
    cutOff-criterion shape."""
    row = DateSettingsMapper().to_csv_rows(MINLIFE_DATE_FULL)[0]
    assert row['Cut Off Criteria'] == 'max cum'
    assert row['Min Life Criteria'] == 'date'
    assert row['Min Life Value'] == '2026-03-01'


def test_roundtrip_exact_minlife_date_full_schema() -> None:
    """MINLIFE_DATE_FULL is full-schema (every fixed cutOff key present), so it round-trips
    exactly, including the date-valued minLife."""
    m = DateSettingsMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(MINLIFE_DATE_FULL))
    assert set(rebuilt) == {'name', 'unique', 'dateSetting', 'cutOff'}
    assert rebuilt['dateSetting'] == MINLIFE_DATE_FULL['dateSetting']
    assert rebuilt['cutOff'] == MINLIFE_DATE_FULL['cutOff']


def test_maxcumcashflow_missing_discount_renders_blank_not_crash() -> None:
    """Regression: `discount` is Optional (absent on legacy lastPositiveCashFlow models), so a
    maxCumCashFlow model that also omits it must render 'Discount' blank rather than crash in
    _num(None). Not observed in practice, but type-permitted."""
    import copy

    model = copy.deepcopy(LOCATION)  # maxCumCashFlow, normally carries discount
    del model['cutOff']['discount']

    rows = DateSettingsMapper().to_csv_rows(model)
    assert rows[0]['Cut Off Criteria'] == 'max cum'
    assert rows[0]['Discount'] == ''


def test_to_csv_rows_date_anchor_fpd_round_trips() -> None:
    """asOfDate/discountDate can be {'fpd': true} (anchored to first production date) instead of
    {'date': ...} -- rendered as the literal 'fpd' and round-tripped losslessly."""
    model = copy.deepcopy(ABD)
    model['dateSetting']['asOfDate'] = {'fpd': True}
    model['dateSetting']['discountDate'] = {'fpd': True}
    m = DateSettingsMapper()
    row = m.to_csv_rows(model)[0]
    assert row['As of Date'] == 'fpd'
    assert row['Discount Date'] == 'fpd'
    rebuilt = m.from_csv_rows(m.to_csv_rows(model))
    assert rebuilt['dateSetting']['asOfDate'] == {'fpd': True}
    assert rebuilt['dateSetting']['discountDate'] == {'fpd': True}


def test_to_csv_rows_minlife_endhist_round_trips() -> None:
    """cutOff.minLife can be {'endHist': true} (min life = end of historical production) -- a flag
    like {'none': true}; renders 'end hist' with a blank Min Life Value and round-trips."""
    model = copy.deepcopy(ABD)
    model['cutOff']['minLife'] = {'endHist': True}
    m = DateSettingsMapper()
    row = m.to_csv_rows(model)[0]
    assert row['Min Life Criteria'] == 'end hist'
    assert row['Min Life Value'] == ''
    rebuilt = m.from_csv_rows(m.to_csv_rows(model))
    assert rebuilt['cutOff']['minLife'] == {'endHist': True}


def test_to_csv_rows_date_cutoff_missing_include_capex_econ_delay_does_not_raise() -> None:
    """A 'date'-criterion cutOff omits includeCapex/econLimitDelay entirely (only date/minLife/
    alignDependentPhases present). The forward mapper must render (both blank -- non-cash-flow)
    instead of raising a ValidationError on the now-Optional required-field absence."""
    model = copy.deepcopy(ABD)
    model['cutOff'] = {'date': '2024-10-01', 'minLife': {'none': True}, 'alignDependentPhases': False}
    row = DateSettingsMapper().to_csv_rows(model)[0]
    assert row['Cut Off Criteria'] == 'date'
    assert row['Cut Off Value'] == '2024-10-01'
    assert row['Include CAPEX'] == ''
    assert row['Econ Limit Delay'] == ''
    assert row['Min Life Criteria'] == 'none'


def test_registry_get_mapper() -> None:
    mapper = get_mapper('Dates')
    assert isinstance(mapper, DateSettingsMapper)
    assert mapper is MAPPERS['Dates']
    assert mapper.econ_model_type == 'Dates'
