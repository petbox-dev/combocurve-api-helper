from typing import Any, Dict, List

import pytest

from combocurve_api_helper.econ_models.capex import CapexMapper

# Real API leaf shape (verified live, Sample_Onboarding / 'Example' + 'D&C CAPEX'
# models): every listed key is always present on an otherCapex row, plus exactly ONE
# criterion key (+ companion date-header key for fromHeaders/fromSchedule).
_PROBABILISTIC_DEFAULTS: Dict[str, Any] = {
    'distributionType': 'na',
    'mean': 0,
    'standardDeviation': 0,
    'lowerBound': 0,
    'upperBound': 0,
    'mode': 0,
    'seed': 1,
}


def _row(
    category: str, tangible: int = 0, intangible: int = 0, after_econ_limit: bool = False, **criterion: Any
) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        'category': category,
        'description': '',
        'tangible': tangible,
        'intangible': intangible,
        'capexExpense': 'capex',
        'afterEconLimit': after_econ_limit,
        'calculation': 'gross',
        'escalationModel': 'none',
        'escalationStart': {'applyToCriteria': 0},
        'depreciationModel': 'none',
        'dealTerms': 1,
    }
    base.update(criterion)
    base.update(_PROBABILISTIC_DEFAULTS)
    return base


API: Dict[str, Any] = {
    'id': 'c1',
    'name': 'D&C CAPEX',
    'unique': False,
    'createdAt': '2026-05-10T03:11:41.000Z',
    'updatedAt': '2026-05-10T03:11:41.000Z',
    'econModelType': 'Capex',
    'otherCapex': {
        'rows': [
            _row('drilling', intangible=3000, offsetToFpd=-120),
            _row('completion', intangible=4000, offsetToFpd=-30),
            _row('abandonment', intangible=70, after_econ_limit=True, offsetToEconLimit=90),
            _row('drilling', date='2026-07-08'),
            _row('drilling', fromHeaders='offset_to_spud_date', spudDate=0),
            _row('other_investment', oilRate=1),
        ],
    },
}


def test_to_csv_rows_values() -> None:
    rows = CapexMapper().to_csv_rows(API)
    assert len(rows) == 6
    criteria = [r['Criteria'] for r in rows]
    values = [r['Value'] for r in rows]
    assert criteria == ['fpd', 'fpd', 'econ limit', 'date', 'from headers', 'oil rate']
    assert values == ['-120', '-30', '90', '07/08/2026', '0', '1']

    from_headers_row = rows[4]
    assert from_headers_row['From Headers'] == 'Spud Date'
    assert from_headers_row['From Schedule'] == ''

    assert rows[5]['Category'] == 'other investment'

    abandonment_row = rows[2]
    assert abandonment_row['Appear After Econ Limit'] == 'yes'
    assert rows[0]['Appear After Econ Limit'] == 'no'

    # Verified against real CAPEX.csv/CAPEX_per_foot.csv exports: the API 'none'
    # model renders as the title-cased string 'None' in both Escalation and
    # Depreciation columns.
    for r in rows:
        assert r['Depreciation'] == 'None'
        assert r['Escalation'] == 'None'

    assert rows[0]['Escalation Start Criteria'] == 'apply to criteria'
    assert rows[0]['Escalation Start Value (Days/Date)'] == '0'
    assert rows[0]['Paying WI / Earning WI'] == '1'
    assert rows[0]['Calculation'] == 'gross'
    assert rows[0]['CAPEX or Expense'] == 'capex'
    assert rows[0]['Intangible (M$)'] == '3000'
    assert rows[0]['Tangible (M$)'] == '0'


def test_from_headers_first_prod_date() -> None:
    """Real otherCapex rows use the abbreviated token 'offset_to_first_prod_date'
    (companion key 'firstProdDate') -- verified live, project 'Sample Project A | AFE' (9 SAMPLE_LATERAL models). Mirrors the existing 'offset_to_spud_date' handling."""
    m: Dict[str, Any] = {
        'name': 'FIRST PROD DATE CAPEX',
        'unique': False,
        'otherCapex': {
            'rows': [
                _row('artificial_lift', intangible=400, fromHeaders='offset_to_first_prod_date', firstProdDate=185)
            ]
        },
    }
    mapper = CapexMapper()
    rows = mapper.to_csv_rows(m)
    assert len(rows) == 1
    assert rows[0]['Criteria'] == 'from headers'
    assert rows[0]['From Headers'] == 'First Prod Date'
    assert rows[0]['From Schedule'] == ''
    assert rows[0]['Value'] == '185'

    rebuilt = mapper.from_csv_rows(rows)
    assert rebuilt['otherCapex'] == m['otherCapex']


def test_roundtrip() -> None:
    mapper = CapexMapper()
    rebuilt = mapper.from_csv_rows(mapper.to_csv_rows(API))
    assert rebuilt['otherCapex'] == API['otherCapex']
    assert rebuilt['name'] == API['name']
    assert rebuilt['unique'] == API['unique']


def test_drilling_cost_present_warns_and_emits_no_extra_rows() -> None:
    """drillingCost/completionCost ($/ft) are not representable in this CSV -- CC's own
    export confirms this (CAPEX.csv and CAPEX_per_foot.csv contain identical otherCapex
    rows despite the per-foot model having drillingCost/completionCost populated)."""
    m: Dict[str, Any] = {
        'name': 'DC PER FOOT',
        'unique': False,
        'drillingCost': {'fixedCost': 0, 'tangiblePct': 0, 'dollarPerFt': 500},
        'completionCost': {'fixedCost': 0, 'tangiblePct': 0, 'dollarPerFt': 700},
        'otherCapex': {'rows': [_row('drilling', intangible=3000, offsetToFpd=-120)]},
    }
    mapper = CapexMapper()
    with pytest.warns(UserWarning, match='drillingCost'):
        rows = mapper.to_csv_rows(m)
    assert len(rows) == 1


def test_non_default_probabilistic_fields_warn() -> None:
    m: Dict[str, Any] = {
        'name': 'PROBABILISTIC CAPEX',
        'unique': False,
        'otherCapex': {
            'rows': [
                {
                    **_row('drilling', intangible=3000, offsetToFpd=-120),
                    'distributionType': 'normal',
                    'mean': 100,
                }
            ]
        },
    }
    mapper = CapexMapper()
    with pytest.warns(UserWarning, match='probabilistic'):
        mapper.to_csv_rows(m)


def test_escalation_none_python_roundtrip() -> None:
    """escalationModel/depreciationModel = None (Python None, not the string 'none')
    should round-trip to None, matching the Optional-string convention used elsewhere."""
    rows_in: List[Dict[str, Any]] = [
        {
            **_row('drilling', intangible=3000, offsetToFpd=-120),
            'escalationModel': None,
            'depreciationModel': None,
        }
    ]
    m: Dict[str, Any] = {'name': 'NONE MODEL', 'unique': False, 'otherCapex': {'rows': rows_in}}
    mapper = CapexMapper()
    rows = mapper.to_csv_rows(m)
    assert rows[0]['Escalation'] == ''
    assert rows[0]['Depreciation'] == ''
    rebuilt = mapper.from_csv_rows(rows)
    assert rebuilt['otherCapex']['rows'][0]['escalationModel'] is None
    assert rebuilt['otherCapex']['rows'][0]['depreciationModel'] is None
