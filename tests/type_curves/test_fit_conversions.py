"""Pure fit, normalization and volume conversions between the v1 and v2 type-curve shapes."""

import copy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from combocurve_api_helper.base import Item
from combocurve_api_helper.type_curve_conversions import (
    fits_for_put,
    fits_from_v1,
    fits_to_v1,
    normalization_for_put,
    type_curve_to_v1,
    volumes_to_v1,
)

FIXTURES = Path(__file__).parent / 'fixtures'


def load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding='utf8'))


def linear_segment(slope: float) -> Item:
    return {
        'segmentIndex': 1,
        'segmentType': 'linear',
        'startDate': '1900-01-01',
        'endDate': '1900-12-31',
        'qStart': 500,
        'qEnd': 400,
        'slope': slope,
    }


def test_fits_for_put_turns_a_read_back_linear_sign_into_the_slope_value() -> None:
    """Read gives the sign; write takes the value. Sending -1 back stored qEnd 136 live."""
    fits: Item = {
        'oil': {
            'fitType': 'rate',
            'eurPercentileMatched': False,
            'updatedAt': '2026-11-05',
            'best': {'segments': [linear_segment(-1)]},
        }
    }

    writable = fits_for_put(fits)

    oil = writable['oil']
    assert isinstance(oil, dict)
    assert 'updatedAt' not in oil
    segment = cast('Any', oil)['best']['segments'][0]
    assert segment['slope'] == pytest.approx(-100 / 364)
    assert cast('Any', fits)['oil']['best']['segments'][0]['slope'] == -1  # input unchanged


def test_fits_for_put_leaves_a_write_form_linear_segment_alone() -> None:
    """No qEnd (the v1 write form): nothing to compute from, the given value stays."""
    segment = linear_segment(-0.25)
    del segment['qEnd']
    fits: Item = {'oil': {'fitType': 'rate', 'best': {'segments': [segment]}}}

    assert cast('Any', fits_for_put(fits))['oil']['best']['segments'][0]['slope'] == -0.25


def test_normalization_for_put_drops_coefficients_on_one_to_one() -> None:
    normalization = load('paired_v2_normalization.json')

    writable = normalization_for_put(normalization)

    assert cast('Any', writable)['gas']['eur']['segments'] == [{'xStart': 0, 'fitType': '1_to_1'}]
    assert normalization['gas']['eur']['segments'][0]['aValue'] == 1  # input unchanged


def test_normalization_for_put_drops_x_axis_with_a_custom_basis() -> None:
    normalization: Item = {
        'oil': {
            'xAxis': 'prop/pll',
            'customBasisKey': 'prop/pll/hz',
            'yAxis': 'eur',
            'targets': [],
            'eur': {'segments': []},
        },
    }

    assert 'xAxis' not in cast('Any', normalization_for_put(normalization))['oil']


def test_fits_from_v1_matches_what_ccs_migration_stored() -> None:
    """The same type curve read through v1 and v2 (live 2026-11-05)."""
    expected = {
        phase: {key: value for key, value in fit.items() if key != 'updatedAt'}
        for phase, fit in load('paired_v2_fits.json').items()
    }

    assert fits_from_v1(load('paired_v1_type_curve.json')) == expected


def test_fits_from_v1_converts_a_ratio_fit_and_a_linear_segment() -> None:
    fits = fits_from_v1(load('v1_type_curve_ratio_linear.json'))

    gas = fits['gas']
    assert isinstance(gas, dict)
    assert gas['fitType'] == 'ratio'
    assert gas['eurPercentileMatched'] is False
    assert cast('Any', gas)['ratio']['basePhase'] == 'oil'
    assert set(cast('Any', gas)['ratio']) == {'basePhase', 'best', 'p10', 'p50', 'p90'}
    assert 'best' not in gas
    assert 'regressionType' not in gas
    oil_segment = cast('Any', fits)['oil']['best']['segments'][0]
    assert oil_segment['slope'] == pytest.approx(-100 / 364)


def test_fits_from_v1_refuses_ratio_series_with_different_base_phases() -> None:
    type_curve = load('v1_type_curve_ratio_linear.json')
    type_curve['fits']['gas']['ratio']['p90']['basePhase'] = 'water'

    with pytest.raises(ValueError, match=r'gas.*base phases'):
        fits_from_v1(type_curve)


def test_fits_to_v1_restores_the_v1_fit_shape() -> None:
    v1_gas = load('paired_v1_type_curve.json')['fits']['gas']
    dropped_keys = ('resolution', 'align', 'normalize', 'normalizations')
    expected_gas = {key: value for key, value in v1_gas.items() if key not in dropped_keys}

    fits = fits_to_v1(load('paired_v2_fits.json'))

    assert fits['gas'] == expected_gas
    assert 'oil' not in fits


def test_fits_to_v1_copies_the_ratio_base_phase_into_each_series() -> None:
    fits_v2: Item = {'gas': {'fitType': 'ratio', 'ratio': {'basePhase': 'oil', 'best': {'segments': []}}}}

    assert fits_to_v1(fits_v2)['gas'] == {'type': 'ratio', 'ratio': {'best': {'segments': [], 'basePhase': 'oil'}}}


def test_type_curve_to_v1_embeds_fits() -> None:
    type_curve_v2: Item = {
        'id': '000000000000000000000009',
        'name': 'Sample',
        'project': 'p',
        'forecast': 'f',
        'forecastSeries': 'best',
        'wells': ['w'],
        'excludedWells': [],
        'createdAt': 'c',
        'updatedAt': 'u',
    }

    converted = type_curve_to_v1(type_curve_v2, load('paired_v2_fits.json'))

    assert set(converted) == {'id', 'name', 'forecast', 'wells', 'createdAt', 'updatedAt', 'fits'}
    assert converted['fits'] == fits_to_v1(load('paired_v2_fits.json'))


def test_volumes_to_v1_puts_back_the_nulls_v2_leaves_out() -> None:
    assert volumes_to_v1(load('paired_v2_monthly_volumes.json')) == load('paired_v1_monthly_fits.json')


def test_conversions_do_not_change_their_input() -> None:
    type_curve = load('v1_type_curve_ratio_linear.json')
    before = copy.deepcopy(type_curve)

    fits_from_v1(type_curve)

    assert type_curve == before
