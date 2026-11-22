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
| [project-scoped-root-volumes-repeat-and-drop-rows](open/project-scoped-root-volumes-repeat-and-drop-rows.md) | 2026-11-20 | medium | Server defect: project-scoped root volume listing returns wrong rows above 200 rows; the helper now reads per forecast (verified on dev); open until ComboCurve fixes the route (support report drafted, not sent) |
| [decisions-pending-from-the-route-and-todo-pass](open/decisions-pending-from-the-route-and-todo-pass.md) | 2026-11-21 | medium | Recommendations carried out; still yours: send the two drafted ComboCurve requests, time the `_get_items_iterator` deprecation |
| [type-curve-v1-wrappers-outlive-the-v1-api](open/type-curve-v1-wrappers-outlive-the-v1-api.md) | 2026-11-05 | low | `type_curves_v1_compatibility.py` stays until at least 2027-01-31; the file lists the removal steps |
| [production-comment-routes-are-unverified-live](open/production-comment-routes-are-unverified-live.md) | 2026-11-21 | low | Comment routes answer `ProductionCommentsDisabledError` on dev and prod; page size 200 is a guess |
| [forecast-segment-parameter-slope-on-write-is-unverified](open/forecast-segment-parameter-slope-on-write-is-unverified.md) | 2026-11-21 | low | Reads carry the sign in `slope`; the write side is unchecked |
| [shapefile-paths-not-verified-live](open/shapefile-paths-not-verified-live.md) | 2026-11-21 | low | Company upload, `projectIds` PATCH, shared-layer unlink and failed-job shape not exercised live |
| [export-jobs-have-no-wait-method](open/export-jobs-have-no-wait-method.md) | 2026-11-21 | low | v2 export job statuses unverified, so no `wait_for_export_*` on `_wait_for_job` |

## Done

| Item | Closed | Settled by |
|---|---|---|
| [v1-type-curve-normalizations-are-not-written-to-v2](closed/v1-type-curve-normalizations-are-not-written-to-v2.md) | 2026-11-21 | Won't do: no v1/v2 pair can be read anymore; 12 of 526 production curves affected |
| [list-getters-hold-the-full-result-in-memory](closed/list-getters-hold-the-full-result-in-memory.md) | 2026-11-21 | Public `iter_pages`; `_get_items_iterator` delegates to it |
| [docstring-freshness-check-tolerates-unsourced-markers](closed/docstring-freshness-check-tolerates-unsourced-markers.md) | 2026-11-21 | Unsourced markers fail `--check`; fetch timeout; malformed shapes exit 2; collapsed-array length gap accepted |
| [live-test-setup-is-copied-and-partly-stale](closed/live-test-setup-is-copied-and-partly-stale.md) | 2026-11-21 | Shared live setup; new live tests passed on dev |
| [type-curve-list-page-size-below-the-server-limit](closed/type-curve-list-page-size-below-the-server-limit.md) | 2026-11-21 | Type-curve list at 2,500 per page (live-verified); compatibility outputs at 1,000 |
| [url-builders-cannot-take-a-repeated-filter](closed/url-builders-cannot-take-a-repeated-filter.md) | 2026-11-21 | `QueryFilters` on repeated-key builders; both bypass sites call their builders |
| [econ-model-unassign-sends-an-empty-wells-filter](closed/econ-model-unassign-sends-an-empty-wells-filter.md) | 2026-11-21 | Blank wells refused locally; `wells` sent as repeated keys (a comma-joined value was a live 400) |
| [model-assignment-writes-do-not-enforce-the-500-record-limit](closed/model-assignment-writes-do-not-enforce-the-500-record-limit.md) | 2026-11-21 | 500-record and 25,000-`wellIds` caps enforced locally (`_require_at_most`, `_count_well_ids`) |
| [count-methods-and-list-methods-do-not-pair-everywhere](closed/count-methods-and-list-methods-do-not-pair-everywhere.md) | 2026-11-21 | `filters` added to the list methods whose GET documents the HEAD keys |
| [base-py-mixes-transport-policy-with-the-client-class](closed/base-py-mixes-transport-policy-with-the-client-class.md) | 2026-11-21 | Transport moved to `_transport.py`; `base.py` re-exports the moved names |
| [project-custom-columns-required-argument-typed-optional](closed/project-custom-columns-required-argument-typed-optional.md) | 2026-11-21 | Overloads make the argument required to type checkers |
| [forecast-output-slope-is-now-a-sign](closed/forecast-output-slope-is-now-a-sign.md) | 2026-11-21 | Reads verified live (3,695 outputs); docstrings state the split; write side opened separately |
| [published-routes-without-a-method](closed/published-routes-without-a-method.md) | 2026-11-21 | All 502 operations accounted for (484 wrapped, 0 gap) |
| [test-transport-doubles-are-copied-per-file](closed/test-transport-doubles-are-copied-per-file.md) | 2026-11-21 | Tests on the shared doubles; route audit checks exceptions against a reviewed list |
| [v2-type-curve-routes-have-no-postman-source](closed/v2-type-curve-routes-have-no-postman-source.md) | 2026-11-12 | v2 docstring links use the collection names; slug skip removed; route-path floor 170; examples generated (large ones point to the docs page) |
| [no-test-checks-that-published-routes-are-wrapped](closed/no-test-checks-that-published-routes-are-wrapped.md) | 2026-11-12 | `tests/test_published_routes_are_wrapped.py`: call-based audit against the collection, with a reviewed `_UNWRAPPED` list |
| [directional-surveys-page-size-above-api-maximum](closed/directional-surveys-page-size-above-api-maximum.md) | 2026-11-05 | `GET_LIMIT = 100` in `directional.py` (2.7.1 and 3.0.0) |
| [request-retries-have-no-overall-deadline](closed/request-retries-have-no-overall-deadline.md) | 2026-11-05 | 600 s deadline per call across all retries; `Retry-After` capped at 120 s |
| [direct-requests-calls-bypass-timeout-and-retry](closed/direct-requests-calls-bypass-timeout-and-retry.md) | 2026-11-05 | All eight single-object call sites send through `_request_with_retry` (3.0.0; 2.7.1 on `2.x`) |
| [econ-model-csv-number-form-differs-from-cc-export](closed/econ-model-csv-number-form-differs-from-cc-export.md) | 2026-11-03 | Decided: every float-valued column writes `9.0` and reads as `float` (`float_columns`) |
| [production-taxes-rate-criteria-not-mapped](closed/production-taxes-rate-criteria-not-mapped.md) | 2026-11-03 | Rate and offset criteria, `$/month`/`$/boe` units and `null` values mapped, checked against a raw CC export; all 8,149 live models export |
| [econ-model-csv-values-unverified-against-a-raw-export](closed/econ-model-csv-values-unverified-against-a-raw-export.md) | 2026-11-03 | Dev exports show one-`btu`-at-default and company `Model Type`; `model_scope(rows)` added |
| [production-taxes-model-with-no-rows-loses-its-state](closed/production-taxes-model-with-no-rows-loses-its-state.md) | 2026-11-03 | CC's own export also writes no line for a model with no rows; the mapper matches it |
| [production-taxes-dates-period-loses-the-century](closed/production-taxes-dates-period-loses-the-century.md) | 2026-11-03 | CC exports `dates` as `MM/YYYY`; the mapper now writes and reads it (old `Mon-yy` still read) |
