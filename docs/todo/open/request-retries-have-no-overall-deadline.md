# Request retries have no overall deadline

Severity: low
Opened: 2026-09-30

## What happens now

The status retry in `_request_with_retry` (up to 6 attempts) wraps the connection retry in
`_send_request` (up to 3 sends), so one GET can be sent 18 times. The read timeout (300 s) is per
socket read, not per request. Worst case for a GET that keeps timing out: about 5,470 s (91 min) with
gateway backoff, about 5,740 s (96 min) with 429 pauses (arithmetic from the constants, not measured).
A slow trickle of bytes is unbounded. A `Retry-After` is honoured up to `_MAX_RETRY_AFTER_SECONDS`
(3600 s, set 2026-09-30 because `time.sleep` overflows near 1e10 s). With 5 status retries, a
server that keeps answering 429 with a large `Retry-After` can hold one call for about 5 hours.

Nothing here can send a write twice; the cost is only time.

## Evidence

Computed in the 2026-09-30 `/code-fix` WRITE audit from `_MAX_REQUEST_RETRIES`,
`_MAX_CONNECTION_RETRIES`, `_REQUEST_TIMEOUT_SECONDS` and the backoff constants in `base.py`.

## What would unblock it

A decision on an overall per-call deadline and a `Retry-After` ceiling, then one clock checked in
both loops.

## Files

- `src/combocurve_api_helper/base.py`: `_send_request`, `_request_with_retry`, `_retry_after_seconds`
