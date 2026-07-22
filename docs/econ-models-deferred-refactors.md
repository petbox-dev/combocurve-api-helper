# econ_models — Refactor Record

**Status: the three items below are now DONE** (completed on `feature/econ-model-csv-mapping`
after this doc was first written; verified behavior-preserving — full gates green, drift audit
0 across ~10.9k models incl. round-trip, `forward_diff` byte-unchanged). This doc is retained
as a record of the decisions (why each was first deferred, then done) and — more importantly
for a future session — the still-active **"Do not re-simplify"** guardrails at the end.

**Context.** During the `feature/econ-model-csv-mapping` work, a whole-branch structural
audit (code-refactor skill) reviewed the 11 econ-model mappers plus `drift.py`, `formats.py`,
`base.py`, `enums.py`, `csv_columns.py`. Its verdict was **structurally sound, no
merge-blocking issues**. The genuine cross-mapper-duplication wins it found were applied
immediately (commit `049e990`): the shared `flat_or_dates_criteria`/`flat_or_dates_row_kwargs`
helpers, `base.model_identity`, `formats.ENTIRE_WELL_LIFE_MARKER` / `formats.PHASE_TO_CSV_CAMEL`,
the `enums.py` `OffsetTo` reconciliation, and NamedTuples for the multi-element helper returns.

The three items below were initially **deferred** (each falls under the code-refactor skill's
own *When NOT to Refactor* section — cosmetic/below-threshold churn with regression risk on
verified-correct, about-to-merge code) and then **subsequently completed** on explicit
request. They are recorded here so a future session understands the reasoning and does not
undo them or re-litigate the trade-off.

**The general rule (for any future item like these):** do it opportunistically, when you are
*already* editing the file for a substantive reason — not as a standalone big-bang sweep — and
re-run the full verification afterward: gates (`mypy --strict`, `ruff`, `pytest`), the drift
audit (`scripts/audit_econ_model_drift.py`, includes round-trip), and `forward_diff` (the
real-CSV forward-fidelity harness) — all must stay green/unchanged.

---

## 1. Helper placement is inconsistent (`@staticmethod` vs module-level) — DONE

**Done.** All `@staticmethod` pure helpers in the 5 affected mappers (stream_properties 3,
differentials 2, pricing 3, production_taxes 3, expenses 7) were moved to module-level
functions; call sites updated `self._x(...)` → `_x(...)`. Module-level is now the uniform
convention across all 11 mappers.


**Finding (audit severity: Medium).** Pure helpers are placed inconsistently across mappers.
Some define them at module level (`capex.py`, `date_settings.py`, `ownership_reversion.py`,
`actual_or_forecast.py`, and the one-row mappers); others define equally-pure helpers as
`@staticmethod` on the mapper class (`stream_properties.py`, `differentials.py`, `pricing.py`,
`production_taxes.py`, `expenses.py`). None of the static methods use `self`.

**Why deferred.** Purely cosmetic — a `@staticmethod` that never touches `self` is
functionally a module-level function namespaced under the class; both read fine. Making it
uniform means relocating ~30–40 methods across 5 files, and every relocation rewrites its call
sites (`self._foo()` → `_foo()`), i.e. hundreds of lines of mechanical churn with real
regression surface (a missed rename, or a helper name shadowing a module-level symbol). Zero
correctness benefit. The refactor skill explicitly lists cosmetic-only changes and
"working abstractions at the wrong ideal level" under *When NOT to Refactor*.

**If you pick it up.** Choose module-level pure functions as the single convention (none use
`self`, so nothing is lost, and it matches the mappers that already read best). Convert one
mapper at a time, as you touch it. Preferred convention: module-level `def _helper(...)` above
the mapper class; keep only genuinely-stateful methods on the class (there are none currently).

---

## 2. Terse number-format import aliases (`_num` / `_numf` / `_renum`) — DONE

**Done.** The aliases were dropped across all 9 mappers that used them; call sites now use the
real names `num_to_csv` / `num_to_csv_float` / `csv_to_num` directly (imports de-aliased). The
local `_opt_num` / `_opt_renum` wrappers in `ownership_reversion.py` are distinct helpers and
were intentionally left as-is.


**Finding (audit severity: Low).** These import aliases are terse relative to the repo's
descriptive-name convention:
- `_num` = `num_to_csv` (render number → CSV, drops trailing `.0`)
- `_numf` = `num_to_csv_float` (render number → CSV, always keeps a decimal point)
- `_renum` = `csv_to_num` (parse CSV → number)

**Why deferred.** They are **consistent** across all 11 mappers (one convention applied
uniformly — this is not drift), they alias functions whose real names in `formats.py` are
fully descriptive, and they are the single most frequently-called formatters in the package
(number formatting appears in nearly every mapping-dict row). Short local handles arguably keep
the dense mapping dicts readable. Renaming touches every mapper's import block plus dozens of
call sites for a pure-style gain. The audit rated it Low/"acceptable."

**If you pick it up.** Either (a) leave as-is (defensible — consistent + defined at the import
line), or (b) if you want the long names, do a repo-wide rename in one commit so consistency is
preserved (never half-migrate — two conventions is worse than one). A cheaper middle option: a
one-line comment at each import block documenting the three aliases.

---

## 3. `date_settings.from_row_dicts` does several things (~70 lines) — DONE

**Done.** The cutOff assembly (criterion + minLife + fixed/conditional keys, with all
per-criterion gating and provenance comments verbatim) was extracted into a module-level
`_cutoff_from_csv(row) -> Dict[str, Any]`; `from_row_dicts` now calls it. The
`dateSetting`/`fpdSourceHierarchy` block stayed inline (already cohesive). Pure extraction —
all round-trip tests unchanged and green.


**Finding (audit severity: Low).** The function assembles four independent structures in
sequence — `dateSetting`, the `cutOff` criterion, `minLife`, and the cash-flow-conditional
columns.

**Why deferred.** It is **under** the 100-line guideline, reads top-to-bottom in clearly
commented sections, and the refactor skill states the 100-line rule "is for functions that are
hard to follow, not a hard rule for clean sequential logic." It is also the most intricate
inverse in the package, and the drift-gap fixes (new `date`/`firstNegativeCashFlow` cutoff
criteria, optional `discount`/`alignDependentPhases`, date-valued FPD source) just landed
there — decomposing now trades near-zero benefit for non-trivial regression risk against the
most complex round-trip in the codebase.

**If you pick it up.** Only when you are already modifying this function. Extract
`_cutoff_from_csv(row) -> Dict[str, Any]` (the cutOff criterion + minLife + cash-flow-conditional
assembly) as the natural seam; the `dateSetting`/`fpdSourceHierarchy` assembly is already
cohesive. Keep the verified-live provenance comments intact.

---

## What is NOT deferred (do not "re-simplify" these)

These look like duplication or shorthand but are **intentional** — leave them:

- **Per-type CSV vocabularies that look similar but differ.** e.g. `production_taxes.py` /
  `expenses.py` key drip condensate as `drip_condensate` while `differentials.py` / `pricing.py`
  use `dripCondensate`; the CSV `Unit`/`Category`/`Criteria` vocabularies genuinely differ per
  econ-model type (verified live). These are real API/CSV differences, not duplication.
- **`multiplier: Any` (risking) / `List[Any]` (production_taxes `value`/`period`).** Documented
  as intentional to preserve the API's exact int-vs-float type through the round-trip.
- **`Dict[str, Any]` at the API boundary.** The model dicts to/from the ComboCurve API are
  legitimately `Dict[str, Any]`; only internal intermediates would warrant a dataclass.
- **The `ownership_reversion` `_renum('')`-on-blank behavior** (raises a bare `ValueError` on a
  malformed/hand-edited blank numeric cell). This is *consistent package-wide* — every mapper
  uses `_renum` on numeric cells and behaves identically. Guarding only one site would create
  the inconsistency the audit warns against. If blank-numeric handling ever needs to be
  friendlier, do it once, package-wide, in `formats.csv_to_num`.
