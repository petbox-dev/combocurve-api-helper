"""Tests for the forecast-parameters export -> CSV converter.

All fixtures are SYNTHETIC (this is a public repo): placeholder well names, INPT/Chosen
ids, APIs, and 24-hex ObjectIds -- never real project/well data.
"""

import csv
import datetime
import io
from typing import Any

import pytest

from combocurve_api_helper.forecast_parameters import (
    FORECAST_PARAMETERS_COLUMNS,
    forecast_parameters_to_csv,
    forecast_parameters_to_row_dicts,
    write_forecast_parameters_csv,
)

# --- synthetic fixtures -------------------------------------------------------------

WELL_A = '000000000000000000000001'
WELL_B = '000000000000000000000002'

WELLS: list[dict[str, Any]] = [
    {'id': WELL_A, 'wellName': 'Sample Well 1', 'inptID': 'INPT0001', 'chosenID': 'CHOSEN-1', 'api10': '0102030405'},
    {'id': WELL_B, 'wellName': 'Sample Well 2', 'inptID': 'INPT0002', 'chosenID': 'CHOSEN-2', 'api10': '0607080910'},
]

# An Oil arps segment with every field populated.
OIL_ROW: dict[str, Any] = {
    'well_name': 'Sample Well 1',
    'well_id': WELL_A,
    'phase': 'Oil',
    'series': 'best',
    'type': 'Rate',
    'base_phase': None,
    'segment': 1.0,
    'segment_type': 'arps',
    'start_date': datetime.date(2020, 1, 1),
    'end_date': datetime.date(2020, 6, 30),
    'start_day': -14.0,
    'end_day': 166.0,
    'q_start': 1234.5,
    'q_end': 500.0,
    'Di_Eff_Sec': 76.26,
    'Di_nominal': 80.0,
    'b': 1.1,
    'realized_D_sw_Eff_Sec': 8.0,
    'sw_date': datetime.date(2021, 1, 1),
    'q_sw': 49.0,
    'warning': None,
}

# A Gas shut-in segment: no decline, so the numeric decline fields are null.
GAS_SHUT_IN_ROW: dict[str, Any] = {
    'well_name': 'Sample Well 2',
    'well_id': WELL_B,
    'phase': 'Gas',
    'series': 'best',
    'type': 'Ratio',
    'base_phase': 'Oil',
    'segment': 1.0,
    'segment_type': 'shut_in',
    'start_date': datetime.date(2020, 1, 1),
    'end_date': datetime.date(2020, 2, 1),
    'start_day': 0.0,
    'end_day': 31.0,
    'q_start': 0.0,
    'q_end': 0.0,
    'Di_Eff_Sec': None,
    'Di_nominal': None,
    'b': None,
    'realized_D_sw_Eff_Sec': None,
    'sw_date': None,
    'q_sw': None,
    'warning': None,
}

_Q_START = 'q Start (BBL/D, MCF/D, BBL/MCF, MCF/BBL)'
_Q_SW = 'q Sw (BBL/D, MCF/D, BBL/MCF, MCF/BBL)'


def test_columns_are_the_exact_23_headers_in_order() -> None:
    rows = forecast_parameters_to_row_dicts([OIL_ROW], WELLS)
    assert list(rows[0].keys()) == FORECAST_PARAMETERS_COLUMNS
    assert len(FORECAST_PARAMETERS_COLUMNS) == 23
    # the unit label is the fixed multi-unit string, not per-phase
    assert _Q_START in FORECAST_PARAMETERS_COLUMNS
    assert 'Status' not in FORECAST_PARAMETERS_COLUMNS


def test_well_identity_is_joined_from_wells_not_the_export() -> None:
    (row,) = forecast_parameters_to_row_dicts([OIL_ROW], WELLS)
    assert row['Well Name'] == 'Sample Well 1'
    assert row['INPT ID'] == 'INPT0001'
    assert row['Chosen ID'] == 'CHOSEN-1'
    assert row['API 10'] == '0102030405'


def test_value_formatting_matches_the_cc_export() -> None:
    (row,) = forecast_parameters_to_row_dicts([OIL_ROW], WELLS)
    assert row['Phase'] == 'Oil'
    assert row['Type'] == 'Rate'
    assert row['Segment Type'] == 'arps'
    assert row['Segment'] == '1'  # 1.0 -> "1", int-if-integral
    assert row['Start Date'] == '2020-01-01'  # ISO, not MM/DD/YYYY
    assert row['End Date'] == '2020-06-30'
    assert row['Sw-Date'] == '2021-01-01'
    assert row['Start Day'] == '-14.0'  # negative, keeps the decimal point
    assert row['End Day'] == '166.0'
    assert row[_Q_START] == '1234.5'
    assert row['q End (BBL/D, MCF/D, BBL/MCF, MCF/BBL)'] == '500'  # 500.0 -> "500"
    assert row['Di Eff-Sec (%)'] == '76.26'  # percent passed through
    assert row['Di Nominal'] == '80'
    assert row['b'] == '1.1'
    assert row['Realized D Sw-Eff-Sec (%)'] == '8'
    assert row[_Q_SW] == '49'


def test_nulls_render_blank_and_zero_q_renders_zero() -> None:
    (row,) = forecast_parameters_to_row_dicts([GAS_SHUT_IN_ROW], WELLS)
    assert row['Phase'] == 'Gas'
    assert row['Base Phase'] == 'Oil'
    assert row['Segment Type'] == 'shut_in'
    assert row[_Q_START] == '0'  # 0.0 -> "0"
    assert row['Start Day'] == '0.0'  # a day of 0 still keeps the decimal point
    # decline fields are null for a shut-in segment
    assert row['Di Eff-Sec (%)'] == ''
    assert row['Di Nominal'] == ''
    assert row['b'] == ''
    assert row['Realized D Sw-Eff-Sec (%)'] == ''
    assert row['Sw-Date'] == ''
    assert row[_Q_SW] == ''
    assert row['Warning'] == ''


def test_a_forecast_row_with_no_matching_well_raises() -> None:
    orphan = dict(OIL_ROW, well_id='ffffffffffffffffffffffff')
    with pytest.raises(ValueError, match=r'not present in `wells`'):
        forecast_parameters_to_row_dicts([orphan], WELLS)


def test_string_null_spellings_from_an_unnormalized_parquet_read_are_blank() -> None:
    # a caller who read the parquet without normalizing may hand us 'NaT'/'nan' strings
    messy = dict(OIL_ROW, sw_date='NaT', q_sw='nan', warning='None')
    (row,) = forecast_parameters_to_row_dicts([messy], WELLS)
    assert row['Sw-Date'] == ''
    assert row[_Q_SW] == ''
    assert row['Warning'] == ''


def test_to_csv_roundtrips_the_header_and_rows() -> None:
    text = forecast_parameters_to_csv([OIL_ROW, GAS_SHUT_IN_ROW], WELLS)
    parsed = list(csv.reader(io.StringIO(text)))
    assert parsed[0] == FORECAST_PARAMETERS_COLUMNS  # header survives comma-in-header quoting
    assert len(parsed) == 3  # header + 2 rows
    assert parsed[1][FORECAST_PARAMETERS_COLUMNS.index('Well Name')] == 'Sample Well 1'


def test_to_csv_of_no_rows_is_header_only() -> None:
    text = forecast_parameters_to_csv([], WELLS)
    parsed = list(csv.reader(io.StringIO(text)))
    assert parsed == [FORECAST_PARAMETERS_COLUMNS]


def test_write_csv_writes_a_utf8_file(tmp_path: Any) -> None:
    path = tmp_path / 'forecasts.csv'
    write_forecast_parameters_csv(path, [OIL_ROW, GAS_SHUT_IN_ROW], WELLS)
    with open(path, encoding='utf-8', newline='') as handle:
        parsed = list(csv.reader(handle))
    assert parsed[0] == FORECAST_PARAMETERS_COLUMNS
    assert len(parsed) == 3
