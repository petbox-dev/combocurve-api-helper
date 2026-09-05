"""Convert a ComboCurve forecast-parameters EXPORT into 'Forecast Parameters' CSV rows.

The async export (`post_export_forecast_parameters` ->
`get_export_forecast_parameters_by_job_id` -> download `result.fileUrls`) yields a parquet
whose rows are keyed in snake_case. `forecast_parameters_to_row_dicts` turns those rows into
the Title-Case, unit-bearing CSV a ComboCurve 'Forecast Parameters' UI export produces --
the spelling downstream ARIES tooling reads.

This is a ONE-WAY converter (export -> CSV); it reuses `RowWriter` for the file-level write
plumbing but is NOT an `EconModelMapper` (no round-trip inverse, a collection+join input
rather than a single model, no Model-Name grouping, and ISO dates rather than the econ
surface's `MM/DD/YYYY`). The value spellings below were verified against a real UI export:
`Phase` (Oil/Gas/Water), `Type` (Rate/Ratio), `Base Phase`, `Segment Type`
(arps/arps_modified/arps_inc/shut_in/flat/...) and `Series` (best) are the SAME strings on
both surfaces, so they pass through unchanged -- no remap was needed.

The reader matches the unit-bearing columns by SUBSTRING ('q Start', 'Di Eff-Sec'), so the
`(BBL/D, MCF/D, BBL/MCF, MCF/BBL)` label is a fixed, non-load-bearing header (it is NOT
per-phase), copied verbatim from a real export.

The 21 snake_case input keys this converter reads were verified against a real
forecast-parameters parquet export (2026-09-04): the parquet carries ~61 columns and all 21
read keys are present with the exact spellings used below; the other ~40 (project/forecast
metadata, eur, cum, ...) are ignored. `test_extra_export_columns_are_ignored` pins that a
real-shaped row is handled and the extras are dropped.
"""

import os
from collections.abc import Callable
from typing import Any, Union

from ._csv_writer import RowWriter
from .econ_models.formats import NULL_TEXTS, num_to_csv, num_to_csv_float, to_csv_iso_date

# The multi-unit label a real CC export writes on every q column, regardless of phase.
_Q_UNITS = 'BBL/D, MCF/D, BBL/MCF, MCF/BBL'

# The three q columns carry that label in their header. Named once so the header list and
# the per-row builder share the exact string -- and so the f-string is not rebuilt on every
# row (a real cost on a large multi-thousand-row export).
_Q_START_COL = f'q Start ({_Q_UNITS})'
_Q_END_COL = f'q End ({_Q_UNITS})'
_Q_SW_COL = f'q Sw ({_Q_UNITS})'

# The 23 columns, in the exact order and spelling of a real CC 'Forecast Parameters' export.
# (A full export carries 83 columns; this is the segment-parameter subset ARIES consumes.)
# A tuple, not a list: it is re-exported at the package root and backs the singleton
# converter's `.columns`, so an immutable header cannot be corrupted process-wide by a
# stray `.append`/`.sort` on the shared object (mirrors base.py's MappingProxyType orders).
FORECAST_PARAMETERS_COLUMNS: tuple[str, ...] = (
    'Well Name',
    'INPT ID',
    'Chosen ID',
    'API 10',
    'Phase',
    'Segment',
    'Series',
    'Type',
    'Base Phase',
    'Segment Type',
    'Start Date',
    'End Date',
    'Start Day',
    'End Day',
    _Q_START_COL,
    _Q_END_COL,
    'Di Eff-Sec (%)',
    'Di Nominal',
    'b',
    'Realized D Sw-Eff-Sec (%)',
    'Sw-Date',
    _Q_SW_COL,
    'Warning',
)


def _text(value: Any) -> str:
    """Pass a categorical/text value through unchanged, emitting '' for a null."""
    if value is None:
        return ''
    text = str(value)
    return '' if text in NULL_TEXTS else text


def _format_value(value: Any, formatter: Callable[[Any], str]) -> str:
    """Apply `formatter` to a number, emitting '' for any parquet null shape.

    The shared null contract for the numeric columns: `None`, a float NaN, or a null-text
    string (an unnormalized parquet read) all render blank; anything else is formatted.
    """
    if value is None:
        return ''
    if isinstance(value, float) and value != value:  # NaN
        return ''
    if isinstance(value, str) and value.strip() in NULL_TEXTS:
        return ''
    return formatter(value)


def _num(value: Any) -> str:
    """Format a number int-if-integral (`0.0` -> '0'), '' for a null.

    Matches the CC export's q / Di / b / Realized-D columns, where a whole value drops its
    trailing '.0' (e.g. a shut-in `q Start` of 0 renders '0') and a decline-less segment
    leaves the field blank.
    """
    return _format_value(value, num_to_csv)


def _day(value: Any) -> str:
    """Format Start/End Day, which KEEP a decimal point in the CC export (e.g. '-14.0').

    Distinct from `_num`: days render '52.0', not '52' -- and can be negative (a segment
    that starts before first production).
    """
    return _format_value(value, num_to_csv_float)


class ForecastParametersConverter(RowWriter):
    """Export-row -> CSV-row converter for CC forecast parameters. See the module docstring.

    Kept as a small `RowWriter` subclass (rather than free functions alone) so it shares the
    `rows_to_csv` / `write_rows_csv` file-level plumbing with the econ mappers. The public
    API is the module-level functions below; this class is the implementation.
    """

    columns = FORECAST_PARAMETERS_COLUMNS

    def to_row_dicts(self, export_rows: list[dict[str, Any]], wells: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Convert forecast-export rows to CSV rows, joining well identity from `wells`.

        `INPT ID` / `Chosen ID` / `API 10` are NOT in the export -- only `well_id` is -- so
        they are looked up from `wells` (project company-well headers, keyed by `id`). A
        forecast row whose `well_id` is absent from `wells` raises `ValueError` rather than
        being dropped: silently discarding forecast segments would under-report downstream.
        """
        wells_by_id: dict[str, dict[str, Any]] = {str(well.get('id', '')): well for well in wells}

        rows: list[dict[str, str]] = []
        for export_row in export_rows:
            well_id = str(export_row.get('well_id', ''))
            well = wells_by_id.get(well_id)
            if well is None:
                raise ValueError(f'forecast export references well_id {well_id!r}, which is not present in `wells`')
            rows.append(self._row(export_row, well))
        return rows

    @staticmethod
    def _row(export_row: dict[str, Any], well: dict[str, Any]) -> dict[str, str]:
        """Build one CSV row from an export row and its matched well header."""
        return {
            # An empty `wellName` on the header falls back to the export's `well_name`;
            # blank is treated as absent (the `or`), unlike the plain `.get()` fields below.
            'Well Name': _text(well.get('wellName') or export_row.get('well_name')),
            'INPT ID': _text(well.get('inptID')),
            'Chosen ID': _text(well.get('chosenID')),
            'API 10': _text(well.get('api10')),
            'Phase': _text(export_row.get('phase')),
            'Segment': _num(export_row.get('segment')),  # 1.0 -> '1'
            'Series': _text(export_row.get('series')),
            'Type': _text(export_row.get('type')),
            'Base Phase': _text(export_row.get('base_phase')),
            'Segment Type': _text(export_row.get('segment_type')),
            'Start Date': to_csv_iso_date(export_row.get('start_date')),
            'End Date': to_csv_iso_date(export_row.get('end_date')),
            'Start Day': _day(export_row.get('start_day')),
            'End Day': _day(export_row.get('end_day')),
            _Q_START_COL: _num(export_row.get('q_start')),
            _Q_END_COL: _num(export_row.get('q_end')),
            'Di Eff-Sec (%)': _num(export_row.get('Di_Eff_Sec')),
            'Di Nominal': _num(export_row.get('Di_nominal')),
            'b': _num(export_row.get('b')),
            'Realized D Sw-Eff-Sec (%)': _num(export_row.get('realized_D_sw_Eff_Sec')),
            'Sw-Date': to_csv_iso_date(export_row.get('sw_date')),
            _Q_SW_COL: _num(export_row.get('q_sw')),
            'Warning': _text(export_row.get('warning')),
        }


_CONVERTER = ForecastParametersConverter()


def forecast_parameters_to_row_dicts(
    export_rows: list[dict[str, Any]], wells: list[dict[str, Any]]
) -> list[dict[str, str]]:
    """Convert forecast-parameters export rows to 'Forecast Parameters' CSV row dicts.

    `export_rows` are the (already-parsed) rows of the parquet export; `wells` are the
    project company-well headers (each carrying `id`, `inptID`, `chosenID`, `api10`,
    `wellName`) used to join the well identity the export omits. Raises `ValueError` for a
    forecast row whose `well_id` is not in `wells`.
    """
    return _CONVERTER.to_row_dicts(export_rows, wells)


def forecast_parameters_to_csv(export_rows: list[dict[str, Any]], wells: list[dict[str, Any]]) -> str:
    """Convert forecast-parameters export rows to a CSV string (header + one row per segment)."""
    return _CONVERTER.rows_to_csv(_CONVERTER.to_row_dicts(export_rows, wells))


def write_forecast_parameters_csv(
    path: Union[str, os.PathLike[str]],
    export_rows: list[dict[str, Any]],
    wells: list[dict[str, Any]],
) -> None:
    """Write forecast-parameters export rows to a CSV file (UTF-8, `newline=''`)."""
    _CONVERTER.write_rows_csv(path, _CONVERTER.to_row_dicts(export_rows, wells))


__all__ = [
    'FORECAST_PARAMETERS_COLUMNS',
    'ForecastParametersConverter',
    'forecast_parameters_to_csv',
    'forecast_parameters_to_row_dicts',
    'write_forecast_parameters_csv',
]
