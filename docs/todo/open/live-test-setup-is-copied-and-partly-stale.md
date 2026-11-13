# Live-test setup is copied and partly stale

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
