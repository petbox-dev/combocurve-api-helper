from typing import Annotated, Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field

from . import formats
from .base import Context, common_columns, model_identity
from .csv_columns import COLUMNS
from .formats import csv_to_num, num_to_csv_float

# API group key -> CSV 'Key' column value.
_KEY_TO_CSV = {
    'yields': 'yields',
    'shrinkage': 'shrinkage',
    'lossFlare': 'loss & flare',
}
_KEY_FROM_CSV = {v: k for k, v in _KEY_TO_CSV.items()}

# API category key (within yields/shrinkage/lossFlare) -> CSV 'Category' column value.
_CATEGORY_TO_CSV = {
    'oil': 'oil',
    'gas': 'gas',
    'water': 'water',
    'ngl': 'ngl',
    'dripCondensate': 'drip cond',
    'oilLoss': 'oil loss',
    'gasLoss': 'gas loss',
    'gasFlare': 'gas flare',
}
_CATEGORY_FROM_CSV = {v: k for k, v in _CATEGORY_TO_CSV.items()}

# (StreamPropertyGroup python attribute name, API category key), in the same canonical
# order as _CATEGORY_TO_CSV -- this is the order categories are emitted in real CC CSVs.
_GROUP_CATEGORY_FIELDS: List[Tuple[str, str]] = [
    ('oil', 'oil'),
    ('gas', 'gas'),
    ('water', 'water'),
    ('ngl', 'ngl'),
    ('drip_condensate', 'dripCondensate'),
    ('oil_loss', 'oilLoss'),
    ('gas_loss', 'gasLoss'),
    ('gas_flare', 'gasFlare'),
]
# API category key -> StreamPropertyGroup python attribute name (inverse direction).
_CATEGORY_TO_ATTR: Dict[str, str] = {api_key: attr for attr, api_key in _GROUP_CATEGORY_FIELDS}


class StreamPropertyRow(BaseModel):
    """One `rows[]` element within a yields/shrinkage/lossFlare category node.

    A row carries exactly one of `entire_well_life` (flat criteria) or `dates` (dated
    criteria), and exactly one of `yield_` (yields group) or `pct_remaining` (shrinkage/
    lossFlare groups). `unshrunk_gas` presence (not truthiness) marks the row as
    'unshrunk' in CC's CSV -- real API rows carry `unshrunkGas = ''` (empty string,
    falsy) on the majority of ngl rows, so an emptystring value must still count as
    present.
    """

    model_config = ConfigDict(populate_by_name=True)

    entire_well_life: Annotated[Optional[str], Field(alias='entireWellLife')] = None
    dates: Optional[str] = None
    yield_: Annotated[Optional[Union[int, float]], Field(alias='yield')] = None
    pct_remaining: Annotated[Optional[Union[int, float]], Field(alias='pctRemaining')] = None
    unshrunk_gas: Annotated[Optional[str], Field(alias='unshrunkGas')] = None


class StreamPropertyCategory(BaseModel):
    """The `{'rows': [...]}` node for a single category within a group."""

    model_config = ConfigDict(populate_by_name=True)

    rows: List[StreamPropertyRow] = Field(default_factory=list)


class StreamPropertyGroup(BaseModel):
    """One of the top-level `yields`/`shrinkage`/`lossFlare` groups.

    `rate_type`/`rows_calculation_method` are carried by the real API but CC's CSV
    export renders 'Rate Type'/'Rate Rows Calculation Method' BLANK regardless -- a
    documented CSV-format limitation, not a bug. `to_csv_rows` therefore never reads
    these fields, and `from_csv_rows` never sets them (they come back as `None` and are
    excluded on dump).
    """

    model_config = ConfigDict(extra='forbid', populate_by_name=True)

    rate_type: Annotated[Optional[str], Field(alias='rateType')] = None
    rows_calculation_method: Annotated[Optional[str], Field(alias='rowsCalculationMethod')] = None
    oil: Optional[StreamPropertyCategory] = None
    gas: Optional[StreamPropertyCategory] = None
    water: Optional[StreamPropertyCategory] = None
    ngl: Optional[StreamPropertyCategory] = None
    drip_condensate: Annotated[Optional[StreamPropertyCategory], Field(alias='dripCondensate')] = None
    oil_loss: Annotated[Optional[StreamPropertyCategory], Field(alias='oilLoss')] = None
    gas_loss: Annotated[Optional[StreamPropertyCategory], Field(alias='gasLoss')] = None
    gas_flare: Annotated[Optional[StreamPropertyCategory], Field(alias='gasFlare')] = None


def _value_unit(group_key: str, r: StreamPropertyRow) -> Tuple[Any, str]:
    if group_key == 'yields':
        if r.yield_ is None:
            raise NotImplementedError(f'Unknown yields row: {r!r}')
        return r.yield_, 'bbl/mmcf'
    if r.pct_remaining is None:
        raise NotImplementedError(f'Unknown {group_key} row: {r!r}')
    return r.pct_remaining, '% remaining'


def _criteria(r: StreamPropertyRow) -> Tuple[str, str]:
    return formats.flat_or_dates_criteria(r.entire_well_life, r.dates, what='StreamProperties row')


def _gas_shrinkage_condition(r: StreamPropertyRow) -> str:
    # Presence of the key, not truthiness of its value: real API rows carry
    # unshrunkGas = '' for ngl and unshrunkGas = 'Unshrunk Gas' for drip cond,
    # both meaning "unshrunk".
    return 'unshrunk' if r.unshrunk_gas is not None else ''


class StreamPropertiesMapper:
    econ_model_type = 'StreamProperties'
    columns = COLUMNS['StreamProperties']

    def to_csv_rows(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        custom_streams = model.get('companyCustomStreams')
        if custom_streams:
            raise NotImplementedError(f'Non-empty companyCustomStreams not supported: {custom_streams}')

        common = common_columns(model, context)
        rows: List[Dict[str, str]] = []

        for group_key in ('yields', 'shrinkage', 'lossFlare'):
            raw_group = model.get(group_key)
            if not raw_group:
                continue
            group = StreamPropertyGroup.model_validate(raw_group)
            for attr, api_key in _GROUP_CATEGORY_FIELDS:
                node = getattr(group, attr)
                if node is None:
                    continue
                for r in node.rows:
                    value, unit = _value_unit(group_key, r)
                    criteria, period = _criteria(r)
                    row = dict(common)
                    row.update(
                        {
                            'Key': _KEY_TO_CSV[group_key],
                            'Category': _CATEGORY_TO_CSV[api_key],
                            'Criteria': criteria,
                            'Value': num_to_csv_float(value),
                            'Period': period,
                            'Unit': unit,
                            'Gas Shrinkage Condition': _gas_shrinkage_condition(r),
                            # Verified against real CC exports: 'Rate Type' / 'Rate Rows
                            # Calculation Method' are always blank in the Stream
                            # Properties CSV, even though the API groups carry
                            # rateType/rowsCalculationMethod. Not round-trippable.
                            'Rate Type': '',
                            'Rate Rows Calculation Method': '',
                        }
                    )
                    rows.append({c: row.get(c, '') for c in self.columns})

        # `btuContent` is intentionally NOT emitted here: CC's real Stream Properties
        # CSV export has no 'btu'-Key rows at all and a blank 'BTU (MBTU/MCF)' column.
        # Like Capex $/ft, btuContent has no CSV representation and does not round-trip.

        return rows

    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        groups: Dict[str, Dict[str, List[StreamPropertyRow]]] = {'yields': {}, 'shrinkage': {}, 'lossFlare': {}}
        name, unique = model_identity(rows)

        for row in rows:
            key = row['Key']
            if key not in _KEY_FROM_CSV:
                raise NotImplementedError(f'Unknown Key: {key}')
            group_key = _KEY_FROM_CSV[key]

            if row['Category'] not in _CATEGORY_FROM_CSV:
                raise NotImplementedError(f'Unknown Category: {row["Category"]}')
            category = _CATEGORY_FROM_CSV[row['Category']]

            row_kwargs: Dict[str, Any] = formats.flat_or_dates_row_kwargs(
                row['Criteria'], row['Period'], formats.ENTIRE_WELL_LIFE_MARKER
            )

            if row.get('Gas Shrinkage Condition') == 'unshrunk':
                # Known, documented CSV-format limitation: the CSV only carries a binary
                # unshrunk/shrunk marker, so the exact original unshrunkGas literal
                # ('' for ngl vs. 'Unshrunk Gas' for drip cond) is not round-trip
                # recoverable. Canonicalize to 'Unshrunk Gas' -- both values mean "unshrunk".
                row_kwargs['unshrunk_gas'] = 'Unshrunk Gas'

            if group_key == 'yields':
                row_kwargs['yield_'] = csv_to_num(row['Value'])
            else:
                row_kwargs['pct_remaining'] = csv_to_num(row['Value'])

            groups[group_key].setdefault(category, []).append(StreamPropertyRow(**row_kwargs))

        # `rateType`/`rowsCalculationMethod` cannot be reconstructed: CC's CSV blanks
        # 'Rate Type'/'Rate Rows Calculation Method' unconditionally (see
        # StreamPropertyGroup docstring), so those fields are simply never set below and
        # are excluded on dump. `btuContent` cannot be reconstructed at all -- there are
        # no 'btu'-Key rows in the CSV to read it back from -- so it is omitted entirely
        # from the result.
        result: Dict[str, Any] = {'name': name, 'unique': unique}
        for group_key in ('yields', 'shrinkage', 'lossFlare'):
            group_kwargs: Dict[str, Any] = {
                _CATEGORY_TO_ATTR[category]: StreamPropertyCategory(rows=category_rows)
                for category, category_rows in groups[group_key].items()
            }
            result[group_key] = StreamPropertyGroup(**group_kwargs).model_dump(by_alias=True, exclude_none=True)
        return result
