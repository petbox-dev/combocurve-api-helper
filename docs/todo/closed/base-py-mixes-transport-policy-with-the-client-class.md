# base.py mixes transport policy with the client class

Closed: 2026-11-21 -- settled by: transport policy, I/O and the chunk send loop moved to `_transport.py`; `ChunkSpec` and the pure `chunk_from_207_body` in `_batch.py`; `base.py` re-exports every moved name (882 lines, was 1,178)
If this was wrong, you will see: an `ImportError` or `AttributeError` for a private transport name imported from `combocurve_api_helper.base`, or a batch or retry test failing on a changed retry count or `may_have_applied` value

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

## Settled 2026-11-21

`src/combocurve_api_helper/_transport.py` now holds the retry and timeout constants, the connection
policy (`_request_was_never_sent`, `_safe_to_send_again`, `_is_read_only`, `_send_request`), the
deadline helpers, `_retry_after_seconds`, `_retry_delay_seconds`, `_gateway_retry_allowed`, the status
retry loop (`_send_with_status_retries`), `Link` pagination (`get_next_page_url`,
`_next_page_url_on_request_origin`) and the batch-chunk send loop (`_send_batch_chunk`, which uses
`_RateLimitState`). `base.py` re-exports every moved name; `APIBase._request_with_retry` and
`_send_one_chunk` delegate to it. `_batch.py` gained `ChunkSpec` (index, offset, records), the pure
`chunk_from_207_body`, and `_whole_chunk_failure` (now takes a `ChunkSpec`). `base.py` went from 1178 to
about 920 lines (with two new batch helpers added in the same change).

## Files

- `src/combocurve_api_helper/base.py`, `src/combocurve_api_helper/_batch.py`
- `tests/test_connection_retry.py` (imports `_MAX_CONNECTION_RETRIES`, `_REQUEST_TIMEOUT_SECONDS`)
