from typing import Any

import pytest

from combocurve_api_helper.econ_models.production_taxes import ProductionTaxesMapper


def _severance_row(phase: str, unit: str, value: float) -> dict[str, Any]:
    """FULL API shape for a severance_tax row. Note there is NO 'deductSeveranceTax' key
    at all -- that field only ever appears on ad_val_tax rows."""
    return {
        'key': phase,
        'category': 'severance_tax',
        'criteria': 'entire_well_life',
        'period': ['Flat'],
        'value': [value],
        'unit': unit,
        'shrinkageCondition': 'shrunk',
        'escalation': 'none',
        'calculation': 'nri',
        'rateType': 'gross_well_head',
        'rateRowsCalculationMethod': 'non_monotonic',
    }


def _ad_valorem_row(value: float, deduct_severance_tax: bool) -> dict[str, Any]:
    """FULL API shape for an ad_val_tax row. 'category' is 'ad_val_tax'; the constant,
    recoverable 'key' is 'ad_valorem_tax'. Unlike severance rows, ad valorem rows always
    carry 'deductSeveranceTax'."""
    return {
        'key': 'ad_valorem_tax',
        'category': 'ad_val_tax',
        'criteria': 'entire_well_life',
        'period': ['Flat'],
        'value': [value],
        'unit': 'pct_of_revenue',
        'shrinkageCondition': 'shrunk',
        'escalation': 'none',
        'calculation': 'nri',
        'deductSeveranceTax': deduct_severance_tax,
        'rateType': 'gross_well_head',
        'rateRowsCalculationMethod': 'non_monotonic',
    }


NEW_MEXICO: dict[str, Any] = {
    'id': 'pt-nm',
    'name': 'NM Prod Tax',
    'unique': False,
    'createdAt': '2026-05-10T03:11:41.000Z',
    'updatedAt': '2026-05-10T03:11:41.000Z',
    'econModelType': 'ProductionTaxes',
    'data': {
        'state': 'new_mexico',
        'rows': [
            _ad_valorem_row(5, False),
            _severance_row('oil', 'pct_of_revenue', 7.09),
            _severance_row('gas', 'pct_of_revenue', 7.94),
            _severance_row('ngl', 'pct_of_revenue', 7.94),
            _severance_row('drip_condensate', 'pct_of_revenue', 7.09),
        ],
    },
}

TEXAS: dict[str, Any] = {
    'id': 'pt-tx',
    'name': 'TX Prod Tax',
    'unique': False,
    'createdAt': '2026-05-10T03:11:41.000Z',
    'updatedAt': '2026-05-10T03:11:41.000Z',
    'econModelType': 'ProductionTaxes',
    'data': {
        'state': 'texas',
        'rows': [
            _severance_row('oil', 'pct_of_revenue', 4.6),
            _severance_row('oil', 'dollar_per_bbl', 0.0081),
            _severance_row('gas', 'pct_of_revenue', 7.5),
            _severance_row('gas', 'dollar_per_mcf', 0.0007),
            _severance_row('ngl', 'pct_of_revenue', 7.5),
            _severance_row('ngl', 'dollar_per_bbl', 0.0001167),
            _severance_row('drip_condensate', 'pct_of_revenue', 4.6),
            _severance_row('drip_condensate', 'dollar_per_bbl', 0.0081),
            _ad_valorem_row(2.5, False),
        ],
    },
}


_DATES_PERIODS = ['1900-01-01', '2023-07-01', '2024-07-01']


def _dates_severance(phase: str, unit: str, values: list[float]) -> dict[str, Any]:
    """API shape for a 'dates'-criteria severance row. period is a list of ISO dates; the
    first is CC's 1900-01-01 schedule-start sentinel."""
    return {
        'key': phase,
        'category': 'severance_tax',
        'criteria': 'dates',
        'period': list(_DATES_PERIODS),
        'value': list(values),
        'unit': unit,
        'shrinkageCondition': 'shrunk',
        'escalation': 'none',
        'calculation': 'nri',
        'rateType': 'gross_well_head',
        'rateRowsCalculationMethod': 'non_monotonic',
    }


DATES: dict[str, Any] = {
    'id': 'pt-nd',
    'name': 'SAMPLE PDP STREAM',
    'unique': False,
    'createdAt': '2026-05-10T03:11:41.000Z',
    'updatedAt': '2026-05-10T03:11:41.000Z',
    'econModelType': 'ProductionTaxes',
    'data': {
        'state': 'custom',
        'rows': [
            _dates_severance('oil', 'pct_of_revenue', [9.4, 9.4, 9.4]),
            _dates_severance('oil', 'dollar_per_bbl', [0, 0, 0]),
            _dates_severance('gas', 'pct_of_revenue', [0, 0, 0]),
            _dates_severance('gas', 'dollar_per_mcf', [0.0753, 0.0753, 0.0753]),
        ],
    },
}


def test_dates_criteria_matches_cc_export() -> None:
    """CC renders a 'dates' Period as 'MM/YYYY' ('07/2023'); the 1900-01-01 sentinel is
    '01/1900' (raw export, fixtures/production_taxes_criteria.csv)."""
    rows = ProductionTaxesMapper().to_row_dicts(DATES)
    assert len(rows) == 12  # 4 API rows x 3 periods

    oil_t1 = [r for r in rows if r['Key'] == 'oil' and r['Category'] == 'Severance Tax 1']
    assert [r['Criteria'] for r in oil_t1] == ['dates', 'dates', 'dates']
    assert [r['Period'] for r in oil_t1] == ['01/1900', '07/2023', '07/2024']
    assert [r['Value'] for r in oil_t1] == ['9.4', '9.4', '9.4']
    assert [r['Unit'] for r in oil_t1] == ['% of rev', '% of rev', '% of rev']

    gas_t2 = [r for r in rows if r['Key'] == 'gas' and r['Category'] == 'Severance Tax 2']
    assert [r['Period'] for r in gas_t2] == ['01/1900', '07/2023', '07/2024']
    assert [r['Value'] for r in gas_t2] == ['0.0753', '0.0753', '0.0753']
    assert [r['Unit'] for r in gas_t2] == ['$/mcf', '$/mcf', '$/mcf']


def test_dates_criteria_roundtrip() -> None:
    m = ProductionTaxesMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(DATES))
    assert rebuilt['data'] == DATES['data']


def test_dates_keep_the_century() -> None:
    """1976-01-01 and 2000-01-01 occur in live data; 'MM/YYYY' keeps both, where the old
    '%b-%y' form read them back as 2076-01-01 and 1900-01-01."""
    model: dict[str, Any] = {
        'name': 'Sample Dates Century Check',
        'unique': False,
        'data': {'state': 'custom', 'rows': [_dates_severance('oil', 'pct_of_revenue', [4.6, 4.7, 4.8])]},
    }
    model['data']['rows'][0]['period'] = ['1976-01-01', '2000-01-01', '2023-07-01']
    m = ProductionTaxesMapper()
    rows = m.to_row_dicts(model)
    assert [row['Period'] for row in rows] == ['01/1976', '01/2000', '07/2023']
    assert m.from_row_dicts(rows)['data'] == model['data']


def test_dates_legacy_month_abbreviation_still_reads() -> None:
    """CSVs written by 2.5.0 and earlier carry '%b-%y'; 'Jan-00' is the 1900 sentinel."""
    rows = ProductionTaxesMapper().to_row_dicts(DATES)
    legacy_periods = {'01/1900': 'Jan-00', '07/2023': 'Jul-23', '07/2024': 'Jul-24'}
    for row in rows:
        row['Period'] = legacy_periods[row['Period']]
    assert ProductionTaxesMapper().from_row_dicts(rows)['data'] == DATES['data']


def test_to_row_dicts_new_mexico_real_shape() -> None:
    rows = ProductionTaxesMapper().to_row_dicts(NEW_MEXICO)
    assert len(rows) == 5

    ad_val = next(r for r in rows if r['Key'] == 'Ad Valorem Tax')
    assert ad_val['Category'] == 'Ad Val Tax'
    assert ad_val['Criteria'] == 'flat'
    assert ad_val['Period'] == ''
    assert ad_val['Value'] == '5.0'
    assert ad_val['Unit'] == '% of rev'
    assert ad_val['Deduct Severance Tax'] == 'no'

    for phase_csv, value in [('oil', '7.09'), ('gas', '7.94'), ('ngl', '7.94'), ('drip cond', '7.09')]:
        row = next(r for r in rows if r['Key'] == phase_csv)
        assert row['Category'] == 'Severance Tax'
        assert row['Criteria'] == 'flat'
        assert row['Period'] == ''
        assert row['Value'] == value
        assert row['Unit'] == '% of rev'

    for r in rows:
        assert r['Production Taxes State'] == 'new_mexico'
        assert r['Stream Type'] == ''
        assert r['Description'] == ''
        assert r['Shrinkage Condition'] == 'shrunk'
        assert r['Escalation'] == 'None'
        assert r['Calculation'] == 'nri'
        assert r['Rate Type'] == 'gross well head'
        assert r['Rate Rows Calculation Method'] == 'non monotonic'


def test_roundtrip_exact_new_mexico() -> None:
    m = ProductionTaxesMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(NEW_MEXICO))
    assert rebuilt['data'] == NEW_MEXICO['data']
    assert rebuilt['name'] == NEW_MEXICO['name']
    assert rebuilt['unique'] == NEW_MEXICO['unique']
    # Severance rows never carry 'deductSeveranceTax' at all; ad valorem rows always do.
    for row in rebuilt['data']['rows']:
        if row['category'] == 'severance_tax':
            assert 'deductSeveranceTax' not in row
        else:
            assert row['category'] == 'ad_val_tax'
            assert 'deductSeveranceTax' in row
        # Escalation/rateType come back in raw API form, not CSV display form.
        assert row['escalation'] == 'none'
        assert row['rateType'] == 'gross_well_head'
        assert row['rateRowsCalculationMethod'] == 'non_monotonic'


def test_to_row_dicts_texas_two_severance_per_phase() -> None:
    rows = ProductionTaxesMapper().to_row_dicts(TEXAS)
    assert len(rows) == 9

    oil_rows = [r for r in rows if r['Key'] == 'oil']
    assert [r['Category'] for r in oil_rows] == ['Severance Tax 1', 'Severance Tax 2']
    assert (oil_rows[0]['Unit'], oil_rows[0]['Value']) == ('% of rev', '4.6')
    assert (oil_rows[1]['Unit'], oil_rows[1]['Value']) == ('$/bbl', '0.0081')

    gas_rows = [r for r in rows if r['Key'] == 'gas']
    assert [r['Category'] for r in gas_rows] == ['Severance Tax 1', 'Severance Tax 2']
    assert (gas_rows[0]['Unit'], gas_rows[0]['Value']) == ('% of rev', '7.5')
    assert (gas_rows[1]['Unit'], gas_rows[1]['Value']) == ('$/mcf', '0.0007')

    ngl_rows = [r for r in rows if r['Key'] == 'ngl']
    assert [r['Category'] for r in ngl_rows] == ['Severance Tax 1', 'Severance Tax 2']
    assert (ngl_rows[0]['Unit'], ngl_rows[0]['Value']) == ('% of rev', '7.5')
    assert (ngl_rows[1]['Unit'], ngl_rows[1]['Value']) == ('$/bbl', '0.0001167')

    drip_rows = [r for r in rows if r['Key'] == 'drip cond']
    assert [r['Category'] for r in drip_rows] == ['Severance Tax 1', 'Severance Tax 2']
    assert (drip_rows[0]['Unit'], drip_rows[0]['Value']) == ('% of rev', '4.6')
    assert (drip_rows[1]['Unit'], drip_rows[1]['Value']) == ('$/bbl', '0.0081')

    ad_val = next(r for r in rows if r['Key'] == 'Ad Valorem Tax')
    assert ad_val['Category'] == 'Ad Val Tax'
    assert ad_val['Value'] == '2.5'
    assert ad_val['Deduct Severance Tax'] == 'no'

    for r in rows:
        assert r['Production Taxes State'] == 'texas'
        assert r['Stream Type'] == ''
        assert r['Description'] == ''
        assert r['Criteria'] == 'flat'
        assert r['Period'] == ''
        assert r['Shrinkage Condition'] == 'shrunk'
        assert r['Escalation'] == 'None'
        assert r['Calculation'] == 'nri'
        assert r['Rate Type'] == 'gross well head'
        assert r['Rate Rows Calculation Method'] == 'non monotonic'


def test_roundtrip_exact_texas() -> None:
    m = ProductionTaxesMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(TEXAS))
    assert rebuilt['data'] == TEXAS['data']
    assert rebuilt['name'] == TEXAS['name']
    assert rebuilt['unique'] == TEXAS['unique']
    for row in rebuilt['data']['rows']:
        if row['category'] == 'severance_tax':
            assert 'deductSeveranceTax' not in row
        else:
            assert row['category'] == 'ad_val_tax'
            assert 'deductSeveranceTax' in row


def test_fpd_criteria_period_roundtrip() -> None:
    """Live `offset_to_fpd` periods are integers (2,966 of 2,966 live rows); the inverse
    must give integers back, not the CSV strings."""
    model: dict[str, Any] = {
        'name': 'FPD offset',
        'unique': False,
        'data': {
            'state': 'colorado',
            'rows': [
                {
                    'key': 'oil',
                    'category': 'severance_tax',
                    'unit': 'pct_of_revenue',
                    'criteria': 'offset_to_fpd',
                    'period': [36, 1164],
                    'value': [3.0, 4.6],
                },
            ],
        },
    }
    m = ProductionTaxesMapper()
    rows = m.to_row_dicts(model)
    assert [row['Criteria'] for row in rows] == ['fpd', 'fpd']
    assert [row['Period'] for row in rows] == ['36', '1164']

    rebuilt = m.from_row_dicts(rows)
    assert rebuilt['data'] == model['data']


_SEVERANCE_PHASES = ['oil', 'gas', 'ngl', 'drip_condensate']
# CC's API accepts oil_rate and gas_rate on severance rows, and water_rate on ad valorem rows
# only ("criteria water_rate can only be specified when category is ad_val_tax").
_SEVERANCE_RATE_CRITERIA_TO_CSV = {'oil_rate': 'oil rate', 'gas_rate': 'gas rate'}


def _rate_row(key: str, category: str, criteria: str, period: list[Any], value: list[Any], unit: str) -> dict[str, Any]:
    """Live rate-criteria shape: integer thresholds starting at 0, one value per threshold.
    CC allows `shrinkageCondition` only on $/bbl and $/mcf rows."""
    row: dict[str, Any] = {
        'key': key,
        'category': category,
        'criteria': criteria,
        'period': period,
        'value': value,
        'unit': unit,
        'escalation': 'none',
        'calculation': 'nri',
        'rateType': 'gross_well_head',
        'rateRowsCalculationMethod': 'non_monotonic',
    }
    if unit in ('dollar_per_bbl', 'dollar_per_mcf'):
        row['shrinkageCondition'] = 'shrunk'
    return row


def _severance_rate_model(criteria: str, phase: str) -> dict[str, Any]:
    per_unit = 'dollar_per_mcf' if phase == 'gas' else 'dollar_per_bbl'
    return {
        'name': 'Sample Rate Tax',
        'unique': False,
        'data': {
            'state': 'custom',
            'rows': [
                _rate_row(phase, 'severance_tax', criteria, [0, 30], [7.5, 10], 'pct_of_revenue'),
                _rate_row(phase, 'severance_tax', criteria, [30], [0.0905], per_unit),
            ],
        },
    }


@pytest.mark.parametrize('phase', _SEVERANCE_PHASES)
@pytest.mark.parametrize('criteria', sorted(_SEVERANCE_RATE_CRITERIA_TO_CSV))
def test_severance_rate_criteria_roundtrip(criteria: str, phase: str) -> None:
    model = _severance_rate_model(criteria, phase)
    m = ProductionTaxesMapper()
    rows = m.to_row_dicts(model)
    assert [row['Criteria'] for row in rows] == [_SEVERANCE_RATE_CRITERIA_TO_CSV[criteria]] * 3
    assert [row['Period'] for row in rows] == ['0', '30', '30']
    assert [row['Value'] for row in rows] == ['7.5', '10.0', '0.0905']
    assert [row['Category'] for row in rows] == ['Severance Tax 1', 'Severance Tax 1', 'Severance Tax 2']

    rebuilt = m.from_row_dicts(rows)
    assert rebuilt['data'] == model['data']


@pytest.mark.parametrize('phase', _SEVERANCE_PHASES)
@pytest.mark.parametrize('criteria', sorted(_SEVERANCE_RATE_CRITERIA_TO_CSV))
def test_severance_rate_criteria_csv_text_roundtrip(criteria: str, phase: str) -> None:
    model = _severance_rate_model(criteria, phase)
    m = ProductionTaxesMapper()
    rebuilt = m.from_csv(m.to_csv([model]))
    assert [rebuilt_model['data'] for rebuilt_model in rebuilt] == [model['data']]


def test_ad_valorem_water_rate_roundtrip() -> None:
    """Two ad valorem water_rate rows, % of revenue and $/boe, as in the raw export."""
    rows_api = [
        _rate_row('ad_valorem_tax', 'ad_val_tax', 'water_rate', [0, 200], [2.5, 1.5], 'pct_of_revenue'),
        _rate_row('ad_valorem_tax', 'ad_val_tax', 'water_rate', [0, 200], [0.4, 0.6], 'dollar_per_boe'),
    ]
    for row in rows_api:
        row['deductSeveranceTax'] = True
    model: dict[str, Any] = {
        'name': 'Sample Water Rate',
        'unique': False,
        'data': {'state': 'custom', 'rows': rows_api},
    }
    m = ProductionTaxesMapper()
    rows = m.to_row_dicts(model)
    assert [row['Criteria'] for row in rows] == ['water rate'] * 4
    assert [row['Category'] for row in rows] == ['Ad Val Tax 1', 'Ad Val Tax 1', 'Ad Val Tax 2', 'Ad Val Tax 2']
    assert [row['Unit'] for row in rows] == ['% of rev', '% of rev', '$/boe', '$/boe']
    assert m.from_row_dicts(rows)['data'] == model['data']


@pytest.mark.parametrize(
    ('criteria', 'criteria_csv'),
    [
        ('offset_to_as_of_date', 'as of'),
        ('offset_to_discount_date', 'disc date'),
        ('offset_to_first_segment', 'maj seg'),
        ('offset_to_end_history', 'end hist'),
    ],
)
def test_offset_criteria_roundtrip(criteria: str, criteria_csv: str) -> None:
    """Integer month offsets, as in the live `offset_to_as_of_date` rows."""
    model: dict[str, Any] = {
        'name': 'Sample Offset Tax',
        'unique': False,
        'data': {
            'state': 'custom',
            'rows': [
                {
                    'key': 'ngl',
                    'category': 'severance_tax',
                    'criteria': criteria,
                    'period': [36, 1164],
                    'value': [0, 8.5],
                    'unit': 'pct_of_revenue',
                    'escalation': 'none',
                    'calculation': 'nri',
                },
            ],
        },
    }
    m = ProductionTaxesMapper()
    rows = m.to_row_dicts(model)
    assert [row['Criteria'] for row in rows] == [criteria_csv, criteria_csv]
    assert [row['Period'] for row in rows] == ['36', '1164']
    assert m.from_row_dicts(rows)['data'] == model['data']


def test_per_month_unit_roundtrip() -> None:
    model: dict[str, Any] = {
        'name': 'Sample Unit Tax',
        'unique': False,
        'data': {'state': 'custom', 'rows': [_severance_row('oil', 'dollar_per_month', 125)]},
    }
    m = ProductionTaxesMapper()
    rows = m.to_row_dicts(model)
    assert rows[0]['Unit'] == '$/month'
    assert m.from_row_dicts(rows)['data'] == model['data']


def test_two_ad_valorem_rows_stay_two_rows() -> None:
    """Live models carry two ad valorem rows (% of revenue plus $/month or $/boe). They are
    numbered like two severance rows of one phase, so the inverse does not merge them."""
    per_month = _ad_valorem_row(0, True)
    per_month['unit'] = 'dollar_per_month'
    per_month['value'] = [466.5]
    model: dict[str, Any] = {
        'name': 'Sample Two Ad Valorem',
        'unique': False,
        'data': {
            'state': 'custom',
            'rows': [_ad_valorem_row(2.33, True), per_month, _severance_row('oil', 'pct_of_revenue', 4.6)],
        },
    }
    m = ProductionTaxesMapper()
    rows = m.to_row_dicts(model)
    assert [row['Category'] for row in rows] == ['Ad Val Tax 1', 'Ad Val Tax 2', 'Severance Tax']
    assert [row['Key'] for row in rows] == ['Ad Valorem Tax', 'Ad Valorem Tax', 'oil']
    assert m.from_row_dicts(rows)['data'] == model['data']


def test_null_value_roundtrip() -> None:
    """Live flat rows can carry `value: [null]` (13 live models). CC's export writes that
    Value as 'nan' (fixtures/production_taxes_null_value.csv); it reads back as null."""
    model: dict[str, Any] = {
        'name': 'Sample Blank Tax',
        'unique': False,
        'data': {'state': 'custom', 'rows': [_severance_row('oil', 'pct_of_revenue', 7.5)]},
    }
    model['data']['rows'][0]['value'] = [None]
    m = ProductionTaxesMapper()
    rows = m.to_row_dicts(model)
    assert rows[0]['Value'] == 'nan'
    assert m.from_row_dicts(rows)['data'] == model['data']


def test_blank_value_reads_as_null() -> None:
    """A blank Value also reads as null (2.6.0 development builds wrote it)."""
    model: dict[str, Any] = {
        'name': 'Sample Blank Tax',
        'unique': False,
        'data': {'state': 'custom', 'rows': [_severance_row('oil', 'pct_of_revenue', 7.5)]},
    }
    model['data']['rows'][0]['value'] = [None]
    m = ProductionTaxesMapper()
    rows = m.to_row_dicts(model)
    rows[0]['Value'] = ''
    assert m.from_row_dicts(rows)['data'] == model['data']


def test_optional_fields_pass_through_when_present() -> None:
    model: dict[str, Any] = {
        'name': 'Passthrough',
        'unique': False,
        'data': {
            'state': 'oklahoma',
            'rows': [
                {
                    'key': 'oil',
                    'category': 'severance_tax',
                    'unit': 'dollar_per_mcf',
                    'criteria': 'entire_well_life',
                    'period': ['Flat'],
                    'value': [0.05],
                    'shrinkageCondition': 'shrunk',
                    'escalation': 'none',
                    'calculation': 'wi',
                    'rateType': 'gross_well_head',
                    'rateRowsCalculationMethod': 'monotonic',
                },
            ],
        },
    }
    m = ProductionTaxesMapper()
    rows = m.to_row_dicts(model)
    row = rows[0]
    assert row['Shrinkage Condition'] == 'shrunk'
    assert row['Escalation'] == 'None'
    assert row['Calculation'] == 'wi'
    assert row['Rate Type'] == 'gross well head'
    assert row['Rate Rows Calculation Method'] == 'monotonic'
    assert row['Unit'] == '$/mcf'

    rebuilt = m.from_row_dicts(rows)
    assert rebuilt['data'] == model['data']


def test_optional_fields_absent_are_not_injected() -> None:
    # A genuinely minimal row -- no shrinkageCondition/escalation/calculation/rateType/
    # rateRowsCalculationMethod/deductSeveranceTax at all -- must round-trip without any
    # of those keys getting injected.
    model: dict[str, Any] = {
        'name': 'Minimal',
        'unique': False,
        'data': {
            'state': 'louisiana',
            'rows': [
                {
                    'key': 'gas',
                    'category': 'severance_tax',
                    'criteria': 'entire_well_life',
                    'period': ['Flat'],
                    'value': [12.5],
                    'unit': 'pct_of_revenue',
                },
            ],
        },
    }
    m = ProductionTaxesMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(model))
    row = rebuilt['data']['rows'][0]
    assert 'shrinkageCondition' not in row
    assert 'escalation' not in row
    assert 'calculation' not in row
    assert 'rateType' not in row
    assert 'rateRowsCalculationMethod' not in row
    assert 'deductSeveranceTax' not in row
    assert rebuilt['data'] == model['data']


def test_unknown_category_raises() -> None:
    model: dict[str, Any] = {
        'name': 'Bad',
        'unique': False,
        'data': {
            'state': 'texas',
            'rows': [
                {
                    'key': 'oil',
                    'category': 'unknown_tax',
                    'unit': 'pct_of_revenue',
                    'criteria': 'entire_well_life',
                    'period': ['Flat'],
                    'value': [1.0],
                    'deductSeveranceTax': None,
                },
            ],
        },
    }
    with pytest.raises(NotImplementedError):
        ProductionTaxesMapper().to_row_dicts(model)


def test_unknown_criteria_raises() -> None:
    model: dict[str, Any] = {
        'name': 'Bad',
        'unique': False,
        'data': {
            'state': 'texas',
            'rows': [_severance_row('oil', 'pct_of_revenue', 1.0)],
        },
    }
    model['data']['rows'][0]['criteria'] = 'some_weird_criteria'
    with pytest.raises(NotImplementedError):
        ProductionTaxesMapper().to_row_dicts(model)


def test_common_columns_present() -> None:
    rows = ProductionTaxesMapper().to_row_dicts(TEXAS)
    assert rows[0]['Model Name'] == 'TX Prod Tax'
    assert rows[0]['Model Type'] == 'project'
