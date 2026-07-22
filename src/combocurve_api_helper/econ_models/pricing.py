from typing import Annotated, Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field

from . import formats
from .base import Context, EconModelMapper, common_columns, model_identity
from .csv_columns import COLUMNS
from .formats import PHASE_TO_CSV_CAMEL as _PHASE_TO_CSV
from .formats import csv_to_num, escalation_from_csv, escalation_to_csv, num_to_csv

_PHASE_FROM_CSV = {v: k for k, v in _PHASE_TO_CSV.items()}
_PHASE_ORDER = ('oil', 'gas', 'ngl', 'dripCondensate')

# (PriceRow python attribute name, CSV 'Unit' column value) per phase: oil rows are ALWAYS
# `price` (never `dollarPerBbl`); gas rows are `dollarPerMmbtu` or `dollarPerMcf` (never
# anything else); ngl rows are ALWAYS `pctOfOilPrice` (never `dollarPerBbl`);
# dripCondensate rows are `pctOfOilPrice` OR `dollarPerBbl` (NEVER bare `price` -- despite
# oil/dripCondensate both rendering CSV Unit '$/bbl', they use DIFFERENT API keys). The
# dispatch is phase-keyed (not a single flat scan) because oil's `price` and
# ngl/dripCondensate's `dollarPerBbl` both map to the same CSV Unit '$/bbl' string and
# would collide in a single unit->attr inverse table.
_PHASE_VALUE_UNIT: Dict[str, List[Tuple[str, str]]] = {
    'oil': [('price', '$/bbl')],
    'gas': [('dollar_per_mmbtu', '$/mmbtu'), ('dollar_per_mcf', '$/mcf')],
    'ngl': [('pct_of_oil_price', '% of oil price'), ('dollar_per_bbl', '$/bbl')],
    'dripCondensate': [('pct_of_oil_price', '% of oil price'), ('dollar_per_bbl', '$/bbl')],
}
_PHASE_UNIT_TO_ATTR = {phase: {u: a for a, u in lst} for phase, lst in _PHASE_VALUE_UNIT.items()}

_BREAKEVEN_PHASE_CSV = 'breakeven'
_BREAKEVEN_UNIT_CSV = 'npv discount %'
_BREAKEVEN_DIRECT_CSV = 'direct'
_BREAKEVEN_RATIO_CSV = 'based on price ratio'

# Gas-only compositional-pricing 'Category' values: extra flat $/mmbtu=0 rows with Category
# in {remaining, n2, co2, c1} can appear alongside 'full_stream' (the plain single-stream
# label) on gas/ngl rows. CRITICAL: the `GET .../pricing` API (both the list endpoint and
# the single-model-by-id endpoint) returns `priceModel.gas` as EXACTLY
# `{cap, escalationModel, rows}` with PLAIN scalar `dollarPerMmbtu`/`dollarPerMcf` row
# values -- IDENTICAL in shape whether CC's CSV renders that model's Category as '',
# 'full_stream', or emits the additional component rows. There is no key anywhere in the
# API response that distinguishes these cases. This is a real API limitation, not an
# oversight: 'full_stream' vs '' is not a property of the Pricing econ model document at
# all (it appears to depend on scenario-level Compositional Economics context that this
# project-scoped econ-model GET endpoint has no way to surface), and the
# c1/co2/n2/remaining component rows have no representable slot in `priceModel.gas`
# whatsoever. `to_row_dicts` therefore ALWAYS emits Category='' (the only constructible
# value) -- 'full_stream' is a non-round-trippable display label CSV-side. `from_row_dicts`
# accepts 'full_stream' as equivalent to '' (same numeric row, label simply not preserved)
# but raises NotImplementedError for the compositional component categories, which have no
# known API home.
_GAS_COMPONENT_CATEGORIES = {'remaining', 'n2', 'co2', 'c1'}


class PriceRow(BaseModel):
    """One `rows[]` element within a `priceModel` phase node.

    Carries exactly one of `entire_well_life` (flat criteria) or `dates` (dated
    criteria), and exactly one of the four value/unit fields (`price`/
    `dollar_per_mmbtu`/`dollar_per_mcf`/`pct_of_oil_price`).
    """

    model_config = ConfigDict(populate_by_name=True)

    entire_well_life: Annotated[Optional[str], Field(alias='entireWellLife')] = None
    dates: Optional[str] = None
    price: Optional[Union[int, float]] = None
    dollar_per_bbl: Annotated[Optional[Union[int, float]], Field(alias='dollarPerBbl')] = None
    dollar_per_mmbtu: Annotated[Optional[Union[int, float]], Field(alias='dollarPerMmbtu')] = None
    dollar_per_mcf: Annotated[Optional[Union[int, float]], Field(alias='dollarPerMcf')] = None
    pct_of_oil_price: Annotated[Optional[Union[int, float]], Field(alias='pctOfOilPrice')] = None


class PricePhaseNode(BaseModel):
    """The `{'cap': ..., 'escalationModel': ..., 'rows': [...]}` node for a single phase
    (oil/gas/ngl/dripCondensate) within `priceModel`. Every phase node carries all three
    keys, `cap` usually `null`; its forward `num_to_csv` rendering when populated is
    inferred from the sibling Differentials/Expenses 'Cap'/'Value' conventions, not
    directly confirmed."""

    model_config = ConfigDict(populate_by_name=True)

    cap: Optional[Union[int, float]] = None
    escalation_model: Annotated[Optional[str], Field(alias='escalationModel')] = None
    rows: List[PriceRow] = Field(default_factory=list)


class Breakeven(BaseModel):
    """The top-level `breakeven` object:
    `{"basedOnPriceRatio": false, "npvDiscount": 0, "priceRatio": null}`
    (direct) or `{"basedOnPriceRatio": true, "npvDiscount": 15, "priceRatio": 20}`
    (based on price ratio). Maps to a single CSV row: Phase='breakeven', Criteria=
    'direct'/'based on price ratio', Value=npvDiscount, Unit='npv discount %',
    Price Ratio=priceRatio (blank for the direct case)."""

    model_config = ConfigDict(populate_by_name=True)

    based_on_price_ratio: Annotated[bool, Field(alias='basedOnPriceRatio')] = False
    npv_discount: Annotated[Union[int, float], Field(alias='npvDiscount')] = 0
    price_ratio: Annotated[Optional[Union[int, float]], Field(alias='priceRatio')] = None


def _value_unit(phase: str, r: PriceRow) -> Tuple[Any, str]:
    for attr, unit in _PHASE_VALUE_UNIT[phase]:
        value = getattr(r, attr)
        if value is not None:
            return value, unit
    raise NotImplementedError(f'Unknown pricing row value for phase {phase!r}: {r!r}')


def _criteria(r: PriceRow) -> Tuple[str, str]:
    return formats.flat_or_dates_criteria(r.entire_well_life, r.dates, what='pricing row')


def _breakeven_from_csv(row: Dict[str, str]) -> Dict[str, Any]:
    criteria = row['Criteria']
    if criteria == _BREAKEVEN_DIRECT_CSV:
        return {
            'basedOnPriceRatio': False,
            'npvDiscount': csv_to_num(row['Value']),
            'priceRatio': None,
        }
    if criteria == _BREAKEVEN_RATIO_CSV:
        return {
            'basedOnPriceRatio': True,
            'npvDiscount': csv_to_num(row['Value']),
            'priceRatio': csv_to_num(row['Price Ratio']),
        }
    raise NotImplementedError(f'Unknown Pricing breakeven Criteria: {criteria!r}')


class PricingMapper(EconModelMapper):
    econ_model_type = 'Pricing'
    columns = COLUMNS['Pricing']

    def to_row_dicts(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        common = common_columns(model, context)
        rows: List[Dict[str, str]] = []
        price_model = model.get('priceModel') or {}

        for phase in _PHASE_ORDER:
            node_raw = price_model.get(phase)
            if not isinstance(node_raw, dict):
                continue
            node = PricePhaseNode.model_validate(node_raw)
            for r in node.rows:
                value, unit = _value_unit(phase, r)
                criteria, period = _criteria(r)
                row = dict(common)
                row.update(
                    {
                        'Phase': _PHASE_TO_CSV[phase],
                        'Category': '',
                        'Criteria': criteria,
                        'Value': num_to_csv(value),
                        'Period': period,
                        'Unit': unit,
                        'Cap': '' if node.cap is None else num_to_csv(node.cap),
                        'Price Ratio': '',
                        'Escalation': escalation_to_csv(node.escalation_model, title=True),
                    }
                )
                rows.append({c: row.get(c, '') for c in self.columns})

        breakeven_raw = model.get('breakeven')
        if breakeven_raw:
            be = Breakeven.model_validate(breakeven_raw)
            row = dict(common)
            row.update(
                {
                    'Phase': _BREAKEVEN_PHASE_CSV,
                    'Category': '',
                    'Criteria': _BREAKEVEN_RATIO_CSV if be.based_on_price_ratio else _BREAKEVEN_DIRECT_CSV,
                    'Value': num_to_csv(be.npv_discount),
                    'Period': '',
                    'Unit': _BREAKEVEN_UNIT_CSV,
                    'Cap': '',
                    'Price Ratio': '' if be.price_ratio is None else num_to_csv(be.price_ratio),
                    'Escalation': '',
                }
            )
            rows.append({c: row.get(c, '') for c in self.columns})

        return rows

    def from_row_dicts(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        price_model: Dict[str, Dict[str, Any]] = {}
        breakeven: Optional[Dict[str, Any]] = None
        name, unique = model_identity(rows)

        for row in rows:
            phase_csv = row['Phase']

            if phase_csv == _BREAKEVEN_PHASE_CSV:
                breakeven = _breakeven_from_csv(row)
                continue

            if phase_csv not in _PHASE_FROM_CSV:
                raise NotImplementedError(f'Unknown Pricing Phase: {phase_csv!r}')
            phase = _PHASE_FROM_CSV[phase_csv]

            category = row.get('Category') or ''
            if category in _GAS_COMPONENT_CATEGORIES:
                # Compositional gas-component row (c1/co2/n2/remaining) -- see
                # `_GAS_COMPONENT_CATEGORIES` docstring: the API has no field to hold this.
                # Fail loud rather than silently dropping it or folding it into the plain
                # gas node.
                raise NotImplementedError(
                    f'Pricing Category {category!r} (compositional gas component pricing) has no '
                    'known API representation -- cannot reconstruct from CSV'
                )
            if category not in ('', 'full_stream'):
                raise NotImplementedError(f'Unknown Pricing Category: {category!r}')

            if phase not in price_model:
                # Only the FIRST row seen for a given phase determines the node's
                # cap/escalationModel -- constant across all rows of a phase (matches
                # DifferentialsMapper's escalationModel-from-first-row convention).
                cap_cell = row.get('Cap') or ''
                price_model[phase] = {
                    'cap': None if not cap_cell else csv_to_num(cap_cell),
                    'escalationModel': escalation_from_csv(row.get('Escalation') or '', title=True),
                    'rows': [],
                }
            node = price_model[phase]

            row_kwargs: Dict[str, Any] = formats.flat_or_dates_row_kwargs(
                row['Criteria'], row['Period'], formats.ENTIRE_WELL_LIFE_MARKER
            )
            unit = row['Unit']
            unit_to_attr = _PHASE_UNIT_TO_ATTR[phase]
            if unit not in unit_to_attr:
                raise NotImplementedError(f'Unknown Pricing Unit {unit!r} for Phase {phase_csv!r}')
            row_kwargs[unit_to_attr[unit]] = csv_to_num(row['Value'])
            node['rows'].append(PriceRow(**row_kwargs).model_dump(by_alias=True, exclude_none=True))

        return {
            'name': name,
            'unique': unique,
            'priceModel': {
                phase: {
                    'cap': node['cap'],
                    'escalationModel': node['escalationModel'],
                    'rows': node['rows'],
                }
                for phase, node in price_model.items()
            },
            'breakeven': breakeven,
        }
