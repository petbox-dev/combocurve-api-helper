from typing import Any, Dict, List

import pytest
from pydantic import ValidationError

from combocurve_api_helper.econ_models.stream_properties import StreamPropertiesMapper

API: Dict[str, Any] = {
    'id': 'sp1',
    'name': 'Sample Stream | Bid',
    'unique': False,
    'createdAt': '2026-01-09T20:47:16.856Z',
    'updatedAt': '2026-01-09T20:47:16.856Z',
    'econModelType': 'StreamProperties',
    'yields': {
        'rateType': 'gross_well_head',
        'rowsCalculationMethod': 'non_monotonic',
        'ngl': {'rows': [{'entireWellLife': 'Flat', 'unshrunkGas': 'Unshrunk Gas', 'yield': 99.67364}]},
        'dripCondensate': {'rows': [{'entireWellLife': 'Flat', 'unshrunkGas': 'Unshrunk Gas', 'yield': 0}]},
    },
    'shrinkage': {
        'rateType': 'gross_well_head',
        'rowsCalculationMethod': 'non_monotonic',
        'oil': {'rows': [{'entireWellLife': 'Flat', 'pctRemaining': 100}]},
        'gas': {'rows': [{'entireWellLife': 'Flat', 'pctRemaining': 71.7}]},
    },
    'lossFlare': {
        'rateType': 'gross_well_head',
        'rowsCalculationMethod': 'non_monotonic',
        'oilLoss': {'rows': [{'entireWellLife': 'Flat', 'pctRemaining': 100}]},
        'gasLoss': {'rows': [{'entireWellLife': 'Flat', 'pctRemaining': 100}]},
        'gasFlare': {'rows': [{'entireWellLife': 'Flat', 'pctRemaining': 100}]},
    },
    # CC's real Stream Properties CSV export has NO 'btu'-Key rows at all (blank 'BTU
    # (MBTU/MCF)' column) even though the API model carries btuContent. Kept here (with
    # a non-empty value) specifically to prove to_csv_rows drops it rather than emitting
    # 'btu' rows.
    'btuContent': {'unshrunkGas': 1000, 'shrunkGas': 1000},
    'companyCustomStreams': [],
}

_BLANK_COLS = (
    'Yield Source',
    'Yield (BBL/MMCF)',
    'Mol %',
    'Gal/lb-mol Factor',
    'Plant Eff (%)',
    'Shrink (% Remaining)',
    'BTU (MBTU/MCF)',
    'Post Extraction (%)',
)


def test_to_csv_rows_values() -> None:
    rows = StreamPropertiesMapper().to_csv_rows(API)
    # 2 yields + 2 shrinkage + 3 lossFlare = 7. NOT 9: btuContent is dropped entirely,
    # matching CC's real export (no 'btu'-Key rows).
    assert len(rows) == 7
    assert not any(r['Key'] == 'btu' for r in rows)

    ngl = next(r for r in rows if r['Key'] == 'yields' and r['Category'] == 'ngl')
    assert (ngl['Criteria'], ngl['Period'], ngl['Value'], ngl['Unit'], ngl['Gas Shrinkage Condition']) == (
        'flat',
        '',
        '99.67364',
        'bbl/mmcf',
        'unshrunk',
    )
    # 'Rate Type' / 'Rate Rows Calculation Method' are ALWAYS blank, even though the API
    # yields/shrinkage/lossFlare groups carry rateType/rowsCalculationMethod values. Not
    # round-trippable.
    assert (ngl['Rate Type'], ngl['Rate Rows Calculation Method']) == ('', '')

    # 'Value' always renders with a decimal point, e.g. '0.0'/'100.0' not '0'/'100'
    # (unlike Capex/Differentials/ProductionTaxes, which drop the trailing '.0').
    drip = next(r for r in rows if r['Key'] == 'yields' and r['Category'] == 'drip cond')
    assert (drip['Value'], drip['Unit'], drip['Gas Shrinkage Condition']) == ('0.0', 'bbl/mmcf', 'unshrunk')
    assert (drip['Rate Type'], drip['Rate Rows Calculation Method']) == ('', '')

    oil_shrink = next(r for r in rows if r['Key'] == 'shrinkage' and r['Category'] == 'oil')
    assert (oil_shrink['Value'], oil_shrink['Unit']) == ('100.0', '% remaining')
    assert (oil_shrink['Rate Type'], oil_shrink['Rate Rows Calculation Method']) == ('', '')

    gas_shrink = next(r for r in rows if r['Key'] == 'shrinkage' and r['Category'] == 'gas')
    assert (gas_shrink['Value'], gas_shrink['Unit']) == ('71.7', '% remaining')

    oil_loss = next(r for r in rows if r['Key'] == 'loss & flare' and r['Category'] == 'oil loss')
    assert (oil_loss['Value'], oil_loss['Unit']) == ('100.0', '% remaining')
    assert (oil_loss['Rate Type'], oil_loss['Rate Rows Calculation Method']) == ('', '')

    gas_loss = next(r for r in rows if r['Key'] == 'loss & flare' and r['Category'] == 'gas loss')
    assert (gas_loss['Value'], gas_loss['Unit']) == ('100.0', '% remaining')

    gas_flare = next(r for r in rows if r['Key'] == 'loss & flare' and r['Category'] == 'gas flare')
    assert (gas_flare['Value'], gas_flare['Unit']) == ('100.0', '% remaining')

    for r in rows:
        for col in _BLANK_COLS:
            assert r[col] == ''


def test_gas_shrinkage_condition_uses_presence_not_truthiness() -> None:
    # Real ComboCurve API exports carry unshrunkGas = '' (empty string, falsy) on the
    # majority of real ngl yields rows. A truthiness check on r.get('unshrunkGas') wrongly
    # blanks 'Gas Shrinkage Condition' for these; only key presence is the correct signal.
    model: Dict[str, Any] = {
        'name': 'ngl-empty-unshrunk',
        'unique': False,
        'yields': {
            'rateType': 'gross_well_head',
            'rowsCalculationMethod': 'non_monotonic',
            'ngl': {'rows': [{'entireWellLife': 'Flat', 'unshrunkGas': '', 'yield': 7.02}]},
        },
        'companyCustomStreams': [],
    }
    rows = StreamPropertiesMapper().to_csv_rows(model)
    ngl = next(r for r in rows if r['Key'] == 'yields' and r['Category'] == 'ngl')
    assert ngl['Gas Shrinkage Condition'] == 'unshrunk'


def test_csv_rows_roundtrip_exact() -> None:
    # Unlike the API dict round-trip (which loses the exact unshrunkGas literal, plus
    # btuContent and rateType/rowsCalculationMethod entirely -- see test_roundtrip), the
    # CSV representation itself round-trips exactly through from_csv_rows -> to_csv_rows
    # for the stream-properties data columns. 'Last Update' is excluded: it is sourced
    # from the API model's top-level 'updatedAt'/context, which from_csv_rows does not
    # reconstruct -- a separate, pre-existing gap unrelated to this fix.
    def _strip_last_update(rs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return [{k: v for k, v in r.items() if k != 'Last Update'} for r in rs]

    m = StreamPropertiesMapper()
    rows = m.to_csv_rows(API)
    rebuilt_rows = m.to_csv_rows(m.from_csv_rows(rows))
    assert _strip_last_update(rebuilt_rows) == _strip_last_update(rows)


def test_roundtrip() -> None:
    m = StreamPropertiesMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(API))

    # Documented, permanent losses through the real CC CSV (not bugs):
    # - btuContent has no CSV representation at all (no 'btu'-Key rows) -- omitted
    #   entirely from the rebuilt model, like Capex $/ft.
    # - rateType/rowsCalculationMethod are blanked unconditionally in the CSV's
    #   'Rate Type'/'Rate Rows Calculation Method' columns -- never reconstructed.
    assert 'btuContent' not in rebuilt
    for group_key in ('yields', 'shrinkage', 'lossFlare'):
        assert 'rateType' not in rebuilt[group_key]
        assert 'rowsCalculationMethod' not in rebuilt[group_key]

    def _rows_only(group: Dict[str, Any]) -> Dict[str, Any]:
        return {
            category: {'rows': node['rows']}
            for category, node in group.items()
            if category not in ('rateType', 'rowsCalculationMethod')
        }

    # Modulo the documented drops above, yields/shrinkage/lossFlare reproduce exactly.
    assert rebuilt['yields'] == _rows_only(API['yields'])
    assert rebuilt['shrinkage'] == _rows_only(API['shrinkage'])
    assert rebuilt['lossFlare'] == _rows_only(API['lossFlare'])
    assert rebuilt['name'] == API['name'] and rebuilt['unique'] == API['unique']


def test_nonempty_company_custom_streams_raises() -> None:
    m = dict(API)
    m['companyCustomStreams'] = [{'key': 'custom1'}]
    with pytest.raises(NotImplementedError):
        StreamPropertiesMapper().to_csv_rows(m)


def test_unknown_category_key_raises() -> None:
    # Unknown category keys in yields/shrinkage/lossFlare groups should raise ValidationError
    # (via pydantic forbid), not be silently dropped. Maintains parity with other mappers.
    m = dict(API)
    m['shrinkage'] = {
        'rateType': 'gross_well_head',
        'rowsCalculationMethod': 'non_monotonic',
        'oil': {'rows': [{'entireWellLife': 'Flat', 'pctRemaining': 100}]},
        'plutonium': {'rows': [{'entireWellLife': 'Flat', 'pctRemaining': 99}]},  # unknown category
    }
    with pytest.raises(ValidationError):
        StreamPropertiesMapper().to_csv_rows(m)
