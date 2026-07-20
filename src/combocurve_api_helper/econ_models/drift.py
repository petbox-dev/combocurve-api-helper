"""Drift detection for the econ-model CSV mappers.

CC owns the API payload shape; we do not. When CC adds a field, a category, a unit, or a
criterion we have never seen, the mappers either raise (good -- it surfaces) or silently
skip it (bad -- the mappers navigate the nested payload by hand with plain ``dict`` access
and validate leaf rows with pydantic ``extra='ignore'``, so an unrecognized key is
dropped without a trace). This module makes both cases observable so a change gets
triaged instead of silently mis-mapped or lost:

* ``value_drift`` -- runs the forward mapper and reports any failure (unknown category /
  unit / criteria / enum / ``entireWellLife`` marker, or a pydantic validation error).
* ``key_drift`` -- compares every key in a payload against a committed per-type baseline
  of keys CC was observed to emit; anything outside the baseline is a key we do not
  handle.
* ``roundtrip_drift`` -- checks CSV idempotency (``to_csv_rows`` -> ``from_csv_rows`` ->
  ``to_csv_rows`` reproduces the same CSV). A divergence means the inverse silently lost or
  altered information the forward path emitted -- a class ``value_drift`` (forward-only)
  cannot see.

``_BASELINE_KEYS`` is a snapshot sampled from real projects (see the module-level date);
every key in it is either consumed by a mapper or a documented limitation. When CC starts
emitting a new key and you teach a mapper to handle it, regenerate/extend the baseline
with ``scripts/audit_econ_model_drift.py --emit-baseline``.

This module has NO network dependency -- it audits already-fetched model dicts, so its
logic is unit-tested. ``scripts/audit_econ_model_drift.py`` is the live-API runner.
"""

from typing import Any, Dict, FrozenSet, List, NamedTuple, Optional, Sequence, Set

from . import get_mapper

# Columns the inverse cannot reconstruct from CSV param cells (context/timestamp supplied
# out-of-band via `Context`), so they are excluded from the round-trip comparison -- the same
# set the forward-fidelity harness excludes.
_NON_ROUNDTRIP_COLUMNS: FrozenSet[str] = frozenset(
    {'Model Id', 'Created At', 'Project Name', 'Last Update', 'Embedded Lookup Table'}
)

# Present on every econ model regardless of type; not type-specific parameters, so they
# never count as drift.
ENVELOPE_KEYS: FrozenSet[str] = frozenset(
    {
        'id',
        'copiedFrom',
        'name',
        'unique',
        'createdBy',
        'lastUpdatedBy',
        'createdAt',
        'updatedAt',
        'econModelType',
        'project',
        'scenario',
        'well',
        'wells',
        'tags',
        'schemaVersion',
    }
)

# Baseline: every key CC was observed to emit in real payloads (sampled 2026-07-20 across
# projects Sample Project A, Sample Project A | AFE, Sample Project D | NonOp | MultiBasin, Sample Project E | NonOp | Multi Basin). Every key here is either consumed by a
# mapper or a documented CSV/API limitation. A payload key outside this set (and outside
# ENVELOPE_KEYS) is drift -- CC emitted something the mappers were not written against.
_BASELINE_KEYS: Dict[str, FrozenSet[str]] = {
    'StreamProperties': frozenset(
        {
            'btuContent',
            'companyCustomStreams',
            'dates',
            'dripCondensate',
            'entireWellLife',
            'gas',
            'gasFlare',
            'gasLoss',
            'lossFlare',
            'ngl',
            'oil',
            'oilLoss',
            'pctRemaining',
            'rateType',
            'rows',
            'rowsCalculationMethod',
            'shrinkage',
            'shrunkGas',
            'unshrunkGas',
            'yield',
            'yields',
        }
    ),
    'Differentials': frozenset(
        {
            'dates',
            'differentials',
            'dollarPerBbl',
            'dollarPerMcf',
            'dollarPerMmbtu',
            'dripCondensate',
            'entireWellLife',
            'escalationModel',
            'firstDifferential',
            'gas',
            'ngl',
            'oil',
            'pctOfBasePrice',
            'rows',
            'secondDifferential',
            'thirdDifferential',
        }
    ),
    'ProductionTaxes': frozenset(
        {
            'calculation',
            'category',
            'criteria',
            'data',
            'deductSeveranceTax',
            'escalation',
            'key',
            'period',
            'rateRowsCalculationMethod',
            'rateType',
            'rows',
            'shrinkageCondition',
            'state',
            'unit',
            'value',
        }
    ),
    'Expenses': frozenset(
        {
            'affectEconLimit',
            'boe',
            'calculation',
            'cap',
            'carbonExpense',
            'carbonExpenses',
            'category',
            'ch4',
            'co2',
            'co2E',
            'dates',
            'dealTerms',
            'deductBeforeAdValTax',
            'deductBeforeSeveranceTax',
            'description',
            'dollarPerBbl',
            'dollarPerMcf',
            'dollarPerMmbtu',
            'dripCondensate',
            'entireWellLife',
            'escalationModel',
            'expenseBeforeFpd',
            'fixedExpense',
            'fixedExpensePerWell',
            'fixedExpenses',
            'gas',
            'gathering',
            'marketing',
            'monthlyWellCost',
            'n2O',
            'ngl',
            'offsetToFpd',
            'oil',
            'other',
            'otherMonthlyCost1',
            'otherMonthlyCost2',
            'otherMonthlyCost3',
            'otherMonthlyCost4',
            'otherMonthlyCost5',
            'otherMonthlyCost6',
            'otherMonthlyCost7',
            'otherMonthlyCost8',
            'processing',
            'rateType',
            'rows',
            'rowsCalculationMethod',
            'shrinkageCondition',
            'stopAtEconLimit',
            'totalFluid',
            'transportation',
            'variableExpenses',
            'waterDisposal',
        }
    ),
    'Capex': frozenset(
        {
            'afterEconLimit',
            'applyToCriteria',
            'calculation',
            'capexExpense',
            'category',
            'completionStartDate',
            'date',
            'dealTerms',
            'depreciationModel',
            'description',
            'distributionType',
            'escalationModel',
            'escalationStart',
            'firstProdDate',
            'fromHeaders',
            'intangible',
            'lowerBound',
            'mean',
            'mode',
            'offsetToEconLimit',
            'offsetToFpd',
            'otherCapex',
            'rows',
            'seed',
            'spudDate',
            'standardDeviation',
            'tangible',
            'upperBound',
        }
    ),
    'ReservesCategory': frozenset(
        {
            'prmsCategory',
            'prmsClass',
            'prmsSubCategory',
            'reservesCategory',
        }
    ),
    'Pricing': frozenset(
        {
            'basedOnPriceRatio',
            'breakeven',
            'cap',
            'dates',
            'dollarPerBbl',
            'dollarPerMcf',
            'dollarPerMmbtu',
            'dripCondensate',
            'entireWellLife',
            'escalationModel',
            'gas',
            'ngl',
            'npvDiscount',
            'oil',
            'pctOfOilPrice',
            'price',
            'priceModel',
            'priceRatio',
            'rows',
        }
    ),
    'DateSettings': frozenset(
        {
            'alignDependentPhases',
            'asOf',
            'asOfDate',
            'cashFlowPriorAsOfDate',
            'cutOff',
            'date',
            'dateSetting',
            'discount',
            'discountDate',
            'econLimitDelay',
            'firstFpdSource',
            'firstNegativeCashFlow',
            'forecast',
            'fourthFpdSource',
            'fpdSourceHierarchy',
            'includeCapex',
            'lastPositiveCashFlow',
            'maxCumCashFlow',
            'maxWellLife',
            'minLife',
            'noCutOff',
            'none',
            'notUsed',
            'productionData',
            'productionDataResolution',
            'secondFpdSource',
            'thirdFpdSource',
            'tolerateNegativeCF',
            'triggerEclCapex',
            'useForecastSchedule',
            'wellHeader',
            'yearsFromAsOf',
        }
    ),
    'OwnershipReversion': frozenset(
        {
            'balance',
            'dripCondensateNetRevenueInterest',
            'eighteenthReversion',
            'eighthReversion',
            'eleventhReversion',
            'fifteenthReversion',
            'fifthReversion',
            'firstReversion',
            'fourteenthReversion',
            'fourthReversion',
            'gasNetRevenueInterest',
            'includeNetProfitInterest',
            'initialOwnership',
            'leaseNetRevenueInterest',
            'netProfitInterest',
            'netProfitInterestType',
            'netRevenueInterest',
            'nglNetRevenueInterest',
            'nineteenthReversion',
            'ninthReversion',
            'oilNetRevenueInterest',
            'ownership',
            'reversionTiedTo',
            'reversionType',
            'reversionValue',
            'secondReversion',
            'seventeenthReversion',
            'seventhReversion',
            'sixteenthReversion',
            'sixthReversion',
            'tenthReversion',
            'thirdReversion',
            'thirteenthReversion',
            'twelfthReversion',
            'twentiethReversion',
            'type',
            'value',
            'workingInterest',
        }
    ),
    'ActualOrForecast': frozenset(
        {
            'actualOrForecast',
            'asOfDate',
            'date',
            'gas',
            'ignoreHistoryProd',
            'never',
            'oil',
            'replaceActualWithForecast',
            'water',
        }
    ),
    'Risking': frozenset(
        {
            'dripCondensate',
            'entireWellLife',
            'gas',
            'multiplier',
            'ngl',
            'oil',
            'riskNglDripCondViaGasRisk',
            'riskProd',
            'risking',
            'rows',
            'water',
        }
    ),
}


def collect_keys(payload: Any) -> FrozenSet[str]:
    """Every ``dict`` key appearing anywhere in ``payload`` (recursively)."""
    found: Set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                found.add(key)
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(payload)
    return frozenset(found)


def key_drift(econ_model_type: str, model: Dict[str, Any]) -> List[str]:
    """Payload keys not in the type's baseline (envelope keys excluded), sorted.

    A non-empty result means CC emitted a key the mappers do not recognize. If the type
    has no baseline entry, every non-envelope key is reported.
    """
    baseline = _BASELINE_KEYS.get(econ_model_type, frozenset())
    present = collect_keys(model)
    return sorted(present - baseline - ENVELOPE_KEYS)


def value_drift(econ_model_type: str, model: Dict[str, Any]) -> Optional[str]:
    """``None`` if the forward mapper renders ``model`` cleanly; otherwise the exception
    string (unknown category/unit/criteria/enum/``entireWellLife``, or validation error).
    """
    try:
        get_mapper(econ_model_type).to_csv_rows(model)
    except Exception as exc:
        return f'{type(exc).__name__}: {exc}'
    return None


def _roundtrip_diff(
    rows1: Sequence[Dict[str, str]], rows2: Sequence[Dict[str, str]], columns: Sequence[str]
) -> Optional[str]:
    """Describe the first difference between two CSV renderings on the round-trippable
    columns (context/timestamp columns excluded), or ``None`` if they match. Pure; unit-tested
    directly."""
    cmp_cols = [c for c in columns if c not in _NON_ROUNDTRIP_COLUMNS]
    if len(rows1) != len(rows2):
        return f'row count changed on round-trip: {len(rows1)} -> {len(rows2)}'
    for i, (r1, r2) in enumerate(zip(rows1, rows2)):
        diffs = [(c, r1.get(c) or '', r2.get(c) or '') for c in cmp_cols if (r1.get(c) or '') != (r2.get(c) or '')]
        if diffs:
            return f'row {i} changed on round-trip: {diffs[:4]}'
    return None


def roundtrip_drift(econ_model_type: str, model: Dict[str, Any]) -> Optional[str]:
    """``None`` if the model survives a CSV round-trip unchanged; otherwise a description of
    the first divergence.

    Idempotency check: ``to_csv_rows`` -> ``from_csv_rows`` -> ``to_csv_rows`` must reproduce
    the same CSV rows on the round-trippable columns. A divergence means the inverse
    (``from_csv_rows``) lost or altered information the forward path emitted. An exception on
    the inverse or the second forward pass is reported too; the FIRST forward pass is
    :func:`value_drift`'s job, so :func:`audit_model` only calls this once that pass succeeds.
    """
    mapper = get_mapper(econ_model_type)
    try:
        rows1 = mapper.to_csv_rows(model)
        rebuilt = mapper.from_csv_rows(rows1)
        rows2 = mapper.to_csv_rows(rebuilt)
    except Exception as exc:
        return f'inverse/round-trip raised {type(exc).__name__}: {exc}'
    return _roundtrip_diff(rows1, rows2, mapper.columns)


class DriftFinding(NamedTuple):
    econ_model_type: str
    model_id: str
    model_name: str
    unknown_keys: List[str]
    map_error: Optional[str]
    roundtrip_error: Optional[str] = None


def audit_model(econ_model_type: str, model: Dict[str, Any]) -> Optional[DriftFinding]:
    """A :class:`DriftFinding` if ``model`` shows any kind of drift, else ``None``.

    Round-trip is checked only when the forward pass (``value_drift``) succeeds -- a forward
    crash is already reported as ``map_error``, and the round-trip would just re-raise it.
    """
    unknown_keys = key_drift(econ_model_type, model)
    map_error = value_drift(econ_model_type, model)
    roundtrip_error = None if map_error is not None else roundtrip_drift(econ_model_type, model)
    if not unknown_keys and map_error is None and roundtrip_error is None:
        return None
    return DriftFinding(
        econ_model_type=econ_model_type,
        model_id=str(model.get('id', '') or ''),
        model_name=str(model.get('name', '') or ''),
        unknown_keys=unknown_keys,
        map_error=map_error,
        roundtrip_error=roundtrip_error,
    )


def audit_models(econ_model_type: str, models: Sequence[Dict[str, Any]]) -> List[DriftFinding]:
    """Audit a batch of models of one type; return only the ones with drift."""
    findings: List[DriftFinding] = []
    for model in models:
        finding = audit_model(econ_model_type, model)
        if finding is not None:
            findings.append(finding)
    return findings
