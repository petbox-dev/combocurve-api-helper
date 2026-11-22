# Decisions pending from the route and TODO pass

Severity: medium
Opened: 2026-11-21

The 2026-11-21 pass wrapped every published route and settled most open items. The maintainer then told the
lead to carry out every recommendation (2026-11-21). This file records what was done and what still needs the
maintainer. Close it when the "Still open" list is empty.

## Done (recommendations carried out, 2026-11-21)

1. **Project-scoped root volumes:** client-side per-forecast fallback in `get_root_forecast_*_volumes`, with
   a count check that raises `RuntimeError` on a mismatch; verified exact on dev (3,983 rows monthly and daily,
   24,798 rows monthly). The support report is drafted (see Still open). The item stays open, at medium, until
   ComboCurve fixes the route.
2. **Public page iterator:** `APIBase.iter_pages`; `_get_items_iterator` delegates to it with no warning.
   `list-getters-hold-the-full-result-in-memory` is closed.
3. **Production comments on a tenant:** the request to ComboCurve is drafted (see Still open).
4. **Collapsed docstring arrays:** accepted and documented in CLAUDE.md;
   `docstring-freshness-check-tolerates-unsourced-markers` is closed.
5. **Read-only production scan for migrated v1 normalizations:** done (744 GETs, no writes; 526 type curves).
   It found 12 migrated `linear`, `power_law_fit` or `eur_and_peak` curves but no v1 definition to pair them
   with, so no mapping was written. Findings are in `v1-type-curve-normalizations-are-not-written-to-v2`.
6. **mypy `deprecated` error code:** left off (recommendation B). The typing test pins the overload.
7. **`filters` on `get_scenario_econ_model_assignments`:** deferred until a caller needs it (recommendation).
   The url builder already takes a repeated `wellId` (100 per request, live).
8. **Unassign of more than 100 wells:** refused locally, not split (recommendation kept).
9. **v1 normalization mapping:** closed as won't-do (maintainer decision);
   `v1-type-curve-normalizations-are-not-written-to-v2` is in `closed/`.
10. **ComboCurve requests sent (2026-11-22, by the maintainer):** the project-scoped root volume bug report
   (`docs/local/2026-11-21-combocurve-bug-report-project-scoped-root-volumes.md`) and the request to enable
   production comments on the dev tenant (`docs/local/2026-11-21-combocurve-request-enable-production-comments.md`).
   Their follow-ups live in `project-scoped-root-volumes-repeat-and-drop-rows` and
   `production-comment-routes-are-unverified-live`.
11. **Package index skill:** its dependents list now names all seven packages and the scripts that use the
   helper (edited in the skills repo; not committed).

## Still open

1. **Deprecation of `_get_items_iterator`:** start the warning after the downstream MCP server moves its call
   sites to `iter_pages`. **Recommendation:** move those call sites when that server next updates the helper.
