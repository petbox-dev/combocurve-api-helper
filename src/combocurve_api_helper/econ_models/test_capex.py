import json
import warnings
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


_DRILLING_COST = 'Drilling Cost ($/ft)'
_COMPLETION_COST = 'Completion Cost ($/ft)'

# Real live shapes (project 'Sample Project B'/'Sample Project C', 2026-07): drilling's
# dollarPerFtOfHorizontal is a scalar; completion's is a proppant-loading tier LIST.
_DRILLING_PER_FOOT: Dict[str, Any] = {
    'dollarPerFtOfVertical': 0,
    'dollarPerFtOfHorizontal': 196,
    'fixedCost': 1000,
    'tangiblePct': 0,
    'calculation': 'gross',
    'escalationModel': 'none',
    'depreciationModel': 'none',
    'dealTerms': 1,
    'rows': [{'pctOfTotalCost': 50, 'offsetToFpd': -243}, {'pctOfTotalCost': 50, 'offsetToFpd': -212}],
}
_COMPLETION_PER_FOOT: Dict[str, Any] = {
    'dollarPerFtOfVertical': 0,
    'dollarPerFtOfHorizontal': [{'propLl': 1, 'unitCost': 142}, {'propLl': 10000, 'unitCost': 142}],
    'fixedCost': 3000,
    'tangiblePct': 0,
    'calculation': 'gross',
    'escalationModel': 'none',
    'depreciationModel': 'none',
    'dealTerms': 1,
    'rows': [{'pctOfTotalCost': 50, 'offsetToFpd': -62}, {'pctOfTotalCost': 50, 'offsetToFpd': -31}],
}


def test_perfoot_columns_declared() -> None:
    """The two extra $/ft columns must be part of the mapper's column set, else
    to_csv_rows would silently filter their values back out."""
    assert _DRILLING_COST in CapexMapper.columns
    assert _COMPLETION_COST in CapexMapper.columns


def test_drilling_completion_cost_captured_as_json_and_round_trip() -> None:
    """Model-level drillingCost/completionCost ($/ft) have no native CC CSV column (CC's
    own export omits them); the mapper captures them losslessly as JSON on the first row
    -- no warning -- and reconstructs them on the inverse pass. Completion's
    dollarPerFtOfHorizontal tier LIST and both rows[] schedules survive the round trip."""
    m: Dict[str, Any] = {
        'name': 'DC PER FOOT',
        'unique': False,
        'drillingCost': _DRILLING_PER_FOOT,
        'completionCost': _COMPLETION_PER_FOOT,
        'otherCapex': {'rows': [_row('drilling', intangible=3000, offsetToFpd=-120)]},
    }
    mapper = CapexMapper()
    with warnings.catch_warnings():
        warnings.simplefilter('error')  # capturing per-foot must NOT warn
        rows = mapper.to_csv_rows(m)
    assert len(rows) == 1
    assert json.loads(rows[0][_DRILLING_COST]) == _DRILLING_PER_FOOT
    assert json.loads(rows[0][_COMPLETION_COST]) == _COMPLETION_PER_FOOT

    rebuilt = mapper.from_csv_rows(rows)
    assert rebuilt['drillingCost'] == _DRILLING_PER_FOOT
    assert rebuilt['completionCost'] == _COMPLETION_PER_FOOT
    assert rebuilt['otherCapex'] == m['otherCapex']


def test_perfoot_only_drilling_leaves_completion_absent() -> None:
    """A model with only drillingCost gets a blank Completion column and no
    completionCost key on the inverse pass (not a null-valued key)."""
    m: Dict[str, Any] = {
        'name': 'DRILL ONLY',
        'unique': False,
        'drillingCost': _DRILLING_PER_FOOT,
        'otherCapex': {'rows': [_row('drilling', intangible=3000, offsetToFpd=-120)]},
    }
    mapper = CapexMapper()
    rows = mapper.to_csv_rows(m)
    assert rows[0][_COMPLETION_COST] == ''
    rebuilt = mapper.from_csv_rows(rows)
    assert rebuilt['drillingCost'] == _DRILLING_PER_FOOT
    assert 'completionCost' not in rebuilt


def test_perfoot_with_no_other_capex_rows_uses_carrier_row() -> None:
    """A model with $/ft objects but ZERO otherCapex rows must not silently drop them:
    the mapper emits ONE carrier row (blank line-item cells, so blank Criteria) carrying
    only the JSON, and the inverse pass restores the object without inventing a spurious
    otherCapex row."""
    m: Dict[str, Any] = {
        'name': 'PER FOOT ONLY',
        'unique': False,
        'drillingCost': _DRILLING_PER_FOOT,
        'otherCapex': {'rows': []},
    }
    mapper = CapexMapper()
    rows = mapper.to_csv_rows(m)
    assert len(rows) == 1
    assert rows[0]['Criteria'] == ''
    assert rows[0]['Model Name'] == 'PER FOOT ONLY'
    assert json.loads(rows[0][_DRILLING_COST]) == _DRILLING_PER_FOOT

    rebuilt = mapper.from_csv_rows(rows)
    assert rebuilt['drillingCost'] == _DRILLING_PER_FOOT
    assert rebuilt['otherCapex']['rows'] == []


def test_no_perfoot_emits_blank_columns_and_no_key() -> None:
    """The common case (no $/ft objects) leaves both extra columns blank and adds no
    drillingCost/completionCost key on the inverse pass."""
    rows = CapexMapper().to_csv_rows(API)
    assert all(r[_DRILLING_COST] == '' and r[_COMPLETION_COST] == '' for r in rows)
    rebuilt = CapexMapper().from_csv_rows(rows)
    assert 'drillingCost' not in rebuilt
    assert 'completionCost' not in rebuilt


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


def test_escalation_start_as_of_date() -> None:
    """escalationStart {'asOfDate': <int>} occurs on 2150 of 9729 real otherCapex rows
    (Sample Project B / Sample Project C / Sample Project A, verified live 2026-07). The int is a
    day-offset, mapped like applyToCriteria. The round-trip assertion is label-agnostic
    (proves to_csv / from_csv are inverses); the 'as of date' display string is CC's
    escalation-start UI option, verified against a CC CSV export."""
    rows_in: List[Dict[str, Any]] = [
        {**_row('drilling', intangible=3000, offsetToFpd=-120), 'escalationStart': {'asOfDate': 5}},
    ]
    m: Dict[str, Any] = {'name': 'AS OF DATE ESC', 'unique': False, 'otherCapex': {'rows': rows_in}}
    mapper = CapexMapper()
    rows = mapper.to_csv_rows(m)
    assert rows[0]['Escalation Start Criteria'] == 'as of date'
    assert rows[0]['Escalation Start Value (Days/Date)'] == '5'
    rebuilt = mapper.from_csv_rows(rows)
    assert rebuilt['otherCapex']['rows'][0]['escalationStart'] == {'asOfDate': 5}


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
