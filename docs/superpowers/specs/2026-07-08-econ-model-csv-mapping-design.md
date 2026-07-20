# Econ-Model API <-> CSV Mapping — Design (combocurve-api-helper)

**Date:** 2026-07-08
**Status:** Draft for review. All value mappings ✅ verified against populated CC exports (`examples/*.csv` + `examples/MoreExamples/*.csv`) and the live API. One open item: confirm the enum move (bottom).

## Purpose

Add a typed, **exact and invertible** mapping between ComboCurve econ-model **API JSON** and CC's **relational CSV export** format, for five model types: StreamProperties, Differentials, ProductionTaxes, Expenses, Capex.

- **Forward** (primary): API JSON -> flat CSV rows (`to_csv_rows`). A flatten.
- **Inverse** (sibling): CSV rows -> API JSON (`from_csv_rows`). A build, structurally identical to cc-afe-sync's production `CapExBuilder.json()`.

The inverse must round-trip, so value transforms reproduce CC's export vocabulary and formatting exactly (not just column names). This layer lives in the helper so both cc-afe-sync (SQL->API today) and cc-api-scripts (API->SQL) can depend on it; cc-afe-sync's existing econ-model models migrate to import from here.

## Decisions (confirmed)

- **Home:** `combocurve-api-helper`, new subpackage `combocurve_api_helper/econ_models/`.
- **Style:** pydantic `BaseModel` (new helper dependency), mirroring cc-afe-sync's `models/` (`Field(alias=...)`, `BeforeValidator`, `StrEnum`).
- **Columns:** exact conformance to CC's export layout (verified column lists below); **model columns only** (the ~33 leading well-header columns are out of scope — they come from the scenario grid, not the model API).
- **Added non-CSV columns kept for the SQL pipeline** (emitted by `to_csv_rows` when a `context` is supplied, else omitted): `Model Id` (`id`), `Created At` (`createdAt`), `Project Name`. `New Name` (always None) and `Embedded Lookup Table` (None for pulled models) included per round-trip fidelity.
- The as-built cc-api-scripts `feature/cc-econ-models-sync` and db-schemas `feature/cc-econ-model-tables` branches are **held as reference**, not merged.

## Package layout

```
combocurve_api_helper/econ_models/
  __init__.py          # exports the 5 mappers + a registry keyed by econModelType
  enums.py             # StrEnums ported from cc-afe-sync (Criteria, OffsetTo, CapExCategory, GrossOrNet, Phase, ...) + CSV-vocab enums
  csv_columns.py       # ordered CSV column list per type + global value formatters
  base.py              # EconModelMapper protocol/ABC: to_csv_rows(model, context=None), from_csv_rows(rows)
  stream_properties.py
  differentials.py
  production_taxes.py
  expenses.py
  capex.py
```

Each type module defines: an API-aligned pydantic model (row + container, e.g. `DifferentialRow` / `DifferentialsModel`), `to_csv_rows`, and `from_csv_rows`. `enums.py` is the single source of CC vocabulary; cc-afe-sync's `models/capex.py` enums move here and cc-afe-sync imports them.

## Global value conventions (✅ verified from exports)

- **Model Type**: lowercase `project` / `unique` (`unique` bool). (CC also uses `lookup`; not pulled.)
- **Dates** (`Period`, capex `Value`): `MM/DD/YYYY`. **Last Update / Created At**: `MM/DD/YYYY HH:MM:SS`. (API gives ISO-8601.)
- **Booleans**: `yes` / blank (⚠️ confirm blank vs `no` per column; capex `Appear After Econ Limit` shows `yes`/`no`).
- **Escalation / Depreciation**: CC emits the model **name** (`none`/`None` when unset). API gives `none`/`None` or an ObjectId. **v1: pass the API value through as-is** (no id->name resolution) per decision; a real attached model will show its id rather than its name until a later version adds resolution.
- Numbers: as-is; capex Tangible/Intangible are M$ (thousands), matching the API value.

## Per-type CSV columns (verified) + mapping

Common leading (added, pipeline-only): `Model Id, Created At, Project Name`. Common model cols: `Model Type, Model Name, New Name, Embedded Lookup Table, <type cols>, Last Update`.

### StreamProperties  (already matches; only Model Type casing changes)
Type cols: `Key, Category, Criteria, Value, Period, Unit, Gas Shrinkage Condition, Rate Type, Rate Rows Calculation Method, Yield Source, Yield (BBL/MMCF), Mol %, Gal/lb-mol Factor, Plant Eff (%), Shrink (% Remaining), BTU (MBTU/MCF), Post Extraction (%)`. Values (Key `yields`/`shrinkage`/`loss & flare`/`btu`, Category `oil`/`gas`/`ngl`/`drip cond`/`oil loss`/..., Unit `bbl/mmcf`/`% remaining`, `unshrunk`) ✅ match. Reuse the existing `StreamPropertiesParser` flatten logic.

### Differentials
Type cols: `Key, Phase, Criteria, Value, Period, Unit, Escalation`.
- `Key` ✅ `differentials_1|2|3`  <- `firstDifferential|secondDifferential|thirdDifferential`
- `Phase` ✅ `oil|gas|ngl|drip cond`; `Criteria` ✅ `flat|dates`; `Period` date `MM/DD/YYYY` or blank
- `Unit` ✅ `$/bbl|$/mcf|$/mmbtu|% base price rem`; `Escalation` name/`none`

### ProductionTaxes
Type cols: `Production Taxes State, Key, Stream Type, Category, Criteria, Value, Period, Unit, Description, Shrinkage Condition, Escalation, Calculation, Deduct Severance Tax, Rate Type, Rate Rows Calculation Method`.
- `Production Taxes State` ✅ `data.state`
- severance rows: `Key` ✅ phase; `Category` ✅ `Severance Tax` when the phase has one severance tax, else numbered `Severance Tax 1`/`Severance Tax 2`/... by ordinal within the phase (Texas oil: `Severance Tax 1` 4.6 `% of rev` + `Severance Tax 2` 0.0081 `$/bbl`)
- ad-valorem row: `Key` ✅ `Ad Valorem Tax`, `Category` ✅ `Ad Val Tax`, `Deduct Severance Tax` ✅ `yes`/`no`/blank
- `Stream Type` ✅ always blank; `Unit` ✅ `% of rev` | `$/bbl` | `$/mcf`; `Description` ✅ blank
- `Criteria/Value/Period/Calculation/Shrinkage Condition/Escalation/Rate Type/Rate Rows Calculation Method` pass through

### Expenses
Type cols: `Key, Category, Criteria, Value, Period, Unit, Description, Shrinkage Condition, Escalation, Calculation, Affect Econ Limit, Deduct bef Sev Tax, Deduct bef Ad Val Tax, Stop at Econ Limit, Expense bef FPD, Cap, Paying WI / Earning WI, Rate Type, Rate Rows Calculation Method`.
- `Key` ✅ stream/group: `oil|gas|ngl|drip cond|boe|total_fluid` (variable), `ch4|co2|co2e|n2o` (carbon), `fixed`, `water`
- `Category` ✅ line: variable -> `g&p|opc|trn|mkt|other` (**verified via `SAMPLE_OPEX_LOOKUP_0001`: API `oil.processing`/desc `OPC/OIL` -> `opc`; so gathering->`g&p`, processing->`opc`, transportation->`trn`, marketing->`mkt`, other->`other`**); carbon -> `co2e` (Unit `$/MT`); fixed -> `fixed1..fixed9` (monthlyWellCost->`fixed1`, otherMonthlyCost1..8->`fixed2..fixed9`); water -> blank (Unit `$/bbl`)
- `Criteria` ✅ `flat|fpd`; `Period` for `fpd` = the API row's `offsetToFpd` month count as a string, with CC's terminal value `1200` (100 yr) rendered as `ecl` (economic limit); blank for `flat`. `Unit` ✅ `$/bbl|$/mcf|$/month|$/MT`
- `Paying WI / Earning WI` ✅ `dealTerms`; `Description` ✅; booleans -> `yes`/blank ⚠️; `Cap` ✅; `Subcategory` dropped

### Capex
Type cols: `Category, Description, Tangible (M$), Intangible (M$), Criteria, From Schedule, From Headers, Value, CAPEX or Expense, Appear After Econ Limit, Calculation, Escalation, Escalation Start Criteria, Escalation Start Value (Days/Date), Depreciation, Paying WI / Earning WI`.
- No Key/Period/Unit. Rows from `otherCapex.rows` **only** — verified against `Sample_Onboarding` model `Example` (API has 30 `otherCapex.rows` + populated `$/ft` `drillingCost`/`completionCost`): CC's CSV contains exactly the 30 `otherCapex` rows and **zero** rows for the `$/ft` objects. So the mapper emits `otherCapex` only, matching CC. `Category` spans the full `CapExCategory` enum incl. `drilling`/`completion` (these are `otherCapex` *categories*, distinct from the `$/ft` `drillingCost`/`completionCost` objects, which CC does not represent in this CSV). **Round-trip asymmetry:** a model whose D&C cost lives only in `$/ft drillingCost`/`completionCost` (no `otherCapex` drilling/completion rows) exports to no CSV rows and cannot be reconstructed by `from_csv_rows`; document and warn.
- `Category` ✅ (space-cased CapExCategory); `Tangible (M$)/Intangible (M$)` ✅.
- `Criteria` ✅ full set: `fpd`, `as of`, `disc date`, `econ limit`, `maj seg`, `date`, `oil rate`, `gas rate`, `water rate`, `total fluid rate`, `from headers`, `from schedule` (= cc-afe-sync `Criteria` enum).
- `Value` ✅ = date `MM/DD/YYYY` (date criterion), the offset (`-120`) for date-offset criteria, or the rate for `*_rate` criteria.
- `From Schedule`/`From Headers` ✅ populated only for `from schedule`/`from headers` (e.g. `Spud Start`/`Completion Start`; `Spud Date`/`Completion Start Date`) with `Value=0`; map from cc-afe-sync `OffsetTo` + `_dateLookup` to these display names.
- `CAPEX or Expense` ✅ `capexExpense`; `Appear After Econ Limit` ✅ `yes`/`no`; `Calculation` ✅ `gross`
- `Escalation Start Criteria` ✅ `apply to criteria`; `Escalation Start Value (Days/Date)` ✅; `Depreciation` ✅ name/`None`; `Paying WI / Earning WI` ✅ `dealTerms`

## Testing

- **Round-trip unit tests** per type: hand-built API JSON -> `to_csv_rows` -> assert exact CSV row dicts (from the verified vocab) -> `from_csv_rows` -> assert equals the original API JSON. This pins invertibility.
- **Fixture tests** against small slices of `examples/*.csv` (the full files are 100-200MB; commit a trimmed fixture of a few populated models per type).
- mypy --strict clean; pydantic models validate on construction.

## Resolved (verified against the `Sample Project E | NonOp | Multi Basin` export + API)

- Expenses variable subcat -> `g&p/opc/trn/mkt/other` ✅ (gathering->g&p, processing->opc, transportation->trn, marketing->mkt, other->other).
- Fixed slot -> `fixed1..fixed9` ✅ (monthlyWellCost->fixed1, otherMonthlyCost1..8->fixed2..fixed9).
- Escalation/Depreciation: pass API value through (no id->name resolution) for v1 ✅.
- Expenses `fpd` `Period`: `offsetToFpd` months, terminal `1200` -> `ecl` ✅.
- Booleans: per-column, matching observed vocab (severance deduct blank/`yes`; capex after-econ-limit `yes`/`no`) ✅.
- Differentials `Unit`: `$/bbl`/`$/mcf`/`$/mmbtu`/`% base price rem` ✅. Capex `Depreciation`=`None`, `CAPEX or Expense`=`capex`, `Appear After Econ Limit`=`yes`/`no` ✅.

All mapping questions resolved via `examples/MoreExamples/*.csv` + API:
- Prod-tax dollar units -> `$/bbl`/`$/mcf`; multiple severance taxes per phase -> `Severance Tax 1/2/...` ✅
- Capex criteria full set (`fpd`, `as of`, `disc date`, `econ limit`, `maj seg`, `date`, `*_rate`, `from headers`, `from schedule`) ✅
- Capex `from headers`/`from schedule` column tokens + `Value=0` ✅
- Capex drilling/completion are otherCapex categories; `$/ft` drilling/completion cost objects out of scope ✅

## Open question (needs a yes)

1. **Enums** (answering "what enums?"): cc-afe-sync `models/capex.py` defines `StrEnum`s `Criteria` (API values: `date`, `offsetToFpd`, `offsetToEconLimit`, `fromHeaders`, `fromSchedule`, `offsetToAsOf`, `offsetToDiscountDate`, `offsetToMajorSegment`, `oilRate`, `gasRate`, `waterRate`, `totalFluidRate`), `OffsetTo` (header tokens: `offset_to_spud_date`, `offset_to_completion_start_date`, ...), `CapExCategory` (`drilling`, `completion`, `abandonment`, `other_investment`, ...), `GrossOrNet` (`gross`/`net`). Plan: **move** these into `econ_models/enums.py` so the helper owns them and cc-afe-sync imports from the helper. Confirm the move (vs duplicate).

## Sequencing / non-goals

Implement enums+csv_columns+base first, then one type per task (StreamProperties reuses existing flatten; Capex reuses cc-afe-sync builder), each with round-trip tests. Not in scope now: migrating cc-afe-sync to import these; wiring cc-api-scripts to call the helper; the SQL sync itself (the held branch already does that and can be re-pointed later).
