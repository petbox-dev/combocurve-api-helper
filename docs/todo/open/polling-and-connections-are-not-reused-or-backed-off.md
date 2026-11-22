# Job polling and connections are not backed off or reused

Severity: low
Opened: 2026-11-22

## What happens now

Judgement calls skipped by the code-fix run on the missing-api-routes branch (2026-11-22), each a behavior
change:

- `APIBase._wait_for_job` polls every `poll_seconds` (2 s) for up to 600 s (900 s for exports): 30-40 GETs for
  a forecast export that finishes in 60-80 s, up to 450 for a slow one. A growing pause capped near 10 s would
  take about 12.
- The per-forecast root volume read and the 100-value batches are read one after another; a small thread pool
  would cut wall time, but `_request_with_retry` has no shared 429 state, so concurrent reads would each back
  off alone.
- `_transport` calls `requests.request` with no `Session`, so every request opens a new connection.
- `scripts/generate_route_coverage.py` imports `tests/route_manifest.py` and `tests/postman_collection.py`
  (the latter imports `pytest`); `scripts/generate_docstrings.py` keeps its logic in the script instead.

## What would unblock it

A read-route rate limit from ComboCurve (for the concurrency), and a decision on the poll backoff. The
`Session` change needs the test doubles (`tests/http_fakes.py`, `tests/route_manifest.py` `Recorder`) to patch
the session.

## Files

`src/combocurve_api_helper/base.py`, `_transport.py`, `root.py`, `scripts/generate_route_coverage.py`
