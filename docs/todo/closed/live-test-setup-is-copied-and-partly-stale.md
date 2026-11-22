# Live-test setup is copied and partly stale

Closed: 2026-11-21 -- settled by: one dev credentials path and fixture prefix in `tests/live_support.py`, a session-scoped `dev_api` fixture in `tests/conftest.py` (one dev token per run); `test_assignments_live.py` cleans up with `delete_scenario_qualifiers` and asserts `X-Delete-Count`, and gained a two-well unassign, a saved-combo delete by `combo_ids` and a lookup-table assignment read/unassign test; all dev live files passed on 2026-11-21
If this was wrong, you will see: a failed qualifier cleanup (`X-Delete-Count` not 1), or leftover `API Helper Fixture` qualifiers, combos or lookup tables on the dev project

Severity: low
Opened: 2026-11-13

## What happens now

- The dev credentials path (`~/.combocurve/dev`) is defined three times: `test_api.py`
  (`CONFIG_PATH`), `test_assignments_live.py` (`DEV`), `test_embedded_lookup_tables_live.py` (`DEV`).
- `test_api.py`'s `api` fixture is function-scoped, so each test fetches its own OAuth token. The
  token endpoint allows 10 requests per client per 15 minutes; `test_api.py` has 2 tests today, so it
  does not hit the limit yet. `test_embedded_lookup_tables_live.py` and `test_type_curves_v2_live.py`
  use `scope='module'`.
- `test_assignments_live.py` cleans up its qualifier with a raw `requests.delete` and no
  `raise_for_status`. Its comment says the helper's `delete_scenario_qualifiers` sends `econName` and
  400s; that was fixed (it sends `econNames`, pinned by `test_scenario_assignments.py`). A failed
  cleanup leaks the qualifier silently, and its name `zz_apitest_*` is not an `API Helper Fixture*`
  name.
- No live test covers `delete_scenario_combo(combo_ids=...)` or the lookup-table assignment read and
  unassign, although their docstrings state live-verified behavior.

## Fix

One shared dev-credentials path and a module-scoped client; clean up with
`api.delete_scenario_qualifiers` and assert `X-Delete-Count`; rename the qualifier to the fixture
prefix.

Found by the `/code-fix` run over 3.1.0 (2026-11-13), Phase 2 duplication pass.

## Status (2026-11-21)

Done in the test files: `tests/live_support.py` holds `DEV_CREDENTIALS_DIRECTORY`, `FIXTURE_PREFIX` and
`live_tests_enabled()`; `tests/conftest.py` has a session-scoped `dev_api` client, used by `test_api.py`,
`test_assignments_live.py`, `test_embedded_lookup_tables_live.py`, `test_econ_settings_live.py` and
`test_production_comments_live.py` (each keeps its own skip condition). `test_assignments_live.py` names
its qualifiers `API Helper Fixture Q <hex>`, deletes them with `delete_scenario_qualifiers` and asserts
`X-Delete-Count: 1`, and has new tests: a two-well unassign in one call (`X-Delete-Count: 2`),
`delete_scenario_combo(combo_ids=...)` on a fixture saved combo, and the lookup-table assignment read and
unassign on a fixture lookup table in a fixture qualifier (`X-Delete-Count: 0`, because the route clears
only the active qualifier). The new live tests have not been run yet; close this item when they pass.
