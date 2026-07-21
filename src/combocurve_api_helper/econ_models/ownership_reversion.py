from typing import Annotated, Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .base import Context, common_columns, model_identity
from .csv_columns import COLUMNS
from .formats import csv_to_num, from_csv_date, num_to_csv, to_csv_date

# Real API `ownership` shape (verified live, project 'Sample Project A | AFE'):
# `{"initialOwnership": {...}, "firstReversion": null|{...}, "secondReversion": ...,
# ..., "twentiethReversion": ...}` -- ALL 20 reversion keys are always present on a real
# model, set to `null` when that tier is unused (verified: models with only 1 active
# reversion still carry `secondReversion` through `twentiethReversion` as explicit
# `null`, not omitted). The ordinal word IS both the API key prefix (`firstReversion`)
# and the CSV `Key` column value (`first`) -- verified against the real CSV export
# (examples/_zipwork/SampleExport_AFE/Ownership and Reversion.csv): `Key='initial'` for
# `initialOwnership`, `Key='first'` for `firstReversion`.
_REVERSION_ORDINALS = [
    'first',
    'second',
    'third',
    'fourth',
    'fifth',
    'sixth',
    'seventh',
    'eighth',
    'ninth',
    'tenth',
    'eleventh',
    'twelfth',
    'thirteenth',
    'fourteenth',
    'fifteenth',
    'sixteenth',
    'seventeenth',
    'eighteenth',
    'nineteenth',
    'twentieth',
]

_INITIAL_KEY_CSV = 'initial'
_INITIAL_KEY_API = 'initialOwnership'

# API `reversionType` -> CSV 'Reversion Type' column value.
#
# A live drift audit (2026-07-20, projects 'Sample Project A' [2754 models] +
# 'Sample Project A | AFE' [106 models]; the other two audited projects,
# 'Sample Project D | NonOp | MultiBasin' and 'Sample Project E | NonOp | Multi Basin', currently have
# zero OwnershipReversion models) found exactly three live `reversionType` values across
# 2860 real models: 'PayoutWithoutInvestment' (49 tiers), 'PayoutWithInvestment' (121
# tiers), 'Date' (10 tiers). ComboCurve's public schema docs
# (docs.api.combocurve.com/api/custom/econ-models/ownership-reversions/overview) list a
# larger enum (`Date`, `AsOf`, `WhCumOil`, `WhCumGas`, `WhCumBoe`, `Irr`,
# `PayoutWithInvestment`, `PayoutWithoutInvestment`, `UndiscRoi`) -- only the three above
# have ever been observed live, so only those three are mapped; anything else still
# raises NotImplementedError rather than guessing at its CSV rendering.
#
# 'PayoutWithoutInvestment' -> 'po' is VERIFIED against the real CSV export (all 3
# populated-reversion models in 'Sample Project A | AFE' use it -- 'Sample Reversion A w
# PO', 'Sample Well 2 - PO 100%', 'Sample Well 3 - PO 100%').
#
# 'Date' -> 'date' is VERIFIED indirectly: `examples/_zipwork/Sample Project D/Ownership and
# Reversion.csv` is a real export (matching 'Last Update' timestamps) whose numeric/WI/NRI
# cells were subsequently hand-edited into `@Header.[...]`/`@PCH.[...]` re-import formula
# references (a documented CC re-import workflow) for 3 rows with a real
# `reversionType == 'Date'` tier -- but the 'Reversion Type' cell on all 3 was left as the
# literal token `'date'`, not a formula, consistent with CC requiring this cell to be a
# recognized keyword on import rather than a free-form formula target.
#
# 'PayoutWithInvestment' -> 'poi' is UNVERIFIED (no real CSV row for this type was found
# in any local export, and the field list for `PayoutWithInvestment`/
# `PayoutWithoutInvestment` is otherwise IDENTICAL per the C# API client docs
# (csharp.devs.combocurve.com/docs/PayoutWithInvestment.html) -- the type name carries all
# the semantic difference). Picked to extend the existing 'po' ("payout") abbreviation
# convention with a distinct, round-trippable token; if a real export ever surfaces a
# different CSV token for this type, update this mapping (and the token below) to match.
_REVERSION_TYPE_TO_CSV = {
    'PayoutWithoutInvestment': 'po',
    'PayoutWithInvestment': 'poi',
    'Date': 'date',
}
_REVERSION_TYPE_FROM_CSV = {v: k for k, v in _REVERSION_TYPE_TO_CSV.items()}

# 'Reversion Tied To' display default -- used when `reversionTiedTo` is absent, or is the
# verified-live `{"type": "as_of"}` shape. 'Sample Reversion A w PO' firstReversion carries NO
# `reversionTiedTo` key at all (real absence, like ProductionTaxes' `deductSeveranceTax` on
# severance rows), while 'Sample Well 2 - PO 100%' and 'Sample Well 3 - PO 100%' carry it
# explicitly as `{"type": "as_of"}` -- yet all three render the identical CSV cell
# `"as of"`. This makes the absent-vs-explicit-'as_of' distinction UNRECOVERABLE from the
# CSV alone -- from_csv_rows always reconstructs the explicit `{"type": "as_of"}` form
# (documented residual: it cannot reproduce the exact-absent shape of 'Sample Reversion A w PO').
#
# A live drift audit additionally found a second real `reversionTiedTo` shape --
# `{"type": "date", "value": "<ISO date>"}` (122 of 2860 models: 121 `PayoutWithInvestment`
# tiers -- apparently always tied to a date -- plus 1 `Date`-type tier where the tied-to
# date differs from the tier's own `reversionValue` date). Unlike the as_of/absent case,
# this shape IS fully round-trippable: it renders as the formatted date itself (via
# `to_csv_date`/`from_csv_date`, matching the date-column convention used elsewhere in
# this package, e.g. `capex.py`), which is unambiguously distinguishable from the literal
# `"as of"` text and from a blank cell -- no CSV representation for this has been directly
# observed live (no real export in this repo contains a populated 'Reversion Tied To'
# cell), so the rendering is CC-consistent-but-unverified; if it disagrees with a future
# real export, adjust `_tied_to_to_csv`/`_tied_to_from_csv` below.
_REVERSION_TIED_TO_CSV_DEFAULT = 'as of'
_KNOWN_TIED_TO_TYPES = frozenset({'as_of', 'date'})

# 'Rev Basis WI %'/'Rev Basis NRI %' have NEVER been observed populated on any live model
# (all 26 models in 'Sample Project A | AFE', including all 3 with active reversion
# tiers, render these two columns blank -- both on the initial row and on reversion
# rows). No backing API field has been identified. to_csv_rows always emits '' for both;
# from_csv_rows raises if it ever sees either cell populated, rather than silently
# dropping real data.
_REV_BASIS_COLUMNS = ('Rev Basis WI %', 'Rev Basis NRI %')


class ReversionTiedTo(BaseModel):
    """`ownership.<n>Reversion.reversionTiedTo` -- verified live in two shapes:
    `{"type": "as_of"}` (no `value`) and `{"type": "date", "value": "<ISO date>"}`. The
    ComboCurve API client docs (csharp.devs.combocurve.com/docs/ReversionTiedTo.html)
    independently confirm a `Value` (nullable DateTime) field alongside `Type`, consistent
    with what live data shows: `value` is a plain ISO `"YYYY-MM-DD"` string, present only
    for `type == 'date'`.
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str
    value: Optional[str] = None


class InitialOwnershipData(BaseModel):
    """`ownership.initialOwnership` (verified live, project 'Sample Project A |
    AFE', model '8/8ths'): `{"workingInterest": 100, "netProfitInterestType": "expense",
    "netProfitInterest": 0, "netRevenueInterest": 75, "leaseNetRevenueInterest": 75,
    "oilNetRevenueInterest": null, "gasNetRevenueInterest": null,
    "nglNetRevenueInterest": null, "dripCondensateNetRevenueInterest": null}`.
    `netProfitInterestType` lives ONLY here -- reversion tiers carry their own
    `netProfitInterest` value but never a `netProfitInterestType` key (verified live);
    the CSV's 'NPI Type' column is therefore populated only on the 'initial' row.

    Every field here is ALWAYS present on a real API `initialOwnership` object --
    including the four phase-NRI fields when their value is null (verified live: '8/8ths',
    'Sample Reversion A w PO', 'Sample Well 2 - PO 100%' all carry
    `oilNetRevenueInterest`/etc explicitly as `null`, never omitted). `Optional` typing
    here exists only so a blank CSV cell can round-trip to `None`; `from_csv_rows` dumps
    with NO `exclude_none`, so a reconstructed `None` still emits its key (matching the
    real always-present shape) -- see `OwnershipReversionMapper._initial_from_csv`.
    """

    model_config = ConfigDict(populate_by_name=True)

    working_interest: Annotated[Union[int, float], Field(alias='workingInterest')]
    net_profit_interest_type: Annotated[Optional[str], Field(alias='netProfitInterestType')] = None
    net_profit_interest: Annotated[Optional[Union[int, float]], Field(alias='netProfitInterest')] = None
    net_revenue_interest: Annotated[Union[int, float], Field(alias='netRevenueInterest')]
    lease_net_revenue_interest: Annotated[Union[int, float], Field(alias='leaseNetRevenueInterest')]
    oil_net_revenue_interest: Annotated[Optional[Union[int, float]], Field(alias='oilNetRevenueInterest')] = None
    gas_net_revenue_interest: Annotated[Optional[Union[int, float]], Field(alias='gasNetRevenueInterest')] = None
    ngl_net_revenue_interest: Annotated[Optional[Union[int, float]], Field(alias='nglNetRevenueInterest')] = None
    drip_condensate_net_revenue_interest: Annotated[
        Optional[Union[int, float]], Field(alias='dripCondensateNetRevenueInterest')
    ] = None


class ReversionTierData(BaseModel):
    """One `ownership.<n>Reversion` element (verified live, project 'Sample Project A |
    AFE', model 'Sample Reversion A w PO'): `{"reversionType":
    "PayoutWithoutInvestment", "reversionValue": 12290000, "balance": "gross",
    "includeNetProfitInterest": "yes", "workingInterest": 0.177749, "netRevenueInterest":
    0.132697, "leaseNetRevenueInterest": 75.00140853, "netProfitInterest": 0,
    "oilNetRevenueInterest": null, "gasNetRevenueInterest": null,
    "nglNetRevenueInterest": null, "dripCondensateNetRevenueInterest": null}` (+
    optional `reversionTiedTo`, see `ReversionTiedTo`/`_REVERSION_TIED_TO_CSV_DEFAULT`).

    `includeNetProfitInterest` is a real API STRING ('yes'/'no'), not a bool -- verified
    live -- so it passes through to the CSV 'Include NPI' column unchanged, unlike the
    `formats.yes_no`-style bool columns elsewhere in this package.

    `reversionValue` is `Union[int, float, str]`: for `reversionType in
    ('PayoutWithoutInvestment', 'PayoutWithInvestment')` it is the numeric payout dollar
    threshold (verified live, e.g. `12290000`, `28588998.75`); for `reversionType ==
    'Date'` it is a plain ISO `"YYYY-MM-DD"` STRING (verified live, e.g. `"2023-03-01"`;
    ComboCurve's schema docs show the same field as a full ISO datetime
    `"2023-04-11T00:00:00.000Z"` -- `formats.to_csv_date`/`from_csv_date` (via
    `datetime.fromisoformat`) accept both forms transparently). Maps to the CSV
    'Reversion Value' column as a formatted `MM/DD/YYYY` date for `'Date'` tiers (same
    date-column convention as `capex.py`), else as a plain number.

    `balance`/`includeNetProfitInterest` are typed `Optional[str]` for pydantic
    permissiveness, but on real `'Date'`-type tiers (where neither concept applies) they
    are verified live to be present as the EMPTY STRING `""`, not `null` or absent (e.g.
    `{"reversionType": "Date", "reversionValue": "2023-03-01", "balance": "",
    "includeNetProfitInterest": "", ...}`) -- the same "always-present, sentinel-when-N/A"
    shape as the phase-NRI fields below, just with `""` as the sentinel instead of `null`.
    `from_csv_rows` therefore reconstructs a blank cell as `""` (not `None`) for both, so a
    real `'Date'` tier round-trips exactly.

    Every field EXCEPT `reversionTiedTo` is ALWAYS present on a real reversion-tier
    object, including the four phase-NRI fields when null (same always-present shape as
    `InitialOwnershipData`, see its docstring). `reversionTiedTo` is the one field that is
    genuinely, structurally absent sometimes -- see `_REVERSION_TIED_TO_CSV_DEFAULT` for
    the verified-live absent-vs-explicit-null case. `from_csv_rows` dumps every other
    field without `exclude_none` and handles `reversionTiedTo` separately -- see
    `OwnershipReversionMapper._reversion_from_csv`.
    """

    model_config = ConfigDict(populate_by_name=True)

    reversion_type: Annotated[str, Field(alias='reversionType')]
    reversion_value: Annotated[Union[int, float, str], Field(alias='reversionValue')]
    balance: Optional[str] = None
    include_net_profit_interest: Annotated[Optional[str], Field(alias='includeNetProfitInterest')] = None
    working_interest: Annotated[Union[int, float], Field(alias='workingInterest')]
    net_revenue_interest: Annotated[Union[int, float], Field(alias='netRevenueInterest')]
    lease_net_revenue_interest: Annotated[Union[int, float], Field(alias='leaseNetRevenueInterest')]
    net_profit_interest: Annotated[Optional[Union[int, float]], Field(alias='netProfitInterest')] = None
    oil_net_revenue_interest: Annotated[Optional[Union[int, float]], Field(alias='oilNetRevenueInterest')] = None
    gas_net_revenue_interest: Annotated[Optional[Union[int, float]], Field(alias='gasNetRevenueInterest')] = None
    ngl_net_revenue_interest: Annotated[Optional[Union[int, float]], Field(alias='nglNetRevenueInterest')] = None
    drip_condensate_net_revenue_interest: Annotated[
        Optional[Union[int, float]], Field(alias='dripCondensateNetRevenueInterest')
    ] = None
    reversion_tied_to: Annotated[Optional[ReversionTiedTo], Field(alias='reversionTiedTo')] = None


def _opt_num(value: Optional[Union[int, float]]) -> str:
    return '' if value is None else num_to_csv(value)


def _opt_renum(cell: Optional[str]) -> Optional[Union[int, float]]:
    cell = (cell or '').strip()
    return None if not cell else csv_to_num(cell)


def _reversion_value_to_csv(tier: ReversionTierData) -> str:
    """'Reversion Value' cell: a formatted date for `'Date'` tiers (verified live --
    `reversionValue` is an ISO date STRING for this type), else a plain number. The
    `isinstance` checks double as a fail-loud guard against a genuinely-unexpected
    type/value combination we have never seen live (e.g. a numeric 'Date' value).
    """
    if tier.reversion_type == 'Date':
        if not isinstance(tier.reversion_value, str):
            raise NotImplementedError(
                f"'Date' reversion expected a string reversionValue, got {tier.reversion_value!r}"
            )
        return to_csv_date(tier.reversion_value)
    if isinstance(tier.reversion_value, str):
        raise NotImplementedError(
            f'Reversion type {tier.reversion_type!r} got a string reversionValue (only verified live for '
            f"'Date'): {tier.reversion_value!r}"
        )
    return num_to_csv(tier.reversion_value)


def _reversion_value_from_csv(reversion_type_api: str, cell: str) -> Union[int, float, str]:
    """Inverse of `_reversion_value_to_csv`."""
    if reversion_type_api == 'Date':
        return from_csv_date(cell)
    return csv_to_num(cell)


def _tied_to_to_csv(tied_to: Optional[ReversionTiedTo]) -> str:
    """'Reversion Tied To' cell. See `_REVERSION_TIED_TO_CSV_DEFAULT` for the verified-live
    as_of/absent collapse and the CC-consistent-but-unverified date+value rendering.
    """
    if tied_to is None:
        return _REVERSION_TIED_TO_CSV_DEFAULT
    if tied_to.type not in _KNOWN_TIED_TO_TYPES:
        raise NotImplementedError(f'Unknown reversionTiedTo type: {tied_to.type!r}')
    if tied_to.type == 'date':
        if tied_to.value is None:
            raise NotImplementedError("reversionTiedTo type 'date' has only been observed live WITH a value")
        return to_csv_date(tied_to.value)
    # type == 'as_of': verified live to never carry a value.
    if tied_to.value is not None:
        raise NotImplementedError(f"Unexpected reversionTiedTo value on type 'as_of': {tied_to.value!r}")
    return _REVERSION_TIED_TO_CSV_DEFAULT


def _tied_to_from_csv(cell: str) -> Optional[ReversionTiedTo]:
    """Inverse of `_tied_to_to_csv`. A blank cell reconstructs to `None` (the documented
    absent-vs-explicit-as_of residual -- see `_REVERSION_TIED_TO_CSV_DEFAULT`); any cell
    that parses as `MM/DD/YYYY` reconstructs the fully-recoverable `date`+`value` shape;
    anything else that is not the literal `'as of'` default is a genuinely-unknown
    representation and raises rather than guessing.
    """
    cell = (cell or '').strip()
    if not cell:
        return None
    if cell == _REVERSION_TIED_TO_CSV_DEFAULT:
        return ReversionTiedTo(type='as_of')
    try:
        iso = from_csv_date(cell)
    except ValueError as exc:
        raise NotImplementedError(f'Unknown Reversion Tied To cell: {cell!r}') from exc
    return ReversionTiedTo(type='date', value=iso)


class OwnershipReversionMapper:
    """One CSV row per ownership tier: the 'initial' row (from `initialOwnership`) plus
    one row per POPULATED reversion tier (`firstReversion`..`twentiethReversion`, in
    ordinal order, skipping `null` tiers). See module docstring-level comments above for
    the live-verified ground truth this is built from.
    """

    econ_model_type = 'OwnershipReversion'
    columns = COLUMNS['OwnershipReversion']

    def to_csv_rows(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        common = common_columns(model, context)
        ownership = model.get('ownership') or {}

        initial = InitialOwnershipData.model_validate(ownership.get(_INITIAL_KEY_API) or {})
        rows: List[Dict[str, str]] = [self._initial_row(common, initial)]

        for ordinal in _REVERSION_ORDINALS:
            raw = ownership.get(f'{ordinal}Reversion')
            if raw is None:
                continue
            tier = ReversionTierData.model_validate(raw)
            rows.append(self._reversion_row(common, ordinal, tier))
        return rows

    def _initial_row(self, common: Dict[str, str], initial: InitialOwnershipData) -> Dict[str, str]:
        row = dict(common)
        row.update(
            {
                'Key': _INITIAL_KEY_CSV,
                'Reversion Type': '',
                'Reversion Value': '',
                'WI %': num_to_csv(initial.working_interest),
                'NRI %': num_to_csv(initial.net_revenue_interest),
                'Lease NRI %': num_to_csv(initial.lease_net_revenue_interest),
                'Reversion Tied To': '',
                'Balance': '',
                'Include NPI': '',
                'NPI Type': initial.net_profit_interest_type or '',
                'NPI %': _opt_num(initial.net_profit_interest),
                'Oil NRI %': _opt_num(initial.oil_net_revenue_interest),
                'Gas NRI %': _opt_num(initial.gas_net_revenue_interest),
                'NGL NRI %': _opt_num(initial.ngl_net_revenue_interest),
                'Drip Cond. NRI %': _opt_num(initial.drip_condensate_net_revenue_interest),
                'Rev Basis WI %': '',
                'Rev Basis NRI %': '',
            }
        )
        return {c: row.get(c, '') for c in self.columns}

    def _reversion_row(self, common: Dict[str, str], ordinal: str, tier: ReversionTierData) -> Dict[str, str]:
        if tier.reversion_type not in _REVERSION_TYPE_TO_CSV:
            raise NotImplementedError(f'Unknown ownership reversion type: {tier.reversion_type!r}')
        tied_to_csv = _tied_to_to_csv(tier.reversion_tied_to)

        row = dict(common)
        row.update(
            {
                'Key': ordinal,
                'Reversion Type': _REVERSION_TYPE_TO_CSV[tier.reversion_type],
                'Reversion Value': _reversion_value_to_csv(tier),
                'WI %': num_to_csv(tier.working_interest),
                'NRI %': num_to_csv(tier.net_revenue_interest),
                'Lease NRI %': num_to_csv(tier.lease_net_revenue_interest),
                'Reversion Tied To': tied_to_csv,
                'Balance': tier.balance or '',
                'Include NPI': tier.include_net_profit_interest or '',
                'NPI Type': '',
                'NPI %': _opt_num(tier.net_profit_interest),
                'Oil NRI %': _opt_num(tier.oil_net_revenue_interest),
                'Gas NRI %': _opt_num(tier.gas_net_revenue_interest),
                'NGL NRI %': _opt_num(tier.ngl_net_revenue_interest),
                'Drip Cond. NRI %': _opt_num(tier.drip_condensate_net_revenue_interest),
                'Rev Basis WI %': '',
                'Rev Basis NRI %': '',
            }
        )
        return {c: row.get(c, '') for c in self.columns}

    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        name, unique = model_identity(rows)
        by_key: Dict[str, Dict[str, str]] = {}
        for row in rows:
            for col in _REV_BASIS_COLUMNS:
                if (row.get(col) or '').strip():
                    raise NotImplementedError(
                        f'{col!r} has no known API mapping (never observed populated live), but got {row.get(col)!r}'
                    )
            by_key[row['Key']] = row

        if _INITIAL_KEY_CSV not in by_key:
            raise NotImplementedError("OwnershipReversion CSV rows missing required Key='initial' row")

        ownership: Dict[str, Any] = {_INITIAL_KEY_API: self._initial_from_csv(by_key[_INITIAL_KEY_CSV])}
        for ordinal in _REVERSION_ORDINALS:
            api_key = f'{ordinal}Reversion'
            if ordinal not in by_key:
                ownership[api_key] = None
                continue
            ownership[api_key] = self._reversion_from_csv(by_key[ordinal])

        return {'name': name, 'unique': unique, 'ownership': ownership}

    @staticmethod
    def _initial_from_csv(row: Dict[str, str]) -> Dict[str, Any]:
        data = InitialOwnershipData(
            working_interest=csv_to_num(row['WI %']),
            net_profit_interest_type=row.get('NPI Type') or None,
            net_profit_interest=_opt_renum(row.get('NPI %')),
            net_revenue_interest=csv_to_num(row['NRI %']),
            lease_net_revenue_interest=csv_to_num(row['Lease NRI %']),
            oil_net_revenue_interest=_opt_renum(row.get('Oil NRI %')),
            gas_net_revenue_interest=_opt_renum(row.get('Gas NRI %')),
            ngl_net_revenue_interest=_opt_renum(row.get('NGL NRI %')),
            drip_condensate_net_revenue_interest=_opt_renum(row.get('Drip Cond. NRI %')),
        )
        # NO exclude_none: every initialOwnership field is always present live, even when
        # null (see InitialOwnershipData docstring) -- exclude_none would wrongly drop a
        # genuinely-null phase-NRI key instead of reproducing it as `null`.
        return data.model_dump(by_alias=True)

    @staticmethod
    def _reversion_from_csv(row: Dict[str, str]) -> Dict[str, Any]:
        reversion_type_csv = row.get('Reversion Type') or ''
        if reversion_type_csv not in _REVERSION_TYPE_FROM_CSV:
            raise NotImplementedError(f'Unknown ownership Reversion Type: {reversion_type_csv!r}')
        reversion_type_api = _REVERSION_TYPE_FROM_CSV[reversion_type_csv]

        # See `_tied_to_from_csv`/`_REVERSION_TIED_TO_CSV_DEFAULT`: the CSV cannot
        # distinguish an absent `reversionTiedTo` key from an explicit `{"type": "as_of"}`
        # (documented residual, reconstructed as the explicit form); a formatted date cell
        # reconstructs the fully-recoverable `{"type": "date", "value": ...}` shape.
        reversion_tied_to = _tied_to_from_csv(row.get('Reversion Tied To', ''))

        data = ReversionTierData(
            reversion_type=reversion_type_api,
            reversion_value=_reversion_value_from_csv(reversion_type_api, row['Reversion Value']),
            # Verified live: on real 'Date'-type tiers (where neither concept applies),
            # `balance`/`includeNetProfitInterest` are present as `""`, not absent/null --
            # see ReversionTierData docstring. A blank cell therefore reconstructs to `''`,
            # not `None`, so that shape round-trips exactly.
            balance=row.get('Balance', ''),
            include_net_profit_interest=row.get('Include NPI', ''),
            working_interest=csv_to_num(row['WI %']),
            net_revenue_interest=csv_to_num(row['NRI %']),
            lease_net_revenue_interest=csv_to_num(row['Lease NRI %']),
            net_profit_interest=_opt_renum(row.get('NPI %')),
            oil_net_revenue_interest=_opt_renum(row.get('Oil NRI %')),
            gas_net_revenue_interest=_opt_renum(row.get('Gas NRI %')),
            ngl_net_revenue_interest=_opt_renum(row.get('NGL NRI %')),
            drip_condensate_net_revenue_interest=_opt_renum(row.get('Drip Cond. NRI %')),
            reversion_tied_to=reversion_tied_to,
        )
        # `reversion_tied_to` is the one field that is genuinely, structurally absent on
        # some real tiers (see ReversionTierData docstring) -- exclude it from the blanket
        # dump and add it back only when present, so a `None` here reproduces a real KEY
        # ABSENCE rather than an explicit `"reversionTiedTo": null`. Every other field
        # dumps unconditionally (no exclude_none) to reproduce the always-present shape.
        dumped = data.model_dump(by_alias=True, exclude={'reversion_tied_to'})
        if data.reversion_tied_to is not None:
            # exclude_none here (not on the outer dump) drops `value` when unset -- e.g.
            # `{"type": "as_of"}` -- rather than emitting an explicit `"value": null` that
            # was never present live; `type` is required (never `None`) so it always
            # survives.
            dumped['reversionTiedTo'] = data.reversion_tied_to.model_dump(by_alias=True, exclude_none=True)
        return dumped
