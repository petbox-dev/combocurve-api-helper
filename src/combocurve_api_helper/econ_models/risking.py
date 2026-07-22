from typing import Annotated, Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from . import formats
from .base import Context, common_columns, model_identity
from .csv_columns import COLUMNS
from .formats import csv_to_num, num_to_csv

# API 'risking' phase key (RiskingModel python attribute name) -> CSV 'Phase' column
# value, in forward-emission order.
_PHASE_ORDER: List[Tuple[str, str]] = [
    ('oil', 'oil'),
    ('gas', 'gas'),
    ('ngl', 'ngl'),
    ('drip_condensate', 'drip cond'),
    ('water', 'water'),
]
_PHASE_FROM_CSV = {csv_phase: attr for attr, csv_phase in _PHASE_ORDER}

_KEY_CSV = 'risking'
_WELLS_KEY_CSV = 'wells'


class RiskingMultiplierRow(BaseModel):
    """One `rows[]` element within a Risking phase node. Every real row carries exactly
    these two keys -- `entireWellLife` is always the literal string `'Flat'`. No shut-in,
    offset/dates, or seasonal criteria are supported; `RiskingMapper` raises
    `NotImplementedError` on anything else.

    `multiplier` is typed `Any`, not `Union[int, float]`, so the forward pass carries
    the API's exact value through unchanged (int `97` stays `97`, float `92.816` stays
    `92.816`) -- mirrors `ProductionTaxApiRow.value: List[Any]` in production_taxes.py.
    Note the CSV->API inverse reconstructs the multiplier via `csv_to_num`, which
    renders whole-number floats as int (a `100.0` multiplier comes back as `100`);
    JSON-equivalent and accepted by CC, but not byte-identical for that case.
    """

    model_config = ConfigDict(populate_by_name=True)

    entire_well_life: Annotated[str, Field(alias='entireWellLife')]
    multiplier: Any


class RiskingPhaseNode(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rows: List[RiskingMultiplierRow] = Field(default_factory=list)


class RiskingModel(BaseModel):
    """The `model['risking']` object. Structurally unlike every other econ-model type:
    this data lives at the TOP LEVEL of the model dict (`model['risking']`), never under
    `model['data']`.

    `risk_prod`/`risk_ngl_drip_cond_via_gas_risk` are `Optional[bool]`: absent/`None`
    means "not set", which CC's CSV renders as `'yes'` -- the same display as an
    explicit `true` (see `RiskingMapper._risk_flag_csv`). `False` IS real data --
    `riskProd: false` -> CSV `'Risk Hist Prod' == 'no'`.
    """

    model_config = ConfigDict(populate_by_name=True)

    risk_prod: Annotated[Optional[bool], Field(alias='riskProd')] = None
    risk_ngl_drip_cond_via_gas_risk: Annotated[Optional[bool], Field(alias='riskNglDripCondViaGasRisk')] = None
    oil: RiskingPhaseNode = Field(default_factory=RiskingPhaseNode)
    gas: RiskingPhaseNode = Field(default_factory=RiskingPhaseNode)
    ngl: RiskingPhaseNode = Field(default_factory=RiskingPhaseNode)
    drip_condensate: Annotated[RiskingPhaseNode, Field(alias='dripCondensate')] = Field(
        default_factory=RiskingPhaseNode
    )
    water: RiskingPhaseNode = Field(default_factory=RiskingPhaseNode)


class RiskingMapper:
    """Row-based mapper for the Risking econ-model type.

    DOCUMENTED LIMITATION -- the CSV 'wells' row: every real CC Risking CSV export also
    contains a constant `Key == 'wells'` row (`Value == '1'`, `Criteria == 'fpd'`,
    `Period == 'ecl'`, every other column blank) on most (not all) models. It is NOT
    recoverable from the API: two models byte-identical in `model['risking']` (both
    `riskProd == true`) can differ in whether the CSV carries a wells row -- so its
    presence depends on state the `risking` endpoint does not expose anywhere in the
    object.

    Decision: `to_csv_rows` emits ONLY the 5 phase rows (oil, gas, ngl, drip cond,
    water) and never emits a wells row. `from_csv_rows` IGNORES any `Key == 'wells'`
    rows on input -- there is no API field to route them to. This means
    `to_csv_rows(from_csv_rows(rows))` will not reproduce a wells row present in the
    original `rows`; that is expected and is the sole forward/round-trip gap for this
    type (see forward_diff.py and test_fixtures.py).
    """

    econ_model_type = 'Risking'
    columns = COLUMNS['Risking']

    def to_csv_rows(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        common = common_columns(model, context)
        data = RiskingModel.model_validate(model.get('risking') or {})

        risk_prod_csv = self._risk_flag_csv(data.risk_prod)
        risk_ngl_csv = self._risk_flag_csv(data.risk_ngl_drip_cond_via_gas_risk)

        rows: List[Dict[str, str]] = []
        for attr, phase_csv in _PHASE_ORDER:
            phase_node: RiskingPhaseNode = getattr(data, attr)
            for r in phase_node.rows:
                formats.check_entire_well_life(r.entire_well_life)
                csv_row = dict(common)
                csv_row.update(
                    {
                        'Key': _KEY_CSV,
                        'Phase': phase_csv,
                        'Category': '',
                        'Description': '',
                        'Risk Hist Prod': risk_prod_csv,
                        'Risk NGL & Drip Cond via Gas Risk': risk_ngl_csv,
                        'Value': num_to_csv(r.multiplier),
                        'Period': '',
                        'Criteria': 'flat',
                        'Criteria Start': '',
                        'Criteria End': '',
                        'Repeat Range Of Dates': '',
                        'Total Occurrences': '',
                        'Unit': '%',
                        'Scale Post Shut-in Factor': '',
                        'Scale Post Shut-In End Criteria': '',
                        'Scale Post Shut-In End': '',
                        'Fixed Expense': '',
                        'CAPEX': '',
                    }
                )
                rows.append({c: csv_row.get(c, '') for c in self.columns})
        return rows

    @staticmethod
    def _risk_flag_csv(value: Optional[bool]) -> str:
        return formats.yes_no(True if value is None else value)

    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        name, unique = model_identity(rows)
        risk_prod_csv: Optional[str] = None
        risk_ngl_csv: Optional[str] = None
        phase_members: Dict[str, List[Dict[str, str]]] = {attr: [] for attr, _ in _PHASE_ORDER}

        for row in rows:
            key = row.get('Key', '')
            if key == _WELLS_KEY_CSV:
                # Not recoverable from the API -- see class docstring. Ignored on input.
                continue
            if key != _KEY_CSV:
                raise NotImplementedError(f'Unknown Risking Key: {key!r}')
            phase_csv = row.get('Phase', '')
            if phase_csv not in _PHASE_FROM_CSV:
                raise NotImplementedError(f'Unknown Risking Phase: {phase_csv!r}')
            phase_members[_PHASE_FROM_CSV[phase_csv]].append(row)
            if risk_prod_csv is None:
                risk_prod_csv = row.get('Risk Hist Prod', '')
            if risk_ngl_csv is None:
                risk_ngl_csv = row.get('Risk NGL & Drip Cond via Gas Risk', '')

        kwargs: Dict[str, Any] = {}
        for attr, _ in _PHASE_ORDER:
            phase_rows: List[RiskingMultiplierRow] = []
            for member in phase_members[attr]:
                if member['Criteria'] != 'flat':
                    raise NotImplementedError(f'Unknown Risking Criteria: {member["Criteria"]!r}')
                phase_rows.append(
                    RiskingMultiplierRow(
                        entire_well_life=formats.ENTIRE_WELL_LIFE_MARKER, multiplier=csv_to_num(member['Value'])
                    )
                )
            kwargs[attr] = RiskingPhaseNode(rows=phase_rows)

        data = RiskingModel(
            risk_prod=formats.parse_yes_no(risk_prod_csv or ''),
            risk_ngl_drip_cond_via_gas_risk=formats.parse_yes_no(risk_ngl_csv or ''),
            **kwargs,
        )

        return {
            'name': name,
            'unique': unique,
            'risking': data.model_dump(by_alias=True, exclude_none=True),
        }
