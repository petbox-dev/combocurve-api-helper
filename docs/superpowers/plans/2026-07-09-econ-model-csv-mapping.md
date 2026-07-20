# Econ-Model API <-> CSV Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a typed, exact, invertible mapping between ComboCurve econ-model API JSON and CC's relational CSV export, for StreamProperties, Differentials, ProductionTaxes, Expenses, and Capex, in `combocurve-api-helper`.

**Architecture:** New subpackage `combocurve_api_helper/econ_models/`. Each type has a row-level pydantic `BaseModel` (the validated intermediate, cc-afe-sync style) plus `to_csv_rows(model) -> list[dict]` (forward flatten, API->CSV) and `from_csv_rows(rows) -> dict` (inverse build, CSV->API JSON), sharing `enums.py` (moved from cc-afe-sync), `csv_columns.py` (ordered columns), `formats.py` (value formatters), and `base.py` (mapper protocol + registry). Round-trip tests pin exactness.

**Tech Stack:** Python >=3.8, pydantic v2, pytest, mypy --strict.

## Global Constraints

- **Python floor is 3.8** — no stdlib `enum.StrEnum` (3.11+). Use the `class StrEnum(str, Enum): pass` shim (as cc-afe-sync does). No `match`, no `X | Y` unions in annotations; use `Optional[...]`/`Union[...]`.
- **pydantic v2** is added to `dependencies` in `pyproject.toml` (`pydantic>=2,<3`). Models use `Field(alias=...)`; parse with `model_validate`, dump API JSON with `model_dump(by_alias=True, exclude_none=True)`.
- All functions fully type-annotated; `python -m mypy --strict src/combocurve_api_helper/econ_models` passes.
- **The CSV vocabulary is fixed and verified** — see `docs/superpowers/specs/2026-07-08-econ-model-csv-mapping-design.md`. Emit exactly these strings; the round-trip tests enforce it.
- **Model Type**: lowercase `unique` if `unique` else `project`.
- **Dates**: `MM/DD/YYYY`; **Created At / Last Update**: `MM/DD/YYYY HH:MM:SS`. API values are ISO-8601.
- **Escalation/Depreciation**: pass the API value through (`none`/`None`/id); no id->name resolution (v1).
- **Booleans are per-column**: helper `yes_blank(b)` -> `'yes'`/`''`; `yes_no(b)` -> `'yes'`/`'no'`.
- **Common columns** (every type): `Model Id, Created At, Project Name, Model Type, Model Name, New Name, Embedded Lookup Table, <type cols>, Last Update`. `Model Id`/`Created At`/`Project Name` are emitted only when a `context` (id, created_at, project_name) is passed; `New Name`=None, `Embedded Lookup Table`=None for pulled models.
- Capex emits `otherCapex.rows` only; `$/ft` `drillingCost`/`completionCost` are NOT exported (warn if present).
- Unknown enum tokens / value keys raise `NotImplementedError` (fail loud; exactness matters).

---

### Task 1: pydantic dependency + `enums.py` (moved from cc-afe-sync) + CSV vocab formatters

**Files:**
- Modify: `pyproject.toml` (add `pydantic>=2,<3` to `dependencies`)
- Create: `src/combocurve_api_helper/econ_models/__init__.py` (empty for now)
- Create: `src/combocurve_api_helper/econ_models/enums.py`
- Create: `src/combocurve_api_helper/econ_models/formats.py`
- Test: `src/combocurve_api_helper/econ_models/test_enums_formats.py`

**Interfaces — Produces:**
- `StrEnum` shim; enums `Criteria`, `OffsetTo`, `CapExCategory`, `GrossOrNet` (API string values).
- `CRITERIA_TO_CSV: Dict[str, str]`, `CRITERIA_FROM_CSV: Dict[str, str]` (inverse).
- `OFFSET_TO_HEADER_CSV`, `OFFSET_TO_SCHEDULE_CSV` (+ inverses) mapping `OffsetTo` value <-> CSV display.
- `model_type(unique: bool) -> str`; `to_csv_date(iso: Optional[str]) -> str`; `to_csv_datetime(iso: Optional[str]) -> str`; `from_csv_date(s: str) -> str` (-> ISO); `yes_blank(b: Optional[bool]) -> str`; `yes_no(b: Optional[bool]) -> str`; and their inverses `parse_yes_blank`, `parse_yes_no`.

- [ ] **Step 1: Write failing tests** — `test_enums_formats.py`:
```python
from combocurve_api_helper.econ_models import formats as F
from combocurve_api_helper.econ_models.enums import Criteria, CRITERIA_TO_CSV, CRITERIA_FROM_CSV


def test_criteria_csv_roundtrip():
    assert CRITERIA_TO_CSV[Criteria.FPD.value] == 'fpd'
    assert CRITERIA_TO_CSV[Criteria.EconLimit.value] == 'econ limit'
    assert CRITERIA_TO_CSV[Criteria.FromHeaders.value] == 'from headers'
    assert CRITERIA_TO_CSV[Criteria.MajorSegment.value] == 'maj seg'
    assert CRITERIA_TO_CSV[Criteria.TotalFluidRate.value] == 'total fluid rate'
    for api, csv in CRITERIA_TO_CSV.items():
        assert CRITERIA_FROM_CSV[csv] == api  # invertible


def test_model_type():
    assert F.model_type(True) == 'unique'
    assert F.model_type(False) == 'project'


def test_dates():
    assert F.to_csv_date('2026-07-08') == '07/08/2026'
    assert F.to_csv_datetime('2026-05-08T14:18:05.000Z') == '05/08/2026 14:18:05'
    assert F.from_csv_date('07/08/2026') == '2026-07-08'
    assert F.to_csv_date(None) == ''


def test_bools():
    assert (F.yes_blank(True), F.yes_blank(False), F.yes_blank(None)) == ('yes', '', '')
    assert (F.yes_no(True), F.yes_no(False)) == ('yes', 'no')
    assert (F.parse_yes_blank('yes'), F.parse_yes_blank('')) == (True, False)
    assert (F.parse_yes_no('yes'), F.parse_yes_no('no')) == (True, False)
```

- [ ] **Step 2: Run — expect fail** (`ModuleNotFoundError`).
Run: `python -m pytest src/combocurve_api_helper/econ_models/test_enums_formats.py -v`

- [ ] **Step 3: Add pydantic to `pyproject.toml`** — under `dependencies = [ ... ]` add `'pydantic>=2,<3',`. Run `pip install -e .` (or `pip install 'pydantic>=2,<3'`).

- [ ] **Step 4: Create `enums.py`** — move the four `StrEnum`s from `cc-afe-sync/src/cc_afe_sync/models/capex.py` verbatim (the shim + `Criteria`, `OffsetTo`, `CapExCategory`, `GrossOrNet`), then add the CSV maps:
```python
from enum import Enum
from typing import Dict


class StrEnum(str, Enum):  # Python <3.11 shim
    pass


class Criteria(StrEnum):
    FromHeaders = "fromHeaders"
    FromSchedule = "fromSchedule"
    Date = "date"
    AsOf = "offsetToAsOf"
    DiscountDate = "offsetToDiscountDate"
    FPD = "offsetToFpd"
    EconLimit = "offsetToEconLimit"
    MajorSegment = "offsetToMajorSegment"
    OilRate = "oilRate"
    GasRate = "gasRate"
    WaterRate = "waterRate"
    TotalFluidRate = "totalFluidRate"


class OffsetTo(StrEnum):
    _None = ""
    PermitDate = "offset_to_permit_date"
    SpudDate = "offset_to_spud_date"
    RigReleaseDate = "offset_to_rig_release_date"
    DrillStartDate = "offset_to_drill_start_date"
    DrillEndDate = "offset_to_drill_end_date"
    CompletionStartDate = "offset_to_completion_start_date"
    CompletionEndDate = "offset_to_completion_end_date"
    FirstProductionDate = "offset_to_first_production_date"
    TIL = "offset_to_til"
    RefracDate = "offset_to_refrac_date"
    FirstProdDateDailyCalc = "offset_to_first_prod_date_daily_calc"
    FirstPProdDateMonthlyCalc = "offset_to_first_prod_date_monthly_calc"
    LastProdDateDailyCalc = "offset_to_last_prod_date_daily_calc"
    LastProdDateMonthlyCalc = "offset_to_last_prod_date_monthly_calc"
    CustomDate0 = "offset_to_custom_date_0"
    CustomDate1 = "offset_to_custom_date_1"
    CustomDate2 = "offset_to_custom_date_2"
    CustomDate3 = "offset_to_custom_date_3"
    CustomDate4 = "offset_to_custom_date_4"
    CustomDate5 = "offset_to_custom_date_5"
    CustomDate6 = "offset_to_custom_date_6"
    CustomDate7 = "offset_to_custom_date_7"
    CustomDate8 = "offset_to_custom_date_8"
    CustomDate9 = "offset_to_custom_date_9"


class CapExCategory(StrEnum):
    Exploration = "exploration"
    Appraisal = "appraisal"
    Pad = "pad"
    Drilling = "drilling"
    Completion = "completion"
    Facilities = "facilities"
    OtherInvestment = "other_investment"
    ArtificialLift = "artificial_lift"
    Salvage = "salvage"
    Abandonment = "abandonment"
    Legal = "legal"
    Workover = "workover"
    Leasehold = "leasehold"
    Development = "development"
    Pipelines = "pipelines"
    Waterline = "waterline"


class GrossOrNet(StrEnum):
    Gross = "gross"
    Net = "net"


# API criteria value -> CSV Criteria string (verified against exports)
CRITERIA_TO_CSV: Dict[str, str] = {
    Criteria.FromHeaders.value: "from headers",
    Criteria.FromSchedule.value: "from schedule",
    Criteria.Date.value: "date",
    Criteria.AsOf.value: "as of",
    Criteria.DiscountDate.value: "disc date",
    Criteria.FPD.value: "fpd",
    Criteria.EconLimit.value: "econ limit",
    Criteria.MajorSegment.value: "maj seg",
    Criteria.OilRate.value: "oil rate",
    Criteria.GasRate.value: "gas rate",
    Criteria.WaterRate.value: "water rate",
    Criteria.TotalFluidRate.value: "total fluid rate",
}
CRITERIA_FROM_CSV: Dict[str, str] = {v: k for k, v in CRITERIA_TO_CSV.items()}

# OffsetTo value -> CSV display (only the values observed in exports are mapped;
# extend as new ones surface — an unmapped token raises in the mapper).
OFFSET_TO_HEADER_CSV: Dict[str, str] = {
    OffsetTo.SpudDate.value: "Spud Date",
    OffsetTo.CompletionStartDate.value: "Completion Start Date",
}
OFFSET_TO_SCHEDULE_CSV: Dict[str, str] = {
    OffsetTo.SpudDate.value: "Spud Start",
    OffsetTo.CompletionStartDate.value: "Completion Start",
}
OFFSET_FROM_HEADER_CSV: Dict[str, str] = {v: k for k, v in OFFSET_TO_HEADER_CSV.items()}
OFFSET_FROM_SCHEDULE_CSV: Dict[str, str] = {v: k for k, v in OFFSET_TO_SCHEDULE_CSV.items()}
```
(cc-afe-sync will later `from combocurve_api_helper.econ_models.enums import Criteria, ...`; that edit is out of scope here and tracked as follow-up.)

- [ ] **Step 5: Create `formats.py`**:
```python
import datetime
from typing import Optional


def model_type(unique: bool) -> str:
    return "unique" if unique else "project"


def _parse_iso(value: str) -> datetime.datetime:
    v = value.replace("Z", "+00:00") if value.endswith("Z") else value
    return datetime.datetime.fromisoformat(v)


def to_csv_date(iso: Optional[str]) -> str:
    if not iso:
        return ""
    return _parse_iso(iso).strftime("%m/%d/%Y")


def to_csv_datetime(iso: Optional[str]) -> str:
    if not iso:
        return ""
    return _parse_iso(iso).strftime("%m/%d/%Y %H:%M:%S")


def from_csv_date(s: str) -> str:
    if not s:
        return ""
    return datetime.datetime.strptime(s, "%m/%d/%Y").date().isoformat()


def yes_blank(b: Optional[bool]) -> str:
    return "yes" if b else ""


def yes_no(b: Optional[bool]) -> str:
    return "yes" if b else "no"


def parse_yes_blank(s: str) -> bool:
    return s.strip().lower() == "yes"


def parse_yes_no(s: str) -> bool:
    return s.strip().lower() == "yes"
```

- [ ] **Step 6: Run tests + mypy** — `python -m pytest src/combocurve_api_helper/econ_models/test_enums_formats.py -v` (pass); `python -m mypy --strict src/combocurve_api_helper/econ_models/enums.py src/combocurve_api_helper/econ_models/formats.py`.

- [ ] **Step 7: Commit** — `git add pyproject.toml src/combocurve_api_helper/econ_models && git commit -m "feat(econ_models): enums (moved from cc-afe-sync) + CSV format helpers"`

---

### Task 2: `csv_columns.py` (ordered column contracts) + `base.py` (mapper protocol, common columns, registry)

**Files:**
- Create: `src/combocurve_api_helper/econ_models/csv_columns.py`
- Create: `src/combocurve_api_helper/econ_models/base.py`
- Test: `src/combocurve_api_helper/econ_models/test_base.py`

**Interfaces — Consumes:** `formats`. **Produces:**
- `COLUMNS: Dict[str, List[str]]` keyed by econModelType (`StreamProperties`,`Differentials`,`ProductionTaxes`,`Expenses`,`Capex`), each the full ordered CSV column list (common + type cols).
- `Context` (`NamedTuple`: `id: Optional[str]`, `created_at: Optional[str]`, `project_name: Optional[str]`).
- `common_columns(model, context) -> Dict[str, str]` producing `Model Id/Created At/Project Name/Model Type/Model Name/New Name/Embedded Lookup Table/Last Update` (Model Id/Created At/Project Name only when context provided).
- `EconModelMapper` protocol: `econ_model_type: str`, `columns: List[str]`, `to_csv_rows(model: Dict[str, Any], context: Optional[Context]) -> List[Dict[str, str]]`, `from_csv_rows(rows: List[Dict[str, str]]) -> Dict[str, Any]`.

- [ ] **Step 1: Failing test** — `test_base.py`:
```python
from combocurve_api_helper.econ_models.csv_columns import COLUMNS
from combocurve_api_helper.econ_models.base import Context, common_columns


def test_columns_have_five_types_and_lead_with_common():
    assert set(COLUMNS) == {'StreamProperties', 'Differentials', 'ProductionTaxes', 'Expenses', 'Capex'}
    for cols in COLUMNS.values():
        assert cols[:7] == ['Model Id', 'Created At', 'Project Name', 'Model Type',
                            'Model Name', 'New Name', 'Embedded Lookup Table']
        assert cols[-1] == 'Last Update'


def test_common_columns_with_context():
    m = {'id': 'x1', 'name': 'M', 'unique': False,
         'createdAt': '2026-05-08T14:18:05.000Z', 'updatedAt': '2026-05-08T14:18:05.000Z'}
    ctx = Context(id='x1', created_at=m['createdAt'], project_name='ProjA')
    c = common_columns(m, ctx)
    assert c['Model Id'] == 'x1'
    assert c['Project Name'] == 'ProjA'
    assert c['Model Type'] == 'project'
    assert c['Model Name'] == 'M'
    assert c['New Name'] == '' and c['Embedded Lookup Table'] == ''
    assert c['Last Update'] == '05/08/2026 14:18:05'


def test_common_columns_without_context_omits_pipeline_cols():
    m = {'id': 'x1', 'name': 'M', 'unique': True, 'createdAt': '2026-05-08T14:18:05.000Z',
         'updatedAt': '2026-05-08T14:18:05.000Z'}
    c = common_columns(m, None)
    assert 'Model Id' not in c and 'Project Name' not in c
    assert c['Model Type'] == 'unique'
```

- [ ] **Step 2: Run — expect fail.**

- [ ] **Step 3: Create `csv_columns.py`** — the exact ordered lists (common 7 + type cols + `Last Update`). Type cols per the spec:
```python
from typing import Dict, List

_COMMON_HEAD = ['Model Id', 'Created At', 'Project Name', 'Model Type', 'Model Name', 'New Name', 'Embedded Lookup Table']

COLUMNS: Dict[str, List[str]] = {
    'StreamProperties': _COMMON_HEAD + [
        'Key', 'Category', 'Criteria', 'Value', 'Period', 'Unit', 'Gas Shrinkage Condition',
        'Rate Type', 'Rate Rows Calculation Method', 'Yield Source', 'Yield (BBL/MMCF)', 'Mol %',
        'Gal/lb-mol Factor', 'Plant Eff (%)', 'Shrink (% Remaining)', 'BTU (MBTU/MCF)', 'Post Extraction (%)',
    ] + ['Last Update'],
    'Differentials': _COMMON_HEAD + [
        'Key', 'Phase', 'Criteria', 'Value', 'Period', 'Unit', 'Escalation',
    ] + ['Last Update'],
    'ProductionTaxes': _COMMON_HEAD + [
        'Production Taxes State', 'Key', 'Stream Type', 'Category', 'Criteria', 'Value', 'Period', 'Unit',
        'Description', 'Shrinkage Condition', 'Escalation', 'Calculation', 'Deduct Severance Tax',
        'Rate Type', 'Rate Rows Calculation Method',
    ] + ['Last Update'],
    'Expenses': _COMMON_HEAD + [
        'Key', 'Category', 'Criteria', 'Value', 'Period', 'Unit', 'Description', 'Shrinkage Condition',
        'Escalation', 'Calculation', 'Affect Econ Limit', 'Deduct bef Sev Tax', 'Deduct bef Ad Val Tax',
        'Stop at Econ Limit', 'Expense bef FPD', 'Cap', 'Paying WI / Earning WI',
        'Rate Type', 'Rate Rows Calculation Method',
    ] + ['Last Update'],
    'Capex': _COMMON_HEAD + [
        'Category', 'Description', 'Tangible (M$)', 'Intangible (M$)', 'Criteria', 'From Schedule',
        'From Headers', 'Value', 'CAPEX or Expense', 'Appear After Econ Limit', 'Calculation', 'Escalation',
        'Escalation Start Criteria', 'Escalation Start Value (Days/Date)', 'Depreciation', 'Paying WI / Earning WI',
    ] + ['Last Update'],
}
```

- [ ] **Step 4: Create `base.py`**:
```python
from typing import Any, Dict, List, NamedTuple, Optional
from typing_extensions import Protocol

from . import formats


class Context(NamedTuple):
    id: Optional[str] = None
    created_at: Optional[str] = None
    project_name: Optional[str] = None


def common_columns(model: Dict[str, Any], context: Optional[Context]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if context is not None:
        out['Model Id'] = context.id or model.get('id', '') or ''
        out['Created At'] = formats.to_csv_datetime(context.created_at or model.get('createdAt'))
        out['Project Name'] = context.project_name or ''
    out['Model Type'] = formats.model_type(bool(model.get('unique', False)))
    out['Model Name'] = model.get('name', '') or ''
    out['New Name'] = ''
    out['Embedded Lookup Table'] = ''
    out['Last Update'] = formats.to_csv_datetime(model.get('updatedAt'))
    return out


class EconModelMapper(Protocol):
    econ_model_type: str
    columns: List[str]

    def to_csv_rows(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]: ...
    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]: ...
```
(`typing_extensions` is already available via the helper's deps; if mypy flags it, use `typing.Protocol` — Python 3.8 has it.)

- [ ] **Step 5: Run tests + mypy** (pass). **Step 6: Commit** — `git commit -m "feat(econ_models): CSV column contracts + mapper base"`.

---

### Task 3: Differentials mapper (establishes the forward/inverse + round-trip pattern)

**Files:**
- Create: `src/combocurve_api_helper/econ_models/differentials.py`
- Test: `src/combocurve_api_helper/econ_models/test_differentials.py`

**Interfaces — Consumes:** `enums`, `formats`, `csv_columns.COLUMNS`, `base.Context/common_columns`. **Produces:** `DifferentialsMapper` (implements `EconModelMapper`), `econ_model_type='Differentials'`.

Mapping (verified): `Key` = `differentials_1|2|3` from `firstDifferential|secondDifferential|thirdDifferential`; `Phase` = `oil|gas|ngl|drip cond` from `oil|gas|ngl|dripCondensate`; per row, value/unit from the single populated key (`dollarPerBbl`->`$/bbl`, `dollarPerMcf`->`$/mcf`, `dollarPerMmbtu`->`$/mmbtu`, `pctOfBasePrice`->`% base price rem`); `Criteria` `flat` (`entireWellLife`) / `dates`; `Period` = `to_csv_date(dates)` or `''`; `Escalation` = `escalationModel`.

- [ ] **Step 1: Failing round-trip test** — `test_differentials.py`:
```python
from combocurve_api_helper.econ_models.differentials import DifferentialsMapper

API = {
    'id': 'd1', 'name': 'Sample Differentials', 'unique': False,
    'createdAt': '2026-05-10T03:11:41.000Z', 'updatedAt': '2026-05-10T03:11:41.000Z',
    'econModelType': 'Differentials',
    'differentials': {
        'firstDifferential': {
            'oil': {'escalationModel': 'none', 'rows': [{'dates': '2027-01-01', 'dollarPerBbl': -2.54}]},
            'gas': {'escalationModel': 'none', 'rows': [{'dates': '2027-01-01', 'dollarPerMmbtu': -0.17}]},
            'ngl': {'escalationModel': 'none', 'rows': [{'entireWellLife': 'Flat', 'pctOfBasePrice': 32}]},
            'dripCondensate': {'escalationModel': 'none', 'rows': [{'entireWellLife': 'Flat', 'dollarPerBbl': 0}]},
        },
        'secondDifferential': {}, 'thirdDifferential': {},
    },
}


def test_to_csv_rows_values():
    rows = DifferentialsMapper().to_csv_rows(API)
    assert len(rows) == 4
    oil = next(r for r in rows if r['Phase'] == 'oil')
    assert oil['Key'] == 'differentials_1'
    assert (oil['Criteria'], oil['Period'], oil['Value'], oil['Unit']) == ('dates', '01/01/2027', '-2.54', '$/bbl')
    gas = next(r for r in rows if r['Phase'] == 'gas')
    assert gas['Unit'] == '$/mmbtu'
    ngl = next(r for r in rows if r['Phase'] == 'ngl')
    assert (ngl['Criteria'], ngl['Period'], ngl['Unit']) == ('flat', '', '% base price rem')


def test_roundtrip():
    m = DifferentialsMapper()
    rebuilt = m.from_csv_rows(m.to_csv_rows(API))
    assert rebuilt['differentials'] == API['differentials']
    assert rebuilt['name'] == 'Sample Differentials' and rebuilt['unique'] is False
```

- [ ] **Step 2: Run — expect fail.**

- [ ] **Step 3: Implement `differentials.py`**:
```python
from typing import Any, Dict, List, Optional, Tuple

from . import formats
from .base import Context, common_columns
from .csv_columns import COLUMNS

_TIER_TO_CSV = {'firstDifferential': 'differentials_1', 'secondDifferential': 'differentials_2', 'thirdDifferential': 'differentials_3'}
_TIER_FROM_CSV = {v: k for k, v in _TIER_TO_CSV.items()}
_PHASE_TO_CSV = {'oil': 'oil', 'gas': 'gas', 'ngl': 'ngl', 'dripCondensate': 'drip cond'}
_PHASE_FROM_CSV = {v: k for k, v in _PHASE_TO_CSV.items()}
_VALUE_UNIT = [('dollarPerBbl', '$/bbl'), ('dollarPerMcf', '$/mcf'), ('dollarPerMmbtu', '$/mmbtu'), ('pctOfBasePrice', '% base price rem')]
_UNIT_TO_KEY = {u: k for k, u in _VALUE_UNIT}


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
                esc = node.get('escalationModel')
                for r in node.get('rows', []):
                    value, unit = self._value_unit(r)
                    criteria, period = self._criteria(r)
                    row = dict(common)
                    row.update({
                        'Key': _TIER_TO_CSV[tier], 'Phase': _PHASE_TO_CSV[phase],
                        'Criteria': criteria, 'Value': _num(value), 'Period': period, 'Unit': unit,
                        'Escalation': '' if esc is None else str(esc),
                    })
                    rows.append({c: row.get(c, '') for c in self.columns})
        return rows

    @staticmethod
    def _value_unit(r: Dict[str, Any]) -> Tuple[Any, str]:
        for k, u in _VALUE_UNIT:
            if k in r:
                return r[k], u
        raise NotImplementedError(f'Unknown differential value: {r}')

    @staticmethod
    def _criteria(r: Dict[str, Any]) -> Tuple[str, str]:
        if 'entireWellLife' in r:
            return 'flat', ''
        if 'dates' in r:
            return 'dates', formats.to_csv_date(r['dates'])
        raise NotImplementedError(f'Unknown differential criteria: {r}')

    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        diffs: Dict[str, Any] = {'firstDifferential': {}, 'secondDifferential': {}, 'thirdDifferential': {}}
        name = ''; unique = False
        for row in rows:
            name = row.get('Model Name', name); unique = row.get('Model Type') == 'unique'
            tier = _TIER_FROM_CSV[row['Key']]; phase = _PHASE_FROM_CSV[row['Phase']]
            node = diffs[tier].setdefault(phase, {'escalationModel': row.get('Escalation') or 'none', 'rows': []})
            r: Dict[str, Any] = {}
            if row['Criteria'] == 'flat':
                r['entireWellLife'] = 'Flat'
            else:
                r['dates'] = formats.from_csv_date(row['Period'])
            r[_UNIT_TO_KEY[row['Unit']]] = _renum(row['Value'])
            node['rows'].append(r)
        return {'name': name, 'unique': unique, 'differentials': diffs}
```
Add module-level helpers `_num`/`_renum` to `formats.py` in Step 3 of THIS task (extend that file):
```python
def _num(value: Any) -> str:  # export as num_to_csv
    ...
```
Actually put these in `formats.py`: `num_to_csv(v) -> str` (int/float -> str, `int` stays integral e.g. `-120` not `-120.0`; float keeps precision) and `csv_to_num(s) -> Union[int, float]`. Import them here as `from .formats import num_to_csv as _num, csv_to_num as _renum`.

- [ ] **Step 4: Run test + mypy** (pass). **Step 5: Commit** — `git commit -m "feat(econ_models): Differentials API<->CSV mapper + round-trip test"`.

---

### Task 4: StreamProperties mapper

**Files:** Create `src/combocurve_api_helper/econ_models/stream_properties.py`; Test `.../test_stream_properties.py`.
**Interfaces — Produces:** `StreamPropertiesMapper`, `econ_model_type='StreamProperties'`.

Reuse the flatten logic proven in the held branch `cc-api-scripts:feature/cc-econ-models-sync` (`src/cc_model_parsers.py` `StreamPropertiesParser`), re-emitting to the exact CSV columns. Mapping (verified): `Key` `yields|shrinkage|loss & flare|btu`; `Category` `oil|gas|ngl|drip cond|oil loss|gas loss|gas flare|unshrunk gas|shrunk gas|water`; `Criteria` `flat`/`dates`; yields Unit `bbl/mmcf`, shrink/loss Unit `% remaining`, btu Unit `mbtu/mcf`; `Gas Shrinkage Condition` `unshrunk` when present; `Value` numeric. `Model Type` lowercase (the only change vs the held parser). Empty `companyCustomStreams` dropped; a non-empty list raises.

- [ ] **Step 1: Failing round-trip test** — build an API StreamProperties model (yields ngl/dripCondensate, shrinkage oil/gas, lossFlare oilLoss/gasLoss/gasFlare, btuContent unshrunkGas/shrunkGas, `companyCustomStreams: []`), assert `to_csv_rows` yields 9 rows with the exact Key/Category/Value/Unit above (e.g. ngl yields row `Value='99.67364'`, `Unit='bbl/mmcf'`; gas shrinkage `Unit='% remaining'`), and `from_csv_rows(to_csv_rows(m))` reproduces `m`'s `yields`/`shrinkage`/`lossFlare`/`btuContent`.
- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** the mapper following the Task 3 structure: a `to_csv_rows` that walks `yields`/`shrinkage`/`lossFlare` (each `{rateType, rowsCalculationMethod, <category>: {rows}}`) and `btuContent` (`{unshrunkGas, shrunkGas}`), emitting the StreamProperties columns; and a `from_csv_rows` that regroups rows by Key into the nested API structure. Port `_parse_keys`/`_parse_btu` semantics from the held `StreamPropertiesParser`. Rows-calculation/rate-type fields map to `Rate Type`/`Rate Rows Calculation Method`.
- [ ] **Step 4: Run + mypy. Step 5: Commit** — `git commit -m "feat(econ_models): StreamProperties API<->CSV mapper"`.

---

### Task 5: ProductionTaxes mapper

**Files:** Create `.../production_taxes.py`; Test `.../test_production_taxes.py`.
**Interfaces — Produces:** `ProductionTaxesMapper`, `econ_model_type='ProductionTaxes'`.

Mapping (verified): `Production Taxes State` = `data.state`. Severance rows (`category=severance_tax`): `Key` = phase (`oil|gas|ngl|drip cond`); `Category` = `Severance Tax` if the phase has one severance row else `Severance Tax 1`,`Severance Tax 2`,... by ordinal. Ad-valorem (`category=ad_valorem_tax`): `Key`=`Ad Valorem Tax`, `Category`=`Ad Val Tax`, `Deduct Severance Tax`=`yes_no(deductSeveranceTax)`. `Unit`: `pct_of_revenue`->`% of rev`, `dollar_per_bbl`->`$/bbl`, `dollar_per_mcf`->`$/mcf`. `Stream Type`/`Description` blank. Explode `period[]`/`value[]` to one row each (`flat`->Period `''`). `Escalation`/`Calculation`/`Shrinkage Condition`/`Rate Type`/`Rate Rows Calculation Method` pass through.

- [ ] **Step 1: Failing round-trip test** — Texas model with oil having TWO severance rows (`% of rev` 4.6 + `$/bbl` 0.0081) and an ad-valorem row (`deductSeveranceTax: False`->`no`); assert CSV `Category` = `Severance Tax 1`/`Severance Tax 2` for oil, `Ad Val Tax` for the ad-val row with `Deduct Severance Tax='no'`, `Unit` values correct; then `from_csv_rows(to_csv_rows(m))` reproduces `data`.
- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** — group `data.rows` by (phase, category); assign severance ordinals per phase (drop the numeral when a phase has exactly one). Inverse: numbered/unnumbered `Severance Tax*` -> `category=severance_tax` with `key=phase`; `Ad Val Tax` -> `category=ad_valorem_tax`. Value/period arrays: forward explodes, inverse regroups consecutive rows of the same (phase,category,ordinal) back into `period[]`/`value[]`.
- [ ] **Step 4: Run + mypy. Step 5: Commit** — `git commit -m "feat(econ_models): ProductionTaxes API<->CSV mapper"`.

---

### Task 6: Expenses mapper

**Files:** Create `.../expenses.py`; Test `.../test_expenses.py`.
**Interfaces — Produces:** `ExpensesMapper`, `econ_model_type='Expenses'`.

Mapping (verified). Variable (`variableExpenses.<phase>.<subcat>`): `Key` = phase (`oil|gas|ngl|dripCondensate|boe|totalFluid` -> `oil|gas|ngl|drip cond|boe|total_fluid`); `Category` = subcat map `{gathering:'g&p', processing:'opc', transportation:'trn', marketing:'mkt', other:'other'}`; Unit from value key (`dollarPerBbl`->`$/bbl`, `dollarPerMcf`->`$/mcf`). Fixed (`fixedExpenses.<slot>`): `Key`=`fixed`; `Category` = `{monthlyWellCost:'fixed1', otherMonthlyCost1:'fixed2', ..., otherMonthlyCost8:'fixed9'}`; Unit `$/month`; value key `fixedExpense`. Carbon (`carbonExpenses.<species>` where species in ch4/co2/co2E/n2O): `Key` = `{ch4:'ch4',co2:'co2',co2E:'co2e',n2O:'n2o'}`; `Category`=`co2e`; Unit `$/MT`; value key `carbonExpense`. Water (`waterDisposal`): `Key`=`water`; `Category`=`''`; Unit `$/bbl`; value key `dollarPerBbl`. `Criteria`: `entireWellLife`->`flat` (Period `''`); `offsetToFpd`->`fpd`, Period = `str(offsetToFpd)` with `1200`->`ecl`. Settings: `Paying WI / Earning WI`=`dealTerms`; `Description`; `Calculation`; `Escalation`=`escalationModel`; `Cap`; `Shrinkage Condition`; per-column bools `Affect Econ Limit`/`Deduct bef Sev Tax`/`Deduct bef Ad Val Tax`=`yes_blank(...)`, `Stop at Econ Limit`/`Expense bef FPD`=`yes_blank(...)`; `Rate Type`/`Rate Rows Calculation Method` pass through.

- [ ] **Step 1: Failing round-trip test** — model with oil.processing (`offsetToFpd:1200`, desc `OPC/OIL`, `dollarPerBbl:0`), gas.processing (`offsetToFpd:1200`, `dollarPerMcf:0.31`), monthlyWellCost (`fixedExpense:4100`, `offsetToFpd:1200`, desc `OPC/T`), co2 carbon (`carbonExpense:0`), waterDisposal (`dollarPerBbl:0`). Assert: oil row `Key='oil',Category='opc',Criteria='fpd',Period='ecl',Unit='$/bbl',Description='OPC/OIL'`; monthlyWellCost `Key='fixed',Category='fixed1',Unit='$/month',Period='ecl'`; co2 `Key='co2',Category='co2e',Unit='$/MT'`; water `Key='water',Category='',Unit='$/bbl'`. Then round-trip reproduces the four groups.
- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** per the maps (dedicated emit for variable/fixed/carbon/water; shared settings extractor; `ecl` handling: forward `1200`->`ecl`, `else str(n)`; inverse `ecl`->`1200`, else `int`). Inverse dispatches on `Key`: phases/boe/total_fluid -> variableExpenses; `fixed` -> fixedExpenses slot (reverse `fixedN`); carbon species -> carbonExpenses; `water` -> waterDisposal.
- [ ] **Step 4: Run + mypy. Step 5: Commit** — `git commit -m "feat(econ_models): Expenses API<->CSV mapper"`.

---

### Task 7: Capex mapper

**Files:** Create `.../capex.py`; Test `.../test_capex.py`.
**Interfaces — Consumes:** `enums.CapExCategory/Criteria/CRITERIA_*`/`OFFSET_*`. **Produces:** `CapexMapper`, `econ_model_type='Capex'`.

Mapping (verified). Rows from `otherCapex.rows` only. `Category` = `_norm(category)` (underscore->space; = `CapExCategory` space form). `Tangible (M$)`/`Intangible (M$)` = `tangible`/`intangible`. `CAPEX or Expense`=`capexExpense`. `Appear After Econ Limit`=`yes_no(afterEconLimit)`. `Calculation`=`calculation`. `Escalation`=`escalationModel`. `Escalation Start Criteria` from `escalationStart.applyToCriteria` (0 -> `apply to criteria`). `Escalation Start Value (Days/Date)` = `escalationStart` value (default `0`). `Depreciation`=`depreciationModel`. `Paying WI / Earning WI`=`dealTerms`. Criterion: detect the API criterion key on the row and map via `CRITERIA_TO_CSV`:
- `date` -> Criteria `date`, `Value`=`to_csv_date(date)`.
- `offsetToFpd`/`offsetToAsOf`/`offsetToDiscountDate`/`offsetToEconLimit`/`offsetToMajorSegment` -> Criteria `fpd|as of|disc date|econ limit|maj seg`, `Value`=`str(offset)`.
- `oilRate`/`gasRate`/`waterRate`/`totalFluidRate` -> `Value`=`str(rate)`.
- `fromHeaders` -> Criteria `from headers`, `From Headers` = `OFFSET_TO_HEADER_CSV[fromHeaders]`, `Value`=`str(companion offset, default 0)`.
- `fromSchedule` -> Criteria `from schedule`, `From Schedule` = `OFFSET_TO_SCHEDULE_CSV[fromSchedule]`, `Value`=`str(offset, default 0)`.
If `drillingCost`/`completionCost` present on the model, do NOT emit rows for them; `warnings.warn(...)` that they are omitted (not representable in this CSV).

- [ ] **Step 1: Failing round-trip test** — model with `otherCapex.rows` = [drilling `offsetToFpd:-120 intangible:3000`, completion `offsetToFpd:-30 intangible:4000`, abandonment `offsetToEconLimit:90 afterEconLimit:True intangible:70`, drilling `fromHeaders:'offset_to_spud_date'`]; assert CSV Criteria `fpd`/`fpd`/`econ limit`/`from headers`, `Value` `-120`/`-30`/`90`/`0`, `From Headers`=`Spud Date` for the last, `Appear After Econ Limit`=`yes` for abandonment; then round-trip reproduces `otherCapex.rows`. Add a second test: a model with `drillingCost` present emits no extra rows and warns.
- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** — criterion detection tries the keys in a fixed order; `_norm`/`_denorm` for Category; inverse maps CSV Criteria via `CRITERIA_FROM_CSV`, rebuilds the criterion key + companion (`From Headers`/`From Schedule` via `OFFSET_FROM_*`), and reconstructs the `escalationStart` object. Unmapped `OffsetTo` display raises `NotImplementedError`.
- [ ] **Step 4: Run + mypy. Step 5: Commit** — `git commit -m "feat(econ_models): Capex API<->CSV mapper (otherCapex; $/ft omitted)"`.

---

### Task 8: Package registry + `__init__` exports + fixture integration test + mypy sweep

**Files:** Modify `src/combocurve_api_helper/econ_models/__init__.py`; Create `.../test_fixtures.py`; Create fixtures under `src/combocurve_api_helper/econ_models/fixtures/` (trimmed CSVs: a handful of populated model rows per type, copied from `examples/`+`examples/MoreExamples/`).

**Interfaces — Produces:** `MAPPERS: Dict[str, EconModelMapper]` keyed by econModelType; `get_mapper(econ_model_type) -> EconModelMapper`; re-export the five mapper classes + `Context`.

- [ ] **Step 1: Failing test** — `test_fixtures.py`: for each type, read its trimmed fixture CSV, group rows by `Model Name`, and for each model assert `to_csv_rows(from_csv_rows(rows))` reproduces the fixture rows exactly (CSV-side round-trip, which needs no API access). Also `test_registry`: `set(MAPPERS) == {the five types}` and each `.econ_model_type` matches its key.
- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** `__init__.py` (registry + exports) and add the trimmed fixture CSVs (5-10 populated model rows per type; do NOT commit the 100-200MB originals — copy only the needed rows).
- [ ] **Step 4: Run full suite + strict mypy** — `python -m pytest src/combocurve_api_helper/econ_models -v`; `python -m mypy --strict src/combocurve_api_helper/econ_models`.
- [ ] **Step 5: Commit** — `git commit -m "feat(econ_models): registry, exports, CSV fixture round-trip tests"`.

---

## Self-Review

**Spec coverage:** enums move (T1) ✅; column contracts + common cols (T2) ✅; all 5 type mappers with verified vocab (T3-T7) ✅; forward+inverse+round-trip per type ✅; capex $/ft omit+warn (T7) ✅; registry/exports/fixtures (T8) ✅; Python 3.8 + pydantic + mypy strict (Global Constraints) ✅.

**Placeholder scan:** Task 4/5/6/7 describe the mapper *body* by mapping tables + test assertions rather than full verbatim code (the value maps and tests — the substantive, differing content — are complete; the method structure is the Task 3 pattern applied to those maps). If executing via subagents, the reviewer must confirm each mapper's round-trip test passes with the exact expected strings; that is the real gate. Tasks 1-3 and 8 carry complete code/tests.

**Type consistency:** `Context`, `common_columns`, `COLUMNS[...]`, `CRITERIA_TO_CSV/_FROM_CSV`, `OFFSET_TO_*`/`OFFSET_FROM_*`, `formats.*`, `num_to_csv`/`csv_to_num` are defined in T1/T2 and consumed unchanged in T3-T8. Every mapper exposes `econ_model_type`, `columns`, `to_csv_rows`, `from_csv_rows` per the `EconModelMapper` protocol.

**Pydantic pattern (required — matches cc-afe-sync).** Each type module defines a row-level pydantic `BaseModel` (fields with `Field(alias=...)` for the API keys), following cc-afe-sync's `CapExRow`/`CapExBuilder`: `to_csv_rows` parses the API JSON into the typed model(s) (`model_validate`) then renders CSV row dicts; `from_csv_rows` builds the typed model(s) from CSV rows then emits API JSON via `model_dump(by_alias=True, exclude_none=True)`. The typed model is the validated intermediate in both directions — not optional. Task 3 is the worked template; Tasks 4-7 define their own row models per the mapping tables and follow the same structure.

**Granularity caveat (honest):** Tasks 1-3 and 8 carry complete code. Tasks 4-7 give each type's complete, verified mapping tables + round-trip test assertions with exact expected strings, and reference Task 3's structure for the method bodies rather than repeating ~150 lines of near-parallel code five times. Under subagent-driven execution the per-type round-trip test (exact CSV strings <-> exact API JSON) is the hard gate that forces correct bodies; a reviewer must confirm it passes. If you prefer fully-inlined per-type code before execution, say so and I will expand Tasks 4-7.

---

## v2 Wave (post-final-review): pydantic refactor + forward fidelity

Decisions: refactor mappers to pydantic; fix forward direction vs real CC CSV. Expenses fpd->ecl rule = (a) the terminal fpd row in a leaf renders `Period='ecl'`, earlier rows show their month offset.

**Pydantic pattern (per type, cc-afe-sync style):** each type module defines a row-level `BaseModel` (fields with `Field(alias=<apiKey>)`) as the validated intermediate. `to_csv_rows`: `model_validate` the API leaves/rows -> render CSV dicts. `from_csv_rows`: build the row models from CSV -> assemble API JSON via `model_dump(by_alias=True, exclude_none=True)` + a builder for the nested structure. Keep every existing test green. Remove the dead top-level pydantic import gap by actually using pydantic.

**Forward fixes (verified vs real CC CSV):**
- StreamProperties: do NOT emit `btu` rows (`btuContent` not exported by CC); `Rate Type`/`Rate Rows Calculation Method` blank; specialized columns stay blank.
- Expenses: emit `boe`/`total_fluid` variable phases (currently dropped); `Rate Type`/`Rate Rows Calculation Method` blank; fpd `Period`: terminal row per leaf -> `ecl` (rule a), earlier -> month offset; inverse `ecl` -> canonical large offset (documented non-exact).
- ProductionTaxes: `escalation` (and any model-name field) `none`->`None` (title); `rateType` `gross_well_head`->`gross well head`; `rateRowsCalculationMethod` `non_monotonic`->`non monotonic` (underscore->space). NOTE escalation casing is TITLE for ProductionTaxes/Capex, lowercase for Differentials/Expenses.
- Differentials, Capex: forward already exact; refactor only.

**Regression tests:** add per-type forward assertions using CC's real CSV values as expected (e.g. SP has no btu rows + blank Rate Type; ProdTax escalation 'None' + 'gross well head'; Expenses boe/total_fluid emitted + terminal 'ecl'). Keep the scratch `forward_diff.py` (real-API->CSV) as the dev gate.

**Tasks:** v2-T1 ProductionTaxes (pilot), v2-T2 StreamProperties, v2-T3 Expenses, v2-T4 Differentials (refactor-only), v2-T5 Capex (refactor-only). Each: pydantic refactor + forward fix + regression test + all gates.
