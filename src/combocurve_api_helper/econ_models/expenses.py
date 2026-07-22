import warnings
from typing import Annotated, Any, Dict, List, NamedTuple, Optional, Set, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import formats
from .base import Context, EconModelMapper, common_columns, model_identity
from .csv_columns import COLUMNS
from .formats import csv_to_num, escalation_from_csv, escalation_to_csv, num_to_csv, num_to_csv_float

# API phase (variableExpenses top-level key) -> CSV 'Key' column value. `boe`/
# `totalFluid` ARE real phases. Unlike oil/gas/ngl/dripCondensate, their REAL
# API shape is DOUBLE-NESTED under the subcat key:
# `variableExpenses.boe == {"processing": {"processing": {<leaf>}}}` (and identically
# for `totalFluid`) -- i.e. `variableExpenses[phase][subcat][subcat]` is the real leaf,
# not `variableExpenses[phase][subcat]` as for every other phase. See
# `_DOUBLE_NESTED_PHASES` / `_unwrap_variable_leaf` (forward unwrap, structural
# detection) and `from_row_dicts` (inverse re-nesting, phase-name-gated since only
# these two phases need it).
_PHASE_TO_CSV = {
    'oil': 'oil',
    'gas': 'gas',
    'ngl': 'ngl',
    'dripCondensate': 'drip cond',
    'boe': 'boe',
    'totalFluid': 'total_fluid',
}
_PHASE_FROM_CSV = {v: k for k, v in _PHASE_TO_CSV.items()}

# Phases whose real leaves are double-nested under the subcat key (see _PHASE_TO_CSV
# comment above). boe/totalFluid only ever populate the 'processing' subcat, so the
# inverse always re-nests as {subcat: {subcat: leaf}} for these two phases specifically.
_DOUBLE_NESTED_PHASES = {'boe', 'totalFluid'}

# Real API leaf-identifying keys: every genuine ExpenseLeaf dict carries at least one
# of these settings keys (even when its value is null/empty), so checking for ANY of
# them distinguishes a real leaf from the boe/totalFluid double-nesting wrapper, whose
# only key is the repeated subcat name (e.g. {'processing': {<leaf>}}) with no
# leaf-settings keys of its own.
_LEAF_MARKER_KEYS = {
    'rows',
    'description',
    'calculation',
    'escalationModel',
    'shrinkageCondition',
    'affectEconLimit',
    'deductBeforeSeveranceTax',
    'deductBeforeAdValTax',
    'cap',
    'dealTerms',
    'rateType',
    'rowsCalculationMethod',
}

# API subcat (variableExpenses.<phase> key) -> CSV 'Category' column value.
_SUBCAT_TO_CSV = {
    'gathering': 'g&p',
    'processing': 'opc',
    'transportation': 'trn',
    'marketing': 'mkt',
    'other': 'other',
}
_SUBCAT_FROM_CSV = {v: k for k, v in _SUBCAT_TO_CSV.items()}

# fixedExpenses slot -> CSV 'Category' column value (monthlyWellCost -> fixed1,
# otherMonthlyCost1..8 -> fixed2..fixed9).
_FIXED_SLOTS = ['monthlyWellCost'] + [f'otherMonthlyCost{i}' for i in range(1, 9)]
_FIXED_KEY_CSV = 'fixed'
_FIXED_SLOT_TO_CSV = {slot: f'fixed{i + 1}' for i, slot in enumerate(_FIXED_SLOTS)}
_FIXED_SLOT_FROM_CSV = {v: k for k, v in _FIXED_SLOT_TO_CSV.items()}

# carbonExpenses species -> CSV 'Key' column value. All carbon rows share CSV
# Category 'co2e' regardless of species.
_CARBON_SPECIES_TO_CSV = {'ch4': 'ch4', 'co2': 'co2', 'co2E': 'co2e', 'n2O': 'n2o'}
_CARBON_SPECIES_FROM_CSV = {v: k for k, v in _CARBON_SPECIES_TO_CSV.items()}
# carbonExpenses also carries a model-level scalar 'category' key (API) sitting
# alongside the species dicts -- always 'co2e' in the real API shape. This is a
# known, documented CSV-format limitation (like StreamProperties.unshrunkGas or
# Capex $/ft): there is no CSV column for it, so it cannot be round-tripped from
# a CSV cell. On the inverse pass we reconstruct it as the constant 'co2e'
# whenever at least one carbon species row exists (see from_row_dicts). If a
# source model's carbonExpenses has ONLY this scalar (no species leaves, so no
# CSV rows are emitted at all), to_row_dicts warns that the block is dropped.
_CARBON_CATEGORY_API = 'category'
_CARBON_CATEGORY_CSV = 'co2e'

_WATER_KEY_CSV = 'water'

# Row value key (API alias) -> CSV 'Unit' column value. dollarPerMmbtu is a gas
# variable expense (Criteria='flat', across g&p/opc/trn/mkt/other subcats) and
# fixedExpensePerWell is the per-well variant of fixedExpense on fixedExpenses slots
# (on monthlyWellCost, Criteria='dates').
_VALUE_UNIT = [
    ('dollarPerBbl', '$/bbl'),
    ('dollarPerMcf', '$/mcf'),
    ('dollarPerMmbtu', '$/mmbtu'),
    ('fixedExpense', '$/month'),
    ('fixedExpensePerWell', '$/well/month'),
    ('carbonExpense', '$/MT'),
]
_UNIT_TO_KEY = {u: k for k, u in _VALUE_UNIT}

# CSV Key values for the $/bbl-denominated leaves (oil/ngl/drip-cond variable
# expenses, water disposal) -- see `_value_unit`'s no-value fallback below.
_NO_VALUE_BBL_KEYS = {'oil', 'ngl', 'drip cond', _WATER_KEY_CSV}

# Inverse-only canonical offsetToFpd reconstructed for a CSV Period of 'ecl'. This is
# NOT a value round-tripped from the real API -- see the terminal-row rule below.
# Documented non-exact: a source leaf whose real terminal offsetToFpd differs from this
# constant will not reproduce its original offsetToFpd through a CSV round trip; it
# comes back as this constant.
_FPD_ECL_CANONICAL_OFFSET = 1200


class ExpenseApiRow(BaseModel):
    """One `rows[]` element within an Expenses leaf (variableExpenses/fixedExpenses/
    carbonExpenses/waterDisposal). A real API row carries exactly one of
    `entireWellLife` (flat criteria), `offsetToFpd` (fpd criteria), or `dates` (dated
    criteria -- CSV Criteria 'dates', Period a literal calendar date, e.g.
    fixedExpenses/waterDisposal rows with `{'dates': '2000-01-01', ...}`), and
    (usually) exactly one of `dollarPerBbl`/`dollarPerMcf`/`dollarPerMmbtu`/
    `fixedExpense`/`fixedExpensePerWell`/`carbonExpense`. Exception: a $/bbl-denominated
    leaf (oil/ngl/drip-cond variable expenses, water disposal) can carry a row with
    NONE of those value keys at all -- CC's real Expenses.csv still renders it as Value
    '0' Unit '$/bbl', so `_value_unit` falls back to that reading for these specific
    Keys rather than raising. See `_NO_VALUE_BBL_KEYS`.

    Terminal-row 'ecl' rule (CSV Period column, forward direction only -- NOT a field
    on this model): within a single leaf's `rows` list, the CSV renders the LAST row's
    fpd Period as `'ecl'` (economic limit) regardless of its actual `offsetToFpd`
    value. Earlier (non-terminal) fpd rows in the same leaf render their literal month
    offset. A leaf whose only fpd row is terminal (the common case) renders that single
    row as 'ecl'. See `_criteria` for the position-based implementation and
    `_FPD_ECL_CANONICAL_OFFSET` for the (documented non-exact) inverse reconstruction.
    This rule is specific to `offsetToFpd`/'fpd' rows -- 'dates' rows never render 'ecl'
    regardless of position within the leaf.
    """

    model_config = ConfigDict(populate_by_name=True)

    entire_well_life: Annotated[Optional[str], Field(alias='entireWellLife')] = None
    offset_to_fpd: Annotated[Optional[int], Field(alias='offsetToFpd')] = None
    dates: Optional[str] = None
    dollar_per_bbl: Annotated[Optional[Union[int, float]], Field(alias='dollarPerBbl')] = None
    dollar_per_mcf: Annotated[Optional[Union[int, float]], Field(alias='dollarPerMcf')] = None
    dollar_per_mmbtu: Annotated[Optional[Union[int, float]], Field(alias='dollarPerMmbtu')] = None
    fixed_expense: Annotated[Optional[Union[int, float]], Field(alias='fixedExpense')] = None
    fixed_expense_per_well: Annotated[Optional[Union[int, float]], Field(alias='fixedExpensePerWell')] = None
    carbon_expense: Annotated[Optional[Union[int, float]], Field(alias='carbonExpense')] = None


class ExpenseLeaf(BaseModel):
    """Leaf settings shared by every expense group (variable/fixed/carbon/water).

    Every key EXCEPT `stopAtEconLimit`/`expenseBeforeFpd` (fixed-only) is always
    present on a real API leaf -- including `cap`/`description`/etc when their value is
    null. `from_row_dicts` therefore reconstructs those fields unconditionally (never
    omits them just because the CSV cell was blank), via an explicit `exclude={...}` set
    on `model_dump` rather than a blanket `exclude_none=True` -- see `_build_leaf`.
    `Optional` typing here exists only because a CSV cell can be blank (-> None), not
    because the key itself is ever genuinely absent.

    `rateType`/`rowsCalculationMethod` are parsed (so `model_validate` never chokes on
    a real leaf) but deliberately never read by `to_row_dicts` and never set by
    `from_row_dicts`: CC's real Expenses CSV renders 'Rate Type'/'Rate Rows Calculation
    Method' BLANK unconditionally, even though the API leaf carries real values (e.g.
    'gross_well_head'/'non_monotonic') -- a documented, non-round-trippable CSV-format
    limitation, exactly like StreamProperties. These two are always excluded from the
    dumped API dict.

    `stopAtEconLimit`/`expenseBeforeFpd` only exist on real fixedExpenses leaves (never
    on variable/carbon/water leaves) -- `from_row_dicts` excludes them from the dump for
    non-fixed leaves.
    """

    model_config = ConfigDict(populate_by_name=True)

    shrinkage_condition: Annotated[Optional[str], Field(alias='shrinkageCondition')] = None
    description: Optional[str] = None
    escalation_model: Annotated[Optional[str], Field(alias='escalationModel')] = None
    calculation: Optional[str] = None
    affect_econ_limit: Annotated[Optional[bool], Field(alias='affectEconLimit')] = None
    deduct_before_severance_tax: Annotated[Optional[bool], Field(alias='deductBeforeSeveranceTax')] = None
    deduct_before_ad_val_tax: Annotated[Optional[bool], Field(alias='deductBeforeAdValTax')] = None
    cap: Optional[Union[int, float]] = None
    deal_terms: Annotated[Optional[Union[int, float]], Field(alias='dealTerms')] = None
    rate_type: Annotated[Optional[str], Field(alias='rateType')] = None
    rows_calculation_method: Annotated[Optional[str], Field(alias='rowsCalculationMethod')] = None
    stop_at_econ_limit: Annotated[Optional[bool], Field(alias='stopAtEconLimit')] = None
    expense_before_fpd: Annotated[Optional[bool], Field(alias='expenseBeforeFpd')] = None
    rows: List[ExpenseApiRow] = Field(default_factory=list)

    @field_validator('cap', mode='before')
    @classmethod
    def _blank_cap_to_none(cls, v: Any) -> Any:
        # Some real API leaves carry cap as '' (empty string) rather than null when
        # unset -- normalize both "no cap" sentinels to None so model_validate never
        # raises on a real leaf.
        return None if v == '' else v


class ExpenseTarget(NamedTuple):
    """Where a CSV (Key, Category) group's leaf belongs in the reconstructed API model,
    as resolved by `_target`."""

    kind: str  # 'variable' | 'fixed' | 'carbon' | 'water'
    slot_a: Optional[str]  # variable: API phase; fixed: slot; carbon: species; water: None
    slot_b: Optional[str]  # variable: API subcat; else None


def _unwrap_variable_leaf(node: Dict[str, Any]) -> Dict[str, Any]:
    """Unwrap the boe/totalFluid double-nesting (see `_DOUBLE_NESTED_PHASES` /
    `_LEAF_MARKER_KEYS`): a real leaf always carries at least one leaf-marker key.
    When `node` carries NONE of them but is a single-entry dict whose lone value
    is itself a dict, `node` is the extra wrapper layer produced by CC's API for
    these two phases -- descend into that nested dict, which is the real leaf.
    Detection is structural (not gated on the subcat name 'processing') so it
    generalizes if the API ever double-nests a different subcat the same way;
    normal single-nested leaves (every other phase) are returned unchanged."""
    if any(k in node for k in _LEAF_MARKER_KEYS):
        return node
    if len(node) == 1:
        (inner,) = node.values()
        if isinstance(inner, dict):
            return inner
    return node


def _settings_columns(leaf: ExpenseLeaf, fixed: bool) -> Dict[str, str]:
    out: Dict[str, str] = {
        'Description': '' if leaf.description is None else leaf.description,
        'Calculation': '' if leaf.calculation is None else leaf.calculation,
        'Escalation': escalation_to_csv(leaf.escalation_model, title=False),
        'Shrinkage Condition': '' if leaf.shrinkage_condition is None else leaf.shrinkage_condition,
        # 'Rate Type'/'Rate Rows Calculation Method' are ALWAYS blank, even though the
        # API leaf carries real rateType/rowsCalculationMethod values. Not
        # round-trippable -- see ExpenseLeaf docstring.
        'Rate Type': '',
        'Rate Rows Calculation Method': '',
        # yes/no (not yes/blank): these boolean toggles render 'no' for False, not ''.
        # 'Expense bef FPD' = 'no' is real data; yes_blank silently corrupted the False
        # case and broke the round-trip (final-review M5). 'Affect Econ Limit' and
        # 'Stop at Econ Limit' are the same kind of real boolean toggle as the yes/no
        # 'Deduct bef *' columns, so they render the same way.
        'Affect Econ Limit': formats.yes_no(leaf.affect_econ_limit),
        'Deduct bef Sev Tax': formats.yes_no(leaf.deduct_before_severance_tax),
        'Deduct bef Ad Val Tax': formats.yes_no(leaf.deduct_before_ad_val_tax),
        'Cap': '' if leaf.cap is None else num_to_csv(leaf.cap),
        'Paying WI / Earning WI': '' if leaf.deal_terms is None else num_to_csv_float(leaf.deal_terms),
    }
    if fixed:
        out['Stop at Econ Limit'] = formats.yes_no(leaf.stop_at_econ_limit)
        out['Expense bef FPD'] = formats.yes_no(leaf.expense_before_fpd)
    else:
        out['Stop at Econ Limit'] = ''
        out['Expense bef FPD'] = ''
    return out


def _value_unit(r: ExpenseApiRow, key_csv: str) -> Tuple[Any, str]:
    if r.dollar_per_bbl is not None:
        return r.dollar_per_bbl, '$/bbl'
    if r.dollar_per_mcf is not None:
        return r.dollar_per_mcf, '$/mcf'
    if r.dollar_per_mmbtu is not None:
        return r.dollar_per_mmbtu, '$/mmbtu'
    if r.fixed_expense is not None:
        return r.fixed_expense, '$/month'
    if r.fixed_expense_per_well is not None:
        return r.fixed_expense_per_well, '$/well/month'
    if r.carbon_expense is not None:
        return r.carbon_expense, '$/MT'
    if key_csv in _NO_VALUE_BBL_KEYS:
        # A real API row for a $/bbl-denominated leaf can omit every value key
        # entirely -- CC's real Expenses.csv still renders these rows as Value '0'
        # Unit '$/bbl' rather than blank. Only these bbl-denominated Keys behave this
        # way; gas/fixed/carbon rows always carry an explicit value key (even when the
        # value is 0), so we do not guess a fallback unit for those -- they still raise
        # below. Round-trip note: from_row_dicts reconstructs this '0'/'$/bbl' cell the
        # same way as any $/bbl row -- i.e. as dollarPerBbl=0, not a value-key-less row
        # -- which is CSV-idempotent and matches CC's own export.
        return 0, '$/bbl'
    raise NotImplementedError(f'Unknown expense row value: {r!r}')


def _criteria(r: ExpenseApiRow, *, is_terminal: bool) -> Tuple[str, str]:
    if r.entire_well_life is not None:
        formats.check_entire_well_life(r.entire_well_life)
        return 'flat', ''
    if r.offset_to_fpd is not None:
        period = 'ecl' if is_terminal else str(r.offset_to_fpd)
        return 'fpd', period
    if r.dates is not None:
        return 'dates', formats.to_csv_date(r.dates)
    raise NotImplementedError(f'Unknown expense row criteria: {r!r}')


def _target(key_csv: str, category_csv: str) -> ExpenseTarget:
    if key_csv in _PHASE_FROM_CSV:
        if category_csv not in _SUBCAT_FROM_CSV:
            raise NotImplementedError(f'Unknown expense Category: {category_csv}')
        return ExpenseTarget('variable', _PHASE_FROM_CSV[key_csv], _SUBCAT_FROM_CSV[category_csv])
    if key_csv == _FIXED_KEY_CSV:
        if category_csv not in _FIXED_SLOT_FROM_CSV:
            raise NotImplementedError(f'Unknown fixed expense Category: {category_csv}')
        return ExpenseTarget('fixed', _FIXED_SLOT_FROM_CSV[category_csv], None)
    if key_csv in _CARBON_SPECIES_FROM_CSV:
        return ExpenseTarget('carbon', _CARBON_SPECIES_FROM_CSV[key_csv], None)
    if key_csv == _WATER_KEY_CSV:
        return ExpenseTarget('water', None, None)
    raise NotImplementedError(f'Unknown expense Key: {key_csv}')


def _build_leaf(members: List[Dict[str, str]], fixed: bool) -> Dict[str, Any]:
    first = members[0]
    kwargs: Dict[str, Any] = {}

    description = first.get('Description') or ''
    kwargs['description'] = description or None
    calculation = first.get('Calculation') or ''
    kwargs['calculation'] = calculation or None
    kwargs['escalationModel'] = escalation_from_csv(first.get('Escalation', ''), title=False)
    shrinkage = first.get('Shrinkage Condition') or ''
    kwargs['shrinkageCondition'] = shrinkage or None
    # 'Rate Type'/'Rate Rows Calculation Method' are always blank in the CSV (see
    # ExpenseLeaf docstring) -- never reconstructed; rateType/rowsCalculationMethod
    # are excluded from the dumped API dict below regardless of value.
    kwargs['affectEconLimit'] = formats.parse_yes_blank(first.get('Affect Econ Limit', ''))
    kwargs['deductBeforeSeveranceTax'] = formats.parse_yes_blank(first.get('Deduct bef Sev Tax', ''))
    kwargs['deductBeforeAdValTax'] = formats.parse_yes_blank(first.get('Deduct bef Ad Val Tax', ''))
    cap_cell = first.get('Cap') or ''
    kwargs['cap'] = None if not cap_cell else csv_to_num(cap_cell)
    deal_terms_cell = first.get('Paying WI / Earning WI') or ''
    kwargs['dealTerms'] = None if not deal_terms_cell else csv_to_num(deal_terms_cell)
    if fixed:
        kwargs['stopAtEconLimit'] = formats.parse_yes_blank(first.get('Stop at Econ Limit', ''))
        kwargs['expenseBeforeFpd'] = formats.parse_yes_blank(first.get('Expense bef FPD', ''))

    rows = [_row_from_csv(m) for m in members]
    kwargs['rows'] = rows

    leaf = ExpenseLeaf.model_validate(kwargs)
    # Real API leaves always carry description/calculation/escalationModel/
    # shrinkageCondition/cap/dealTerms/affectEconLimit/deductBefore* EVEN WHEN the
    # value is null/false -- so, unlike rateType/rowsCalculationMethod (never
    # reconstructed) and stopAtEconLimit/expenseBeforeFpd (only exist on fixed leaves),
    # these fields must NOT be dropped just because their reconstructed value happens to
    # be None. Hence `exclude=` (a fixed field-name set) rather than a blanket
    # `exclude_none=True` on the leaf itself.
    exclude_fields: Set[str] = {'rate_type', 'rows_calculation_method'}
    if not fixed:
        exclude_fields |= {'stop_at_econ_limit', 'expense_before_fpd'}
    dumped = leaf.model_dump(by_alias=True, exclude=exclude_fields)
    # `rows` was already assembled above as clean, exclude-None alias dicts (each
    # row carries exactly its 2 real keys -- one criteria key, one value key). The
    # leaf-level `exclude` set only governs the leaf's OWN fields, not the nested
    # row dicts, so restore the pre-built list rather than pydantic's default
    # (all-keys-present, None-included) re-dump of leaf.rows.
    dumped['rows'] = rows
    return dumped


def _row_from_csv(m: Dict[str, str]) -> Dict[str, Any]:
    row_dict: Dict[str, Any] = {}
    criteria = m['Criteria']
    if criteria == 'flat':
        row_dict['entireWellLife'] = formats.ENTIRE_WELL_LIFE_MARKER
    elif criteria == 'fpd':
        period = m['Period']
        # 'ecl' identifies a leaf's TERMINAL fpd row (see ExpenseApiRow docstring)
        # -- the real original offsetToFpd is not recoverable from that string
        # alone, so we reconstruct a canonical placeholder (documented non-exact).
        row_dict['offsetToFpd'] = _FPD_ECL_CANONICAL_OFFSET if period == 'ecl' else int(period)
    elif criteria == 'dates':
        row_dict['dates'] = formats.from_csv_date(m['Period'])
    else:
        raise NotImplementedError(f'Unknown expense Criteria: {criteria}')
    unit = m['Unit']
    if unit not in _UNIT_TO_KEY:
        raise NotImplementedError(f'Unknown expense Unit: {unit}')
    row_dict[_UNIT_TO_KEY[unit]] = csv_to_num(m['Value'])
    return ExpenseApiRow.model_validate(row_dict).model_dump(by_alias=True, exclude_none=True)


class ExpensesMapper(EconModelMapper):
    econ_model_type = 'Expenses'
    columns = COLUMNS['Expenses']

    def to_row_dicts(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        common = common_columns(model, context)
        rows: List[Dict[str, str]] = []

        for phase, subcats in (model.get('variableExpenses') or {}).items():
            if phase not in _PHASE_TO_CSV:
                raise NotImplementedError(f'Unknown expense phase: {phase}')
            if not isinstance(subcats, dict):
                continue
            for subcat, leaf in subcats.items():
                if subcat not in _SUBCAT_TO_CSV:
                    raise NotImplementedError(f'Unknown expense subcat: {subcat}')
                if isinstance(leaf, dict):
                    leaf = _unwrap_variable_leaf(leaf)
                rows.extend(self._leaf_rows(common, leaf, _PHASE_TO_CSV[phase], _SUBCAT_TO_CSV[subcat], fixed=False))

        for slot, leaf in (model.get('fixedExpenses') or {}).items():
            if slot not in _FIXED_SLOT_TO_CSV:
                raise NotImplementedError(f'Unknown fixed expense slot: {slot}')
            rows.extend(self._leaf_rows(common, leaf, _FIXED_KEY_CSV, _FIXED_SLOT_TO_CSV[slot], fixed=True))

        # Water is emitted BEFORE carbon: CC's CSV row order is
        # variable -> fixed -> water -> carbon, not variable -> fixed -> carbon -> water.
        water = model.get('waterDisposal')
        if water:
            rows.extend(self._leaf_rows(common, water, _WATER_KEY_CSV, '', fixed=False))

        carbon_expenses = model.get('carbonExpenses') or {}
        carbon_species_leaves = {k: v for k, v in carbon_expenses.items() if isinstance(v, dict)}
        for species, leaf in carbon_species_leaves.items():
            if species not in _CARBON_SPECIES_TO_CSV:
                raise NotImplementedError(f'Unknown carbon expense species: {species}')
            rows.extend(
                self._leaf_rows(common, leaf, _CARBON_SPECIES_TO_CSV[species], _CARBON_CATEGORY_CSV, fixed=False)
            )
        if _CARBON_CATEGORY_API in carbon_expenses and not carbon_species_leaves:
            # The scalar 'category' key is present but there are no species leaves to
            # emit rows for, so this carbonExpenses block has no CSV representation at
            # all -- it will not round-trip. Warn rather than silently dropping it.
            warnings.warn(
                "carbonExpenses has only the scalar 'category' key with no species rows; "
                'this block is not representable in the CSV and will be dropped.',
                stacklevel=2,
            )

        return rows

    def _leaf_rows(
        self, common: Dict[str, str], raw_leaf: Dict[str, Any], key_csv: str, category_csv: str, fixed: bool
    ) -> List[Dict[str, str]]:
        leaf = ExpenseLeaf.model_validate(raw_leaf)
        settings = _settings_columns(leaf, fixed)
        out: List[Dict[str, str]] = []
        last_index = len(leaf.rows) - 1
        for i, r in enumerate(leaf.rows):
            value, unit = _value_unit(r, key_csv)
            criteria, period = _criteria(r, is_terminal=(i == last_index))
            row = dict(common)
            row.update(settings)
            row.update(
                {
                    'Key': key_csv,
                    'Category': category_csv,
                    'Criteria': criteria,
                    'Value': num_to_csv_float(value),
                    'Period': period,
                    'Unit': unit,
                }
            )
            out.append({c: row.get(c, '') for c in self.columns})
        return out

    def from_row_dicts(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        groups: Dict[Tuple[str, str], List[Dict[str, str]]] = {}
        order: List[Tuple[str, str]] = []
        name, unique = model_identity(rows)
        for row in rows:
            group_key = (row['Key'], row['Category'])
            if group_key not in groups:
                groups[group_key] = []
                order.append(group_key)
            groups[group_key].append(row)

        variable_expenses: Dict[str, Dict[str, Any]] = {}
        fixed_expenses: Dict[str, Any] = {}
        carbon_expenses: Dict[str, Any] = {}
        water_disposal: Optional[Dict[str, Any]] = None

        for key_csv, category_csv in order:
            members = groups[(key_csv, category_csv)]
            kind, slot_a, slot_b = _target(key_csv, category_csv)
            leaf = _build_leaf(members, fixed=(kind == 'fixed'))
            if kind == 'variable':
                assert slot_a is not None and slot_b is not None
                if slot_a in _DOUBLE_NESTED_PHASES:
                    # Re-create the real API's double-nested shape (see
                    # `_PHASE_TO_CSV` / `_unwrap_variable_leaf`): boe/totalFluid only
                    # ever use the 'processing' subcat, so slot_b == slot_b here, but
                    # this is written generically off slot_b (the actual subcat)
                    # rather than hard-coding 'processing'.
                    variable_expenses.setdefault(slot_a, {})[slot_b] = {slot_b: leaf}
                else:
                    variable_expenses.setdefault(slot_a, {})[slot_b] = leaf
            elif kind == 'fixed':
                assert slot_a is not None
                fixed_expenses[slot_a] = leaf
            elif kind == 'carbon':
                assert slot_a is not None
                carbon_expenses[_CARBON_CATEGORY_API] = _CARBON_CATEGORY_CSV
                carbon_expenses[slot_a] = leaf
            else:  # water
                water_disposal = leaf

        result: Dict[str, Any] = {'name': name, 'unique': unique}
        # Only reconstruct a top-level group if at least one CSV row belonged to it --
        # an empty {} would misrepresent a source model that never had the group at all.
        if variable_expenses:
            result['variableExpenses'] = variable_expenses
        if fixed_expenses:
            result['fixedExpenses'] = fixed_expenses
        if carbon_expenses:
            result['carbonExpenses'] = carbon_expenses
        if water_disposal is not None:
            result['waterDisposal'] = water_disposal
        return result
