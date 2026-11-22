# Test transport doubles are copied per file

Closed: 2026-11-21 -- settled by: 18 test files moved onto `tests/http_fakes.py` (`RecordingTransport`, new `install_responding_transport`, recorded `headers` and `data`); the route audit records (method, exception type) against `EXPECTED_EXCEPTIONS` and fills arguments from the evaluated annotations
If this was wrong, you will see: a test file with its own `requests.request` replacement or a private-method stub, other than `test_connection_retry.py`, `test_auth.py`'s token endpoint and the route audit; or a route-audit exception that is not in `EXPECTED_EXCEPTIONS`

Severity: low
Opened: 2026-11-13

## What happens now

3.1.0 made `tests/http_fakes.py` the home of one recording transport (`RecordingTransport`,
`RecordedCall`, `install_recording_transport`), and moved five test files onto it. About twelve
local `fake_request` closures and recorders remain, each with its own record shape:

- `tests/test_batch_write.py` (4), `tests/test_exports.py` (3), `tests/test_production_batched.py`
  (2), `tests/test_directional_page_size.py`, `tests/test_count_routes.py`,
  `tests/test_root_urls_and_params.py`, `tests/test_typecurves_deprecation.py`, `tests/test_auth.py`;
- `_Recorder` in `tests/test_single_object_requests_use_the_transport.py` (records `timeout`, now
  also in `RecordedCall`) and `_Script` in `tests/test_connection_retry.py`.

They differ in method case (some record the raw lowercase verb), in which keywords they accept, and in
what they do past the last queued response. `V1 = 'https://api.combocurve.com/v1'` is redefined in
six test files.

`tests/test_published_routes_are_wrapped.py` keeps its own `_Recorder` on purpose: it records
(verb, normalized path) for every method, a different job.

## Fix

Move each file onto `install_recording_transport` when it is next touched, or in one pass. Keep a
local double only where its job differs, and say why in its docstring.

## Related, in the route audit

`_call_every_public_method` discards every exception (`except Exception: pass`), so it cannot tell
"no route for this type" from a placeholder that does not fit; four econ-run methods already raise on
the fake body after they send. `_placeholder_for` matches annotation text (`'Item' in annotation`
would fill `Sequence[Item]` with a dict). Record (method, exception type) against a reviewed list,
as `_UNWRAPPED` does.

Found by the `/code-fix` run over 3.1.0 (2026-11-13), Phases 2-3.

## Status (2026-11-21)

Done for the transport doubles. `tests/http_fakes.py` gained `V1` / `V2` (from
`ComboCurveAPI.API_BASE_URL` / `API_BASE_URL_V2`), a `respond` callback on `RecordingTransport` with
`install_responding_transport` (for a response that depends on the request, or a request count the test
does not fix), the `headers` and raw `data` fields of `RecordedCall`, and `methods_and_urls`. These files
moved onto it: `test_batch_write.py`, `test_exports.py`, `test_production_batched.py`,
`test_directional_page_size.py`, `test_count_routes.py`, `test_typecurves_deprecation.py`,
`test_auth.py` (the page loop), `test_auth_concurrency.py`,
`test_company_routes_without_company_endpoint.py`, `test_single_object_requests_use_the_transport.py`,
`test_econ_settings.py`, `test_forecast_volume_put.py`, `test_forecast_configurations_and_project_wells.py`,
`test_assignment_write_generics.py`, `test_scenario_assignments.py`, `test_require_any_filter.py`,
`test_production_delete.py`, `type_curves/test_v1_compatibility.py` (the connection failure). The tests
that stubbed `_put_items` / `_patch_items` / `_delete_responses` now see the real requests, so they also
show that a write is not split (or is split at the limit). `V1` is defined once. Kept local on purpose,
with the reason in the docstring: `_Script` in `test_connection_retry.py` (raised outcomes and a clock),
`FakeTokenEndpoint` in `test_auth.py` (`requests.post` for the token). `test_root_urls_and_params.py`
and the route audit's `_Recorder` were out of this pass's scope.

Still open: the route-audit part below.
