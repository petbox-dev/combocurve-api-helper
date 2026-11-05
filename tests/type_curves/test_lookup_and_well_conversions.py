"""Pure lookup-table, lookup-table-id and representative-well conversions."""

import json
from pathlib import Path
from typing import Any, cast

import pytest

from combocurve_api_helper.base import Item
from combocurve_api_helper.type_curve_conversions import (
    lookup_table_from_v1,
    lookup_table_id_from_v1,
    lookup_table_to_v1,
    lookup_table_uses_v1_fields,
    representative_well_from_v2,
)

FIXTURES = Path(__file__).parent / 'fixtures'


def per_phase_table() -> Any:
    return json.loads((FIXTURES / 'v1_lookup_table_per_phase.json').read_text(encoding='utf8'))


def filter_value(rule: Any) -> str:
    return str(rule['filter'][0]['value'])


def test_a_table_with_rules_that_differ_by_phase_is_refused() -> None:
    with pytest.raises(ValueError, match='NM'):
        lookup_table_from_v1(per_phase_table())


def test_rules_that_differ_only_by_phase_collapse_to_one() -> None:
    table = per_phase_table()
    table['rules'] = [rule for rule in table['rules'] if filter_value(rule) != 'NM']

    converted = lookup_table_from_v1(table)

    rules = converted['rules']
    assert isinstance(rules, list)
    assert [filter_value(rule) for rule in rules] == ['TX', 'OK']
    texas, oklahoma = rules
    assert set(texas) == {
        'filter',
        'typeCurve',
        'applySeries',
        'fpdSource',
        'riskFactorPeakOil',
        'riskFactorPeakGas',
        'riskFactorPeakWater',
    }
    assert oklahoma['normalization'] == {'source': 'own'}
    assert oklahoma['riskFactorPeakOil'] == 0.9
    assert oklahoma['fixedDate'] == '2026-01-01'


def test_schedule_first_production_date_has_no_v2_equivalent() -> None:
    table: Item = {'name': 'Sample', 'rules': [{'filter': [], 'fpdSource': 'schedule'}]}

    with pytest.raises(ValueError, match='schedule'):
        lookup_table_from_v1(table)


def test_v1_field_detection() -> None:
    assert lookup_table_uses_v1_fields(per_phase_table())
    assert not lookup_table_uses_v1_fields({'name': 'Sample', 'rules': [{'riskFactorPeakOil': 1}]})


def test_lookup_table_to_v1_renames_back() -> None:
    table: Item = {'name': 'Sample', 'rules': [{'riskFactorPeakGas': 0.5, 'normalization': {'source': 'own'}}]}

    assert lookup_table_to_v1(table)['rules'] == [{'riskFactorGas': 0.5, 'applyNormalization': True}]


def test_lookup_table_to_v1_refuses_a_shared_normalization() -> None:
    table: Item = {'name': 'Sample', 'rules': [{'normalization': {'source': 'shared', 'preset': 'x'}}]}

    with pytest.raises(ValueError, match='shared'):
        lookup_table_to_v1(table)


def test_lookup_table_id_from_v1_swaps_the_halves() -> None:
    """Seen on 2 of 2 migrated tables on 2026-11-05."""
    assert lookup_table_id_from_v1('aaaaaaaaaaaabbbbbbbbbbbb') == 'bbbbbbbbbbbbaaaaaaaaaaaa'


def test_lookup_table_id_from_v1_refuses_a_non_object_id() -> None:
    with pytest.raises(ValueError):
        lookup_table_id_from_v1('not-an-id')


def test_lookup_table_id_from_v1_refuses_a_trailing_newline() -> None:
    with pytest.raises(ValueError):
        lookup_table_id_from_v1('aaaaaaaaaaaabbbbbbbbbbbb\n')


def test_a_lone_phased_rule_converts_to_one_rule_without_phase() -> None:
    table: Item = {'name': 'Sample', 'rules': [{'filter': [{'value': 'TX'}], 'phase': 'oil'}]}

    rules = cast('Any', lookup_table_from_v1(table))['rules']

    assert rules == [{'filter': [{'value': 'TX'}]}]


def test_a_phased_rule_and_an_unphased_rule_with_the_same_filter_are_both_kept() -> None:
    table: Item = {
        'name': 'Sample',
        'rules': [{'filter': [{'value': 'TX'}], 'phase': 'oil'}, {'filter': [{'value': 'TX'}]}],
    }

    assert len(cast('Any', lookup_table_from_v1(table))['rules']) == 2


WELL_ROW: Item = {
    'id': '000000000000000000000011',
    'wellName': 'Sample Well 1',
    'api14': '00000000000001',
    'chosenID': '00000000000001',
    'wellNumber': '1H',
    'perfLateralLength': 4240,
    'excluded': False,
}


def test_representative_well_matches_the_v1_values() -> None:
    """Values from one live well, v1 row vs. its forecast output (2026-11-05)."""
    output: Item = {
        'well': '000000000000000000000011',
        'phase': 'oil',
        'forecastType': 'rate',
        'forecastSubType': 'automatic',
        'data_freq': 'monthly',
        'best': {'eur': 569214.15244654},
    }

    row = representative_well_from_v2(WELL_ROW, {'oil': output}, 'best')

    assert row['wellId'] == '000000000000000000000011'
    assert row['oil'] == {
        'rep': True,
        'hasForecast': True,
        'eur': pytest.approx(569.21415244654),
        'eurPll': pytest.approx(134.24862086003301),
        'forecastType': 'rate;automatic',
        'dataFrequency': 'monthly',
    }


def test_representative_well_ratio_output_appends_the_base_phase() -> None:
    output: Item = {
        'phase': 'water',
        'forecastType': 'ratio',
        'forecastSubType': 'manual',
        'data_freq': 'monthly',
        'ratio': {'basePhase': 'gas', 'eur': 177415.73},
    }

    phase_row = representative_well_from_v2(WELL_ROW, {'water': output}, 'best')['water']

    assert cast('Any', phase_row)['forecastType'] == 'ratio;manual;gas'
    assert cast('Any', phase_row)['eur'] == pytest.approx(177.41573)


def test_representative_well_phase_without_output_reads_not_forecasted() -> None:
    """v1 for an unfitted phase: eur 0, eurPll 0, not_forecasted, rep false (live 2026-11-05)."""
    row = representative_well_from_v2(WELL_ROW, {}, 'best')

    assert row['gas'] == {'eur': 0, 'eurPll': 0, 'forecastType': 'not_forecasted', 'hasForecast': False, 'rep': False}


def test_representative_well_excluded_is_not_rep() -> None:
    output: Item = {'forecastType': 'rate', 'forecastSubType': 'automatic', 'best': {'eur': 1000.0}}

    row = representative_well_from_v2({**WELL_ROW, 'excluded': True}, {'oil': output}, 'P50')

    assert cast('Any', row)['oil']['rep'] is False
    assert 'eur' not in cast('Any', row)['oil']
