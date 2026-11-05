# TODO index

Work that is not done lives here: one document per item in `open/`, kept in `closed/` when settled.
This repo is public: no confidential project, model, well or fund names in any document.

- Never write `# TODO:` in code. Fix it now, or open a document here.
- Name the file for the problem, not the fix. The name does not change when the item closes.
- Header: `# <problem>`, `Severity: high | medium | low`, `Opened: <YYYY-MM-DD>`. No frontmatter.
- Sections as needed: what happens now, evidence, what was ruled out, blast radius, what is still
  unverified, what would unblock it, files. Target 60 lines.
- Adding a document includes adding its row below. Sort by severity, then oldest first.
- To close: move the file to `closed/`, add `Closed: <date> -- settled by: <one line>` and
  `If this was wrong, you will see: <symptom>` at the top, and move the row to `## Done`.

| Item | Opened | Severity | Summary |
|---|---|---|---|
| [count-methods-and-list-methods-do-not-pair-everywhere](open/count-methods-and-list-methods-do-not-pair-everywhere.md) | 2026-09-30 | low | 4 list methods take no `filters` their counts accept; no company per-type counts; company `Emission`/`FluidModel` routes 400 |
| [base-py-mixes-transport-policy-with-the-client-class](open/base-py-mixes-transport-policy-with-the-client-class.md) | 2026-09-30 | low | Move the retry/timeout policy out of `base.py` into `_transport.py` |
| [docstring-freshness-check-tolerates-unsourced-markers](open/docstring-freshness-check-tolerates-unsourced-markers.md) | 2026-09-30 | low | `--check` exits 0 with unsourced markers; no `urlopen` timeout; collapsed arrays hide a length change |
| [type-curve-v1-wrappers-outlive-the-v1-api](open/type-curve-v1-wrappers-outlive-the-v1-api.md) | 2026-11-05 | low | `type_curves_v1_compatibility.py` stays until at least 2027-01-31; the file lists the removal steps |
| [v2-type-curve-routes-have-no-postman-source](open/v2-type-curve-routes-have-no-postman-source.md) | 2026-11-05 | low | The collection has no v2 type-curve operations; the route and slug tests skip them; the `-preview` docs path can move at GA |
| [forecast-output-slope-is-now-a-sign](open/forecast-output-slope-is-now-a-sign.md) | 2026-11-05 | low | Forecast outputs `slope` is the sign since 2026-10 and `slopeValue` the value; no consumer in this package is checked |
| [v1-type-curve-normalizations-are-not-written-to-v2](open/v1-type-curve-normalizations-are-not-written-to-v2.md) | 2026-11-05 | low | The write wrappers drop v1 `normalizations`; the migration of `linear`, `power_law_fit` and `eur_and_q_peak` is unseen |
| [published-routes-without-a-method](open/published-routes-without-a-method.md) | 2026-11-05 | low | 86 published v1 operations have no method (57 new Aug-Oct 2026), plus 6 docs-only embedded-lookup-table operations |
| [no-test-checks-that-published-routes-are-wrapped](open/no-test-checks-that-published-routes-are-wrapped.md) | 2026-11-05 | low | Make the call-based route audit a network-gated test (approved for after 3.0.0) |

## Done

| Item | Closed | Settled by |
|---|---|---|
| [request-retries-have-no-overall-deadline](closed/request-retries-have-no-overall-deadline.md) | 2026-11-05 | 600 s deadline per call across all retries; `Retry-After` capped at 120 s |
| [direct-requests-calls-bypass-timeout-and-retry](closed/direct-requests-calls-bypass-timeout-and-retry.md) | 2026-11-05 | All eight single-object call sites send through `_request_with_retry` (3.0.0; 2.7.1 on `2.x`) |
| [econ-model-csv-number-form-differs-from-cc-export](closed/econ-model-csv-number-form-differs-from-cc-export.md) | 2026-11-03 | Decided: every float-valued column writes `9.0` and reads as `float` (`float_columns`) |
| [production-taxes-rate-criteria-not-mapped](closed/production-taxes-rate-criteria-not-mapped.md) | 2026-11-03 | Rate and offset criteria, `$/month`/`$/boe` units and `null` values mapped, checked against a raw CC export; all 8,149 live models export |
| [econ-model-csv-values-unverified-against-a-raw-export](closed/econ-model-csv-values-unverified-against-a-raw-export.md) | 2026-11-03 | Dev exports show one-`btu`-at-default and company `Model Type`; `model_scope(rows)` added |
| [production-taxes-model-with-no-rows-loses-its-state](closed/production-taxes-model-with-no-rows-loses-its-state.md) | 2026-11-03 | CC's own export also writes no line for a model with no rows; the mapper matches it |
| [production-taxes-dates-period-loses-the-century](closed/production-taxes-dates-period-loses-the-century.md) | 2026-11-03 | CC exports `dates` as `MM/YYYY`; the mapper now writes and reads it (old `Mon-yy` still read) |
