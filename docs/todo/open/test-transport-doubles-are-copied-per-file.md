# Test transport doubles are copied per file

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
