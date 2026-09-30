# base.py mixes transport policy with the client class

Severity: low
Opened: 2026-09-30

## What happens now

`base.py` is about 930 lines. It holds the module-level transport policy and I/O (timeouts,
`_request_was_never_sent`, `_safe_to_send_again`, `_is_read_only`, `_send_request`,
`_gateway_retry_allowed`, `_retry_after_seconds`, `_retry_delay_seconds`) beside the 700-line
`APIBase` class. `_send_one_chunk` takes 6 loose parameters and does I/O, retry and 207-body parsing
in one function. Tests import private constants from `base`.

## Evidence

2026-09-30 `/code-fix` structural audit. Deferred because the move is about 150 lines, most of them
older than that run's diff.

## Fix

Move the policy, `_send_request`, `_RateLimitState` use and the retry helpers into
`_transport.py`; leave `APIBase` and the types in `base.py`. Bundle `(index, offset, chunk)` into
one chunk spec, and split "parse a 207 body" into a pure function.

## Files

- `src/combocurve_api_helper/base.py`, `src/combocurve_api_helper/_batch.py`
- `tests/test_connection_retry.py` (imports `_MAX_CONNECTION_RETRIES`, `_REQUEST_TIMEOUT_SECONDS`)
