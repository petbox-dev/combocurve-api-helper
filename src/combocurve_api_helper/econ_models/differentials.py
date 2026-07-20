from typing import Annotated, Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field

from . import formats
from .base import Context, common_columns, model_identity
from .csv_columns import COLUMNS
from .formats import PHASE_TO_CSV_CAMEL as _PHASE_TO_CSV
from .formats import csv_to_num, escalation_from_csv, escalation_to_csv, num_to_csv

_TIER_TO_CSV = {
    'firstDifferential': 'differentials_1',
    'secondDifferential': 'differentials_2',
    'thirdDifferential': 'differentials_3',
}
_TIER_FROM_CSV = {v: k for k, v in _TIER_TO_CSV.items()}
_PHASE_FROM_CSV = {v: k for k, v in _PHASE_TO_CSV.items()}

# (DifferentialRow python attribute name, CSV 'Unit' column value), in the same
# priority order as the original dict-key scan -- only one of these four is ever
# populated on a real row, so scan order is not actually load-bearing.
_VALUE_UNIT: List[Tuple[str, str]] = [
    ('dollar_per_bbl', '$/bbl'),
    ('dollar_per_mcf', '$/mcf'),
    ('dollar_per_mmbtu', '$/mmbtu'),
    ('pct_of_base_price', '% base price rem'),
]
_UNIT_TO_ATTR = {u: attr for attr, u in _VALUE_UNIT}


class DifferentialRow(BaseModel):
    """One `rows[]` element within a differentials tier/phase node (verified against
    real CC CSV exports).

    Carries exactly one of `entire_well_life` (flat criteria) or `dates` (dated
    criteria), and exactly one of the four value/unit fields
    (`dollar_per_bbl`/`dollar_per_mcf`/`dollar_per_mmbtu`/`pct_of_base_price`).
    """

    model_config = ConfigDict(populate_by_name=True)

    entire_well_life: Annotated[Optional[str], Field(alias='entireWellLife')] = None
    dates: Optional[str] = None
    dollar_per_bbl: Annotated[Optional[Union[int, float]], Field(alias='dollarPerBbl')] = None
    dollar_per_mcf: Annotated[Optional[Union[int, float]], Field(alias='dollarPerMcf')] = None
    dollar_per_mmbtu: Annotated[Optional[Union[int, float]], Field(alias='dollarPerMmbtu')] = None
    pct_of_base_price: Annotated[Optional[Union[int, float]], Field(alias='pctOfBasePrice')] = None


class DifferentialPhaseNode(BaseModel):
    """The `{'escalationModel': ..., 'rows': [...]}` node for a single phase within a
    differential tier.

    `escalation_model` is deliberately NOT round-tripped via a blanket
    `model_dump(exclude_none=True)` on the inverse pass: CC's real API distinguishes an
    explicit `null` escalationModel from the literal string `'none'`, and
    `from_csv_rows` must preserve that distinction (commit 3105852) -- a Python `None`
    must come back as `None`, not be omitted. So `DifferentialsMapper.from_csv_rows`
    builds the phase-node dict by hand, keeping `escalationModel` present (possibly
    `None`) while each row is dumped with `exclude_none=True` to drop its unused
    criteria/value fields.
    """

    model_config = ConfigDict(populate_by_name=True)

    escalation_model: Annotated[Optional[str], Field(alias='escalationModel')] = None
    rows: List[DifferentialRow] = Field(default_factory=list)


def _value_unit(r: DifferentialRow) -> Tuple[Any, str]:
    for attr, unit in _VALUE_UNIT:
        value = getattr(r, attr)
        if value is not None:
            return value, unit
    raise NotImplementedError(f'Unknown differential value: {r!r}')


def _criteria(r: DifferentialRow) -> Tuple[str, str]:
    return formats.flat_or_dates_criteria(r.entire_well_life, r.dates, what='differential')


class DifferentialsMapper:
    econ_model_type = 'Differentials'
    columns = COLUMNS['Differentials']

    def to_csv_rows(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        common = common_columns(model, context)
        rows: List[Dict[str, str]] = []
        for tier, phases in model.get('differentials', {}).items():
            if tier not in _TIER_TO_CSV:
                raise NotImplementedError(f'Unknown differential tier: {tier}')
            if not isinstance(phases, dict):
                continue
            for phase, node in phases.items():
                if not isinstance(node, dict):
                    continue
                phase_node = DifferentialPhaseNode.model_validate(node)
                for r in phase_node.rows:
                    value, unit = _value_unit(r)
                    criteria, period = _criteria(r)
                    row = dict(common)
                    row.update(
                        {
                            'Key': _TIER_TO_CSV[tier],
                            'Phase': _PHASE_TO_CSV[phase],
                            'Criteria': criteria,
                            'Value': num_to_csv(value),
                            'Period': period,
                            'Unit': unit,
                            'Escalation': escalation_to_csv(phase_node.escalation_model, title=False),
                        }
                    )
                    rows.append({c: row.get(c, '') for c in self.columns})
        return rows

    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        diffs: Dict[str, Dict[str, DifferentialPhaseNode]] = {
            'firstDifferential': {},
            'secondDifferential': {},
            'thirdDifferential': {},
        }
        name, unique = model_identity(rows)
        for row in rows:
            tier = _TIER_FROM_CSV[row['Key']]
            phase = _PHASE_FROM_CSV[row['Phase']]

            if phase not in diffs[tier]:
                # Only the FIRST row seen for a given tier/phase determines the node's
                # escalationModel -- matches the original `setdefault` behavior.
                escalation_model = escalation_from_csv(row.get('Escalation') or '', title=False)
                diffs[tier][phase] = DifferentialPhaseNode(escalation_model=escalation_model)
            node = diffs[tier][phase]

            # NOTE (fix): the shared helper raises on an unknown Criteria instead of
            # silently falling into the 'dates' branch -- the pre-refactor code here had
            # no `else: raise` and would misparse any Criteria value other than 'flat' as
            # a dated row.
            row_kwargs: Dict[str, Any] = formats.flat_or_dates_row_kwargs(
                row['Criteria'], row['Period'], formats.ENTIRE_WELL_LIFE_MARKER
            )
            row_kwargs[_UNIT_TO_ATTR[row['Unit']]] = csv_to_num(row['Value'])
            node.rows.append(DifferentialRow(**row_kwargs))

        return {
            'name': name,
            'unique': unique,
            'differentials': {
                tier: {
                    phase: {
                        'escalationModel': node.escalation_model,
                        'rows': [r.model_dump(by_alias=True, exclude_none=True) for r in node.rows],
                    }
                    for phase, node in phases.items()
                }
                for tier, phases in diffs.items()
            },
        }
