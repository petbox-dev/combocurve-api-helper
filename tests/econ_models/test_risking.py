from typing import Any, Dict

import pytest

from combocurve_api_helper.econ_models import MAPPERS, get_mapper
from combocurve_api_helper.econ_models.risking import RiskingMapper

# Real, FULL API shape. 'risking' sits at the TOP LEVEL of the model dict -- NOT under
# 'data' -- unlike every other econ-model type in this package. This model has NO CSV
# 'wells' row despite an identical `risking` shape to models that DO -- confirming the
# wells row is not recoverable from the API.
SAMPLE_WELL_1_P50: Dict[str, Any] = {
    'id': 'risk-rd7h',
    'name': 'SAMPLE WELL 1 P50',
    'unique': False,
    'createdAt': '2023-05-16T16:59:55.000Z',
    'updatedAt': '2023-05-16T16:59:55.000Z',
    'econModelType': 'Risking',
    'risking': {
        'riskProd': True,
        'riskNglDripCondViaGasRisk': True,
        'oil': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 93.976}]},
        'gas': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 93.976}]},
        'ngl': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 100}]},
        'dripCondensate': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 100}]},
        'water': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 100}]},
    },
}

# riskProd/riskNglDripCondViaGasRisk KEYS ABSENT ENTIRELY. CC's CSV still renders
# 'Risk Hist Prod'/'Risk NGL...' as 'yes' -- the documented None -> yes default.
LOW_PROPPANT: Dict[str, Any] = {
    'name': 'Low Proppant',
    'unique': False,
    'econModelType': 'Risking',
    'risking': {
        'oil': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 85}]},
        'gas': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 85}]},
        'ngl': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 85}]},
        'dripCondensate': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 85}]},
        'water': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 85}]},
    },
}

# riskProd == False -- exercises the mapper's explicit no/False branch, not just the
# None default.
SAMPLE_UNIT_2: Dict[str, Any] = {
    'name': 'SAMPLE_UNIT_2',
    'unique': False,
    'econModelType': 'Risking',
    'risking': {
        'riskProd': False,
        'riskNglDripCondViaGasRisk': True,
        'oil': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 65}]},
        'gas': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 65}]},
        'ngl': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 100}]},
        'dripCondensate': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 100}]},
        'water': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 65}]},
    },
}

_BLANK_COLS = (
    'Period',
    'Criteria Start',
    'Criteria End',
    'Repeat Range Of Dates',
    'Total Occurrences',
    'Scale Post Shut-in Factor',
    'Scale Post Shut-In End Criteria',
    'Scale Post Shut-In End',
    'Fixed Expense',
    'CAPEX',
)


def test_to_csv_rows_emits_exactly_five_phase_rows_in_order() -> None:
    rows = RiskingMapper().to_csv_rows(SAMPLE_WELL_1_P50)
    assert len(rows) == 5
    assert [r['Phase'] for r in rows] == ['oil', 'gas', 'ngl', 'drip cond', 'water']
    for r in rows:
        assert r['Key'] == 'risking'
        assert r['Category'] == ''
        assert r['Description'] == ''
        assert r['Criteria'] == 'flat'
        assert r['Unit'] == '%'
        assert r['Risk Hist Prod'] == 'yes'
        assert r['Risk NGL & Drip Cond via Gas Risk'] == 'yes'
        for blank_col in _BLANK_COLS:
            assert r[blank_col] == ''

    values = {r['Phase']: r['Value'] for r in rows}
    assert values == {'oil': '93.976', 'gas': '93.976', 'ngl': '100', 'drip cond': '100', 'water': '100'}


def test_to_csv_rows_int_value_stays_integral() -> None:
    rows = RiskingMapper().to_csv_rows(SAMPLE_WELL_1_P50)
    ngl = next(r for r in rows if r['Phase'] == 'ngl')
    assert ngl['Value'] == '100'  # not '100.0'


def test_to_csv_rows_risk_prod_none_defaults_to_yes() -> None:
    rows = RiskingMapper().to_csv_rows(LOW_PROPPANT)
    assert len(rows) == 5
    for r in rows:
        assert r['Risk Hist Prod'] == 'yes'
        assert r['Risk NGL & Drip Cond via Gas Risk'] == 'yes'


def test_to_csv_rows_risk_prod_false_renders_no() -> None:
    rows = RiskingMapper().to_csv_rows(SAMPLE_UNIT_2)
    assert len(rows) == 5
    for r in rows:
        assert r['Risk Hist Prod'] == 'no'
        assert r['Risk NGL & Drip Cond via Gas Risk'] == 'yes'


def test_roundtrip_exact_sample_well_1() -> None:
    m = RiskingMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(SAMPLE_WELL_1_P50))
    assert rebuilt['name'] == SAMPLE_WELL_1_P50['name']
    assert rebuilt['unique'] == SAMPLE_WELL_1_P50['unique']
    assert rebuilt['risking'] == SAMPLE_WELL_1_P50['risking']


def test_roundtrip_risk_prod_false_exact() -> None:
    m = RiskingMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(SAMPLE_UNIT_2))
    assert rebuilt['risking'] == SAMPLE_UNIT_2['risking']


def test_roundtrip_risk_prod_none_collapses_to_explicit_true() -> None:
    # DOCUMENTED lossy collapse: CSV cannot distinguish an explicit True riskProd from
    # an absent/None riskProd -- both render 'yes' -- so the inverse always reconstructs
    # an explicit bool. Mirrors the forward mapping rule exactly (None -> yes default).
    m = RiskingMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(LOW_PROPPANT))
    assert rebuilt['risking']['riskProd'] is True
    assert rebuilt['risking']['riskNglDripCondViaGasRisk'] is True
    for phase in ('oil', 'gas', 'ngl', 'dripCondensate', 'water'):
        assert rebuilt['risking'][phase] == LOW_PROPPANT['risking'][phase]


def test_from_csv_rows_ignores_wells_rows() -> None:
    # Every real CC Risking CSV export also carries a Key == 'wells' row on most models
    # (Value=1, Criteria=fpd, Period=ecl) that has no corresponding API field -- see
    # RiskingMapper's class docstring. from_csv_rows must skip it without error.
    m = RiskingMapper()
    rows = m.to_csv_rows(SAMPLE_WELL_1_P50)
    wells_row = dict(rows[0])
    wells_row.update(
        {
            'Key': 'wells',
            'Phase': '',
            'Value': '1',
            'Criteria': 'fpd',
            'Period': 'ecl',
            'Risk Hist Prod': '',
            'Risk NGL & Drip Cond via Gas Risk': '',
            'Unit': '',
        }
    )
    rebuilt = m.from_csv_rows(rows + [wells_row])
    assert rebuilt['risking'] == SAMPLE_WELL_1_P50['risking']


def test_unknown_entire_well_life_raises() -> None:
    model: Dict[str, Any] = {
        'name': 'Bad',
        'unique': False,
        'risking': {
            'riskProd': True,
            'riskNglDripCondViaGasRisk': True,
            'oil': {'rows': [{'entireWellLife': 'Dates', 'multiplier': 90}]},
            'gas': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 90}]},
            'ngl': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 100}]},
            'dripCondensate': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 100}]},
            'water': {'rows': [{'entireWellLife': 'Flat', 'multiplier': 100}]},
        },
    }
    with pytest.raises(NotImplementedError):
        RiskingMapper().to_csv_rows(model)


def test_unknown_criteria_raises_on_inverse() -> None:
    rows = RiskingMapper().to_csv_rows(SAMPLE_WELL_1_P50)
    rows[0]['Criteria'] = 'fpd'
    with pytest.raises(NotImplementedError):
        RiskingMapper().from_csv_rows(rows)


def test_unknown_key_raises_on_inverse() -> None:
    rows = RiskingMapper().to_csv_rows(SAMPLE_WELL_1_P50)
    rows[0]['Key'] = 'something_else'
    with pytest.raises(NotImplementedError):
        RiskingMapper().from_csv_rows(rows)


def test_unknown_phase_raises_on_inverse() -> None:
    rows = RiskingMapper().to_csv_rows(SAMPLE_WELL_1_P50)
    rows[0]['Phase'] = 'condensate'
    with pytest.raises(NotImplementedError):
        RiskingMapper().from_csv_rows(rows)


def test_common_columns_present() -> None:
    rows = RiskingMapper().to_csv_rows(SAMPLE_WELL_1_P50)
    assert rows[0]['Model Name'] == 'SAMPLE WELL 1 P50'
    assert rows[0]['Model Type'] == 'project'


def test_to_csv_rows_unique_model_type() -> None:
    model = dict(SAMPLE_WELL_1_P50, unique=True)
    rows = RiskingMapper().to_csv_rows(model)
    assert rows[0]['Model Type'] == 'unique'


def test_registry_get_mapper() -> None:
    mapper = get_mapper('Risking')
    assert isinstance(mapper, RiskingMapper)
    assert mapper is MAPPERS['Risking']
    assert mapper.econ_model_type == 'Risking'
