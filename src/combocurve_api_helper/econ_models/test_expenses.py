from typing import Any, Dict

import pytest

from combocurve_api_helper.econ_models.expenses import ExpensesMapper


def _leaf(rows: Any, **overrides: Any) -> Dict[str, Any]:
    """Real API leaf shape (verified live, model SAMPLE_OPEX_LOOKUP_0001):
    every listed setting key is always present."""
    base: Dict[str, Any] = {
        'shrinkageCondition': 'shrunk',
        'description': None,
        'escalationModel': 'none',
        'calculation': 'wi',
        'affectEconLimit': True,
        'deductBeforeSeveranceTax': False,
        'deductBeforeAdValTax': False,
        'cap': None,
        'dealTerms': 100,
        'rateType': 'gross_well_head',
        'rowsCalculationMethod': 'monotonic',
        'rows': rows,
    }
    base.update(overrides)
    return base


def _strip_rate_fields(node: Any) -> Any:
    """'Rate Type'/'Rate Rows Calculation Method' never round-trip through the CSV --
    CC's real Expenses export blanks both columns unconditionally even though the API
    leaf carries real rateType/rowsCalculationMethod values (see ExpenseLeaf
    docstring), so from_csv_rows never reconstructs them. Strip them recursively
    before comparing a rebuilt variableExpenses/fixedExpenses/carbonExpenses/
    waterDisposal structure back against a source API dict that has them."""
    if isinstance(node, dict):
        if 'rows' in node:
            return {k: v for k, v in node.items() if k not in ('rateType', 'rowsCalculationMethod')}
        return {k: _strip_rate_fields(v) for k, v in node.items()}
    return node


API: Dict[str, Any] = {
    'id': 'e1',
    'name': 'OPEX',
    'unique': False,
    'createdAt': '2026-05-10T03:11:41.000Z',
    'updatedAt': '2026-05-10T03:11:41.000Z',
    'econModelType': 'Expenses',
    'variableExpenses': {
        'oil': {
            'processing': _leaf(
                [{'offsetToFpd': 1200, 'dollarPerBbl': 0}],
                description='OPC/OIL',
                cap=500,
                deductBeforeAdValTax=True,
            ),
            'gathering': _leaf(
                [{'entireWellLife': 'Flat', 'dollarPerBbl': 0}],
                shrinkageCondition='unshrunk',
            ),
        },
        'gas': {
            'processing': _leaf(
                [{'offsetToFpd': 1200, 'dollarPerMcf': 0.31}],
                description='OPC/GAS',
                shrinkageCondition=None,
                escalationModel=None,
                affectEconLimit=False,
                deductBeforeSeveranceTax=True,
                rateType=None,
                rowsCalculationMethod=None,
            ),
        },
        'ngl': {
            'marketing': _leaf(
                # A single fpd row is, by definition, the leaf's terminal row -- see
                # the terminal-row rule in ExpenseApiRow's docstring. offsetToFpd=1200
                # (the inverse canonical value) is used here so the round-trip test
                # below reproduces this leaf exactly; test_roundtrip_non_canonical_*
                # covers the documented non-exact case with a different offset.
                [{'offsetToFpd': 1200, 'dollarPerBbl': 1.25}],
                description='MKT/NGL',
                shrinkageCondition=None,
                rateType=None,
                rowsCalculationMethod=None,
            ),
        },
        # 'boe'/'totalFluid' are real phases -- verified against a real Expenses.csv
        # export (Key='boe'/'total_fluid', Category='opc') AND against the live API
        # model SAMPLE_OPEX_LOOKUP_0001. Unlike oil/gas/ngl above, their
        # REAL API shape is DOUBLE-NESTED under the subcat key: raw verified value is
        # `variableExpenses.boe == {"processing": {"processing": {<leaf>}}}` (identically
        # for totalFluid) -- i.e. `variableExpenses[phase]['processing']['processing']`
        # is the real leaf, not `variableExpenses[phase]['processing']`.
        'boe': {
            'processing': {
                'processing': _leaf(
                    [{'entireWellLife': 'Flat', 'dollarPerBbl': 0}],
                    shrinkageCondition='unshrunk',
                ),
            },
        },
        'totalFluid': {
            'processing': {
                'processing': _leaf(
                    [{'entireWellLife': 'Flat', 'dollarPerBbl': 0}],
                    shrinkageCondition='unshrunk',
                ),
            },
        },
    },
    'fixedExpenses': {
        'monthlyWellCost': _leaf(
            [{'offsetToFpd': 1200, 'fixedExpense': 4100}],
            description='OPC/T',
            shrinkageCondition=None,
            rateType=None,
            rowsCalculationMethod=None,
            stopAtEconLimit=True,
            expenseBeforeFpd=True,
        ),
    },
    'carbonExpenses': {
        'category': 'co2e',
        'co2': _leaf(
            [{'entireWellLife': 'Flat', 'carbonExpense': 0}],
            shrinkageCondition=None,
            escalationModel=None,
            rateType=None,
            rowsCalculationMethod=None,
        ),
    },
    'waterDisposal': _leaf(
        [{'entireWellLife': 'Flat', 'dollarPerBbl': 0}],
        shrinkageCondition=None,
        escalationModel=None,
        rateType=None,
        rowsCalculationMethod=None,
    ),
}


def test_to_csv_rows_oil_processing() -> None:
    rows = ExpensesMapper().to_csv_rows(API)
    oil_processing = next(r for r in rows if r['Key'] == 'oil' and r['Category'] == 'opc')
    assert oil_processing['Criteria'] == 'fpd'
    assert oil_processing['Period'] == 'ecl'
    assert oil_processing['Unit'] == '$/bbl'
    assert oil_processing['Description'] == 'OPC/OIL'
    # Verified against real Expenses.csv: 'Value' always renders with a decimal
    # point, e.g. '0.0' not '0' (unlike Capex/Differentials/ProductionTaxes).
    assert oil_processing['Value'] == '0.0'
    assert oil_processing['Cap'] == '500'
    assert oil_processing['Deduct bef Ad Val Tax'] == 'yes'


def test_to_csv_rows_gas_processing() -> None:
    rows = ExpensesMapper().to_csv_rows(API)
    gas_processing = next(r for r in rows if r['Key'] == 'gas' and r['Category'] == 'opc')
    assert gas_processing['Criteria'] == 'fpd'
    assert gas_processing['Period'] == 'ecl'
    assert gas_processing['Unit'] == '$/mcf'
    assert gas_processing['Description'] == 'OPC/GAS'
    assert gas_processing['Value'] == '0.31'
    assert gas_processing['Shrinkage Condition'] == ''
    assert gas_processing['Escalation'] == ''


def test_to_csv_rows_oil_gathering_flat() -> None:
    rows = ExpensesMapper().to_csv_rows(API)
    oil_gathering = next(r for r in rows if r['Key'] == 'oil' and r['Category'] == 'g&p')
    assert oil_gathering['Criteria'] == 'flat'
    assert oil_gathering['Period'] == ''
    assert oil_gathering['Unit'] == '$/bbl'


def test_to_csv_rows_ngl_marketing_single_fpd_row_is_terminal_ecl() -> None:
    # A leaf whose only fpd row is terminal (the common case) renders that single row
    # as 'ecl' -- position-based (last row of the leaf), not value-based.
    rows = ExpensesMapper().to_csv_rows(API)
    ngl_marketing = next(r for r in rows if r['Key'] == 'ngl' and r['Category'] == 'mkt')
    assert ngl_marketing['Criteria'] == 'fpd'
    assert ngl_marketing['Period'] == 'ecl'
    assert ngl_marketing['Value'] == '1.25'


def test_to_csv_rows_fixed_monthly_well_cost() -> None:
    rows = ExpensesMapper().to_csv_rows(API)
    fixed = next(r for r in rows if r['Key'] == 'fixed')
    assert fixed['Category'] == 'fixed1'
    assert fixed['Unit'] == '$/month'
    assert fixed['Period'] == 'ecl'
    assert fixed['Value'] == '4100.0'
    assert fixed['Expense bef FPD'] == 'yes'
    assert fixed['Stop at Econ Limit'] == 'yes'
    assert fixed['Description'] == 'OPC/T'


def test_fixed_expense_before_fpd_false_renders_no_and_round_trips() -> None:
    """Regression (final-review M5): a fixed expense with expenseBeforeFpd=False must
    render CSV 'no', not '' -- real CC exports carry 'no' on 82+ models. The old
    yes_blank renderer could only emit ''/'yes', silently corrupting the False case
    and breaking the CSV round-trip. Stop at Econ Limit follows the same yes/no rule."""
    model: Dict[str, Any] = {
        'id': 'e2',
        'name': 'FX',
        'unique': False,
        'createdAt': '2026-05-10T03:11:41.000Z',
        'updatedAt': '2026-05-10T03:11:41.000Z',
        'econModelType': 'Expenses',
        'fixedExpenses': {
            'monthlyWellCost': _leaf(
                [{'offsetToFpd': 1200, 'fixedExpense': 4100}],
                description='OPC/T',
                shrinkageCondition=None,
                rateType=None,
                rowsCalculationMethod=None,
                stopAtEconLimit=False,
                expenseBeforeFpd=False,
            ),
        },
    }
    m = ExpensesMapper()
    rows = m.to_csv_rows(model)
    fixed = next(r for r in rows if r['Key'] == 'fixed')
    assert fixed['Expense bef FPD'] == 'no'
    assert fixed['Stop at Econ Limit'] == 'no'
    back = next(r for r in m.to_csv_rows(m.from_csv_rows(rows)) if r['Key'] == 'fixed')
    assert back['Expense bef FPD'] == 'no'
    assert back['Stop at Econ Limit'] == 'no'


def test_to_csv_rows_carbon_co2() -> None:
    rows = ExpensesMapper().to_csv_rows(API)
    co2 = next(r for r in rows if r['Key'] == 'co2')
    assert co2['Category'] == 'co2e'
    assert co2['Unit'] == '$/MT'
    assert co2['Criteria'] == 'flat'
    assert co2['Value'] == '0.0'


def test_to_csv_rows_water_disposal() -> None:
    rows = ExpensesMapper().to_csv_rows(API)
    water = next(r for r in rows if r['Key'] == 'water')
    assert water['Category'] == ''
    assert water['Unit'] == '$/bbl'
    assert water['Criteria'] == 'flat'
    assert water['Value'] == '0.0'


def test_to_csv_rows_boe_and_total_fluid_emitted() -> None:
    """Regression test for the (verified, real-API->CSV) requirement that 'boe'/
    'total_fluid' variable-expense phases are emitted, not dropped -- exercised here
    via the shared API fixture's REAL double-nested shape
    (variableExpenses.boe.processing.processing is the leaf, see API above)."""
    rows = ExpensesMapper().to_csv_rows(API)

    boe = next(r for r in rows if r['Key'] == 'boe')
    assert boe['Category'] == 'opc'
    assert boe['Unit'] == '$/bbl'
    assert boe['Criteria'] == 'flat'
    assert boe['Value'] == '0.0'

    total_fluid = next(r for r in rows if r['Key'] == 'total_fluid')
    assert total_fluid['Category'] == 'opc'
    assert total_fluid['Unit'] == '$/bbl'
    assert total_fluid['Criteria'] == 'flat'
    assert total_fluid['Value'] == '0.0'


def _normalize_for_roundtrip_compare(node: Any) -> Any:
    """Normalize a variableExpenses/etc. structure for exact-equality round-trip
    comparison against a REAL (live-verified) source model. Strips THREE ALREADY-
    DOCUMENTED, pre-existing CSV-format limitations that are orthogonal to the
    boe/totalFluid double-nesting bug this module targets, and apply uniformly to
    every phase (not just boe/totalFluid):
    (a) rateType/rowsCalculationMethod are never round-tripped (see
        _strip_rate_fields / ExpenseLeaf docstring -- the real CSV always blanks
        both columns);
    (b) a leaf's real `description` of `''` (empty string, as opposed to null) is
        indistinguishable from a blank CSV cell on the way back, so it always
        reconstructs as `None` -- the same blank-cell-ambiguity class as the
        documented `cap: ''` normalization;
    (c) `shrinkageCondition` is only present on real oil/gas leaves (verified live,
        same model: ngl/dripCondensate/boe/totalFluid leaves omit the key entirely),
        but `from_csv_rows` always reconstructs it (as `None` when the CSV cell is
        blank) since the CSV format has a 'Shrinkage Condition' column regardless of
        phase -- so a rebuilt leaf always carries the key even when the source
        never had it.
    """
    if isinstance(node, dict):
        if 'rows' in node:
            out = {k: v for k, v in node.items() if k not in ('rateType', 'rowsCalculationMethod')}
            if out.get('description') == '':
                out['description'] = None
            if out.get('shrinkageCondition') is None:
                out.pop('shrinkageCondition', None)
            return out
        return {k: _normalize_for_roundtrip_compare(v) for k, v in node.items()}
    return node


def test_boe_and_total_fluid_real_double_nested_structure_round_trips() -> None:
    """Uses the EXACT raw shape verified live against model
    SAMPLE_OPEX_LOOKUP_0001 (project 'Sample Project E | NonOp | Multi Basin'):
    `variableExpenses.boe == {"processing": {"processing": {<leaf>}}}` (identically for
    `totalFluid`) -- DOUBLE-nested under the subcat key, unlike every other phase's
    single-nested `variableExpenses.<phase>.<subcat> == {<leaf>}`. Before the fix,
    `ExpensesMapper` treated `{"processing": {<leaf>}}` itself as the leaf (no `rows`
    key at that level -> zero rows emitted); this proves boe/total_fluid rows are now
    emitted AND that from_csv_rows reconstructs the real double-nested shape (not the
    normal single-nested one)."""
    leaf = {
        'description': '',
        'escalationModel': 'none',
        'calculation': 'wi',
        'affectEconLimit': True,
        'deductBeforeSeveranceTax': False,
        'deductBeforeAdValTax': False,
        'cap': None,
        'dealTerms': 1,
        'rateType': 'gross_well_head',
        'rowsCalculationMethod': 'non_monotonic',
        'rows': [{'dollarPerBbl': 0, 'entireWellLife': 'Flat'}],
    }
    model: Dict[str, Any] = {
        'name': 'BOE TOTAL FLUID REAL DOUBLE NESTED',
        'unique': False,
        'variableExpenses': {
            'boe': {'processing': {'processing': dict(leaf)}},
            'totalFluid': {'processing': {'processing': dict(leaf)}},
        },
    }
    mapper = ExpensesMapper()
    rows = mapper.to_csv_rows(model)

    boe_rows = [r for r in rows if r['Key'] == 'boe']
    assert len(boe_rows) == 1
    assert boe_rows[0]['Category'] == 'opc'
    assert boe_rows[0]['Unit'] == '$/bbl'
    assert boe_rows[0]['Criteria'] == 'flat'
    assert boe_rows[0]['Value'] == '0.0'

    total_fluid_rows = [r for r in rows if r['Key'] == 'total_fluid']
    assert len(total_fluid_rows) == 1
    assert total_fluid_rows[0]['Category'] == 'opc'
    assert total_fluid_rows[0]['Unit'] == '$/bbl'
    assert total_fluid_rows[0]['Criteria'] == 'flat'
    assert total_fluid_rows[0]['Value'] == '0.0'

    rebuilt = mapper.from_csv_rows(rows)
    # The nesting depth/shape itself must match exactly, unnormalized -- this is the
    # actual bug under test.
    assert set(rebuilt['variableExpenses']['boe'].keys()) == {'processing'}
    assert set(rebuilt['variableExpenses']['boe']['processing'].keys()) == {'processing'}
    assert set(rebuilt['variableExpenses']['totalFluid'].keys()) == {'processing'}
    assert set(rebuilt['variableExpenses']['totalFluid']['processing'].keys()) == {'processing'}
    # Full leaf content matches too, after normalizing the two orthogonal, pre-existing,
    # already-documented CSV limitations above (not part of the nesting bug).
    assert _normalize_for_roundtrip_compare(rebuilt['variableExpenses']['boe']) == _normalize_for_roundtrip_compare(
        model['variableExpenses']['boe']
    )
    assert _normalize_for_roundtrip_compare(
        rebuilt['variableExpenses']['totalFluid']
    ) == _normalize_for_roundtrip_compare(model['variableExpenses']['totalFluid'])


def test_rate_type_and_rows_calculation_method_always_blank() -> None:
    """Verified against real Expenses.csv: 'Rate Type'/'Rate Rows Calculation Method'
    are ALWAYS blank, even though every leaf in API carries real
    rateType='gross_well_head'/rowsCalculationMethod='monotonic' (via the shared
    _leaf() base). Not round-trippable -- see ExpenseLeaf docstring."""
    rows = ExpensesMapper().to_csv_rows(API)
    assert rows, 'expected at least one row'
    for r in rows:
        assert r['Rate Type'] == ''
        assert r['Rate Rows Calculation Method'] == ''


def test_to_csv_rows_multi_row_fpd_leaf_only_last_row_is_ecl() -> None:
    """Terminal-row rule (a): within a single leaf, earlier fpd rows render their
    literal month offset; only the LAST row of the leaf's rows list renders 'ecl' --
    regardless of its numeric value (verified live: real terminal offsets include
    1104/1140, not just 1200)."""
    model: Dict[str, Any] = {
        'name': 'MULTI ROW FPD',
        'unique': False,
        'variableExpenses': {
            'oil': {
                'processing': _leaf(
                    [
                        {'offsetToFpd': 12, 'dollarPerBbl': 1.0},
                        {'offsetToFpd': 36, 'dollarPerBbl': 2.0},
                        # Not the constant 1200 -- proves the rule is position-based,
                        # not value-based.
                        {'offsetToFpd': 1104, 'dollarPerBbl': 3.0},
                    ],
                ),
            },
        },
    }
    rows = ExpensesMapper().to_csv_rows(model)
    assert [r['Period'] for r in rows] == ['12', '36', 'ecl']
    assert [r['Value'] for r in rows] == ['1.0', '2.0', '3.0']


def test_roundtrip_exact_all_four_groups() -> None:
    m = ExpensesMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(API))
    # 'Rate Type'/'Rate Rows Calculation Method' are documented as never
    # round-tripping (always blanked in the CSV) -- strip before comparing.
    assert _strip_rate_fields(rebuilt['variableExpenses']) == _strip_rate_fields(API['variableExpenses'])
    assert _strip_rate_fields(rebuilt['fixedExpenses']) == _strip_rate_fields(API['fixedExpenses'])
    assert _strip_rate_fields(rebuilt['carbonExpenses']) == _strip_rate_fields(API['carbonExpenses'])
    assert _strip_rate_fields(rebuilt['waterDisposal']) == _strip_rate_fields(API['waterDisposal'])
    assert rebuilt['name'] == API['name']
    assert rebuilt['unique'] == API['unique']


def test_roundtrip_non_canonical_terminal_offset_is_not_exact() -> None:
    """Documented non-exactness: a leaf's terminal offsetToFpd is only recoverable
    exactly if it happens to equal the inverse canonical placeholder (1200). A
    real, verified terminal offset like 1104 does NOT round-trip -- it comes back
    as 1200 instead, not its original value."""
    model: Dict[str, Any] = {
        'name': 'NON CANONICAL TERMINAL',
        'unique': False,
        'variableExpenses': {
            'oil': {
                'processing': _leaf([{'offsetToFpd': 1104, 'dollarPerBbl': 1.0}]),
            },
        },
    }
    mapper = ExpensesMapper()
    rebuilt = mapper.from_csv_rows(mapper.to_csv_rows(model))
    rebuilt_offset = rebuilt['variableExpenses']['oil']['processing']['rows'][0]['offsetToFpd']
    assert rebuilt_offset == 1200
    assert rebuilt_offset != 1104


def test_common_columns_present() -> None:
    rows = ExpensesMapper().to_csv_rows(API)
    assert rows[0]['Model Name'] == 'OPEX'
    assert rows[0]['Model Type'] == 'project'


def test_roundtrip_variable_only_exact_no_injected_empty_groups() -> None:
    """A model with only variableExpenses must round-trip without from_csv_rows
    injecting empty fixedExpenses/carbonExpenses/waterDisposal containers -- those
    groups never existed on the source model and shouldn't be fabricated."""
    m: Dict[str, Any] = {
        'name': 'VAR ONLY',
        'unique': True,
        'variableExpenses': {
            'oil': {
                'processing': _leaf(
                    [{'offsetToFpd': 1200, 'dollarPerBbl': 0}],
                    description='OPC/OIL',
                ),
            },
        },
    }
    mapper = ExpensesMapper()
    rebuilt = mapper.from_csv_rows(mapper.to_csv_rows(m))
    assert _strip_rate_fields(rebuilt['variableExpenses']) == _strip_rate_fields(m['variableExpenses'])
    assert rebuilt['name'] == m['name']
    assert rebuilt['unique'] == m['unique']
    assert 'fixedExpenses' not in rebuilt
    assert 'carbonExpenses' not in rebuilt
    assert 'waterDisposal' not in rebuilt


def test_to_csv_rows_gas_dollar_per_mmbtu_maps_and_round_trips() -> None:
    """Regression (drift audit, 146/297 real Expenses models crashed): `dollarPerMmbtu`
    is a real, previously-unmodeled gas variable-expense value key -- verified live
    (project 'Sample Project A', models 'Sample Model | Bid' et al.) and against the
    real Expenses.csv export (Unit '$/mmbtu')."""
    model: Dict[str, Any] = {
        'name': 'GAS MMBTU',
        'unique': False,
        'variableExpenses': {
            'gas': {
                'marketing': _leaf(
                    [{'entireWellLife': 'Flat', 'dollarPerMmbtu': 0.05}],
                    description='MKT/GAS',
                ),
            },
        },
    }
    mapper = ExpensesMapper()
    rows = mapper.to_csv_rows(model)
    gas_mkt = next(r for r in rows if r['Key'] == 'gas' and r['Category'] == 'mkt')
    assert gas_mkt['Criteria'] == 'flat'
    assert gas_mkt['Unit'] == '$/mmbtu'
    assert gas_mkt['Value'] == '0.05'

    rebuilt = mapper.from_csv_rows(rows)
    assert _strip_rate_fields(rebuilt['variableExpenses']) == _strip_rate_fields(model['variableExpenses'])


def test_to_csv_rows_fixed_expense_per_well_maps_and_round_trips() -> None:
    """Regression (drift audit): `fixedExpensePerWell` is a real, previously-unmodeled
    fixedExpenses value key -- verified live (project 'Sample Project A', model
    'Sample Unit | Bid', fixedExpenses.monthlyWellCost row
    `{'dates': '2000-01-01', 'fixedExpensePerWell': 9840}`) and against the real
    Expenses.csv export (Unit '$/well/month', Criteria 'dates', Period '01/01/2000')."""
    model: Dict[str, Any] = {
        'name': 'FIXED PER WELL',
        'unique': False,
        'fixedExpenses': {
            'monthlyWellCost': _leaf(
                [{'dates': '2000-01-01', 'fixedExpensePerWell': 9840}],
                description='OPC/OGW',
                shrinkageCondition=None,
                rateType=None,
                rowsCalculationMethod=None,
                stopAtEconLimit=True,
                expenseBeforeFpd=True,
            ),
        },
    }
    mapper = ExpensesMapper()
    rows = mapper.to_csv_rows(model)
    fixed = next(r for r in rows if r['Key'] == 'fixed')
    assert fixed['Category'] == 'fixed1'
    assert fixed['Criteria'] == 'dates'
    assert fixed['Period'] == '01/01/2000'
    assert fixed['Unit'] == '$/well/month'
    assert fixed['Value'] == '9840.0'

    rebuilt = mapper.from_csv_rows(rows)
    assert _strip_rate_fields(rebuilt['fixedExpenses']) == _strip_rate_fields(model['fixedExpenses'])


def test_to_csv_rows_water_disposal_dates_criteria_maps_and_round_trips() -> None:
    """Regression (drift audit): a leaf's rows can use `dates` (dated criteria)
    instead of `entireWellLife`/`offsetToFpd` -- verified live (project 'Sample Project A', model 'Sample Unit | Bid', waterDisposal rows
    `{'dates': '2000-01-01', 'dollarPerBbl': 1.155}` /
    `{'dates': '2025-01-01', 'dollarPerBbl': 0.838}`). Also proves the fpd-only
    terminal-row 'ecl' rule does not apply to 'dates' rows, even for the last row of
    the leaf (verified against the real Expenses.csv export, which never renders
    'ecl' for a 'dates' row)."""
    model: Dict[str, Any] = {
        'name': 'WATER DATES',
        'unique': False,
        'waterDisposal': _leaf(
            [
                {'dates': '2000-01-01', 'dollarPerBbl': 1.155},
                {'dates': '2025-01-01', 'dollarPerBbl': 0.838},
            ],
            shrinkageCondition=None,
            escalationModel=None,
            rateType=None,
            rowsCalculationMethod=None,
        ),
    }
    mapper = ExpensesMapper()
    rows = mapper.to_csv_rows(model)
    water_rows = [r for r in rows if r['Key'] == 'water']
    assert [r['Criteria'] for r in water_rows] == ['dates', 'dates']
    assert [r['Period'] for r in water_rows] == ['01/01/2000', '01/01/2025']
    assert [r['Value'] for r in water_rows] == ['1.155', '0.838']
    assert [r['Unit'] for r in water_rows] == ['$/bbl', '$/bbl']

    rebuilt = mapper.from_csv_rows(rows)
    assert _strip_rate_fields(rebuilt['waterDisposal']) == _strip_rate_fields(model['waterDisposal'])


def test_no_value_key_bbl_leaf_falls_back_to_zero_dollar_per_bbl() -> None:
    """Regression (drift audit, model 'Sample Model | Bid', project 'Sample Project A | AFE'): a real API row for a $/bbl-denominated leaf (oil/ngl/drip-cond
    variable expenses, water disposal) can omit EVERY value key entirely --
    `{'entireWellLife': 'Flat'}` with no dollarPerBbl/etc at all. The real Expenses.csv
    export still renders these as Value '0' Unit '$/bbl' (not blank/skipped), so the
    forward mapper must not raise. Covers oil/ngl/dripCondensate/water, the only Keys
    verified live to exhibit this."""
    model: Dict[str, Any] = {
        'name': 'NO VALUE KEY',
        'unique': False,
        'variableExpenses': {
            'oil': {'gathering': _leaf([{'entireWellLife': 'Flat'}])},
            'ngl': {'marketing': _leaf([{'entireWellLife': 'Flat'}])},
            'dripCondensate': {'other': _leaf([{'entireWellLife': 'Flat'}])},
        },
        'waterDisposal': _leaf([{'entireWellLife': 'Flat'}]),
    }
    rows = ExpensesMapper().to_csv_rows(model)
    for key, category in [('oil', 'g&p'), ('ngl', 'mkt'), ('drip cond', 'other'), ('water', '')]:
        row = next(r for r in rows if r['Key'] == key and r['Category'] == category)
        assert row['Criteria'] == 'flat'
        assert row['Value'] == '0.0'
        assert row['Unit'] == '$/bbl'


def test_no_value_key_gas_leaf_still_raises() -> None:
    """The no-value fallback is scoped to the verified $/bbl-denominated Keys
    (oil/ngl/drip cond/water) only -- a gas (or fixed/carbon) leaf with no value key
    at all has never been observed live, so guessing a fallback unit ($/mcf vs
    $/mmbtu) would risk silently misreporting the value's real unit. Must still
    raise."""
    model: Dict[str, Any] = {
        'name': 'NO VALUE KEY GAS',
        'unique': False,
        'variableExpenses': {'gas': {'gathering': _leaf([{'entireWellLife': 'Flat'}])}},
    }
    with pytest.raises(NotImplementedError, match='Unknown expense row value'):
        ExpensesMapper().to_csv_rows(model)


def test_carbon_scalar_only_warns_and_emits_no_rows() -> None:
    """carbonExpenses.category is a scalar with no CSV column. If it's the only
    thing present (no species leaves), the block can't be represented in the CSV
    at all -- to_csv_rows should warn rather than silently dropping it."""
    m: Dict[str, Any] = {
        'name': 'CARBON SCALAR ONLY',
        'unique': False,
        'carbonExpenses': {'category': 'co2e'},
    }
    mapper = ExpensesMapper()
    with pytest.warns(UserWarning, match='carbonExpenses'):
        rows = mapper.to_csv_rows(m)
    assert not any(r['Key'] in ('ch4', 'co2', 'co2e', 'n2o') for r in rows)
