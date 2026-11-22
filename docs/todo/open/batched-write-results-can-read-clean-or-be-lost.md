# Batched write results can read clean, or be lost after records were applied

Severity: medium
Opened: 2026-11-22

## What happens now

Two pre-existing gaps in the batched write path (`APIBase._request_batched`, `_batch.chunk_from_207_body`),
moved unchanged from `base.py` into `_transport.py` / `_batch.py` on the missing-api-routes branch:

1. A 2xx chunk whose body is not a 207 envelope (`None`, text, a list, an object with no `results`) reads as
   `success_count=0, failed_count=0, results=[]`. `BatchWriteResult.ok` is then True, and `results` stops
   lining up with `data` for every later chunk. `tests/test_transport_module.py`
   (`test_body_that_is_not_an_envelope_reads_as_empty`) pins that reading.
2. An exception other than `requests.RequestException` in a worker (a `ComboCurveAuthError` from a token
   refresh, an exception from `on_progress`) leaves `future.result()` and discards the whole result. Probed
   offline (code-fix 2026-11-22): 50 records in chunks of 10, the second token fetch raising; four chunks
   (40 records) were sent and the caller got only the exception, with no `may_have_applied` data.

Found by the same run's review (also pre-existing, `_transport.py` / `_batch.py`):

3. A write chunk answered with a 5xx other than 502/503/504 (a 500) is reported `may_have_applied=False`,
   which reads as "safe to resend"; nothing records that a ComboCurve 500 is atomic.
4. `BatchChunk.is_chunk_failure` is False for an HTTP error with an empty body (`error_message = ''`).
5. `_whole_chunk_failure` placeholders share one nested `errors` list (`dict(placeholder)` is a shallow copy).

## What was ruled out

Neither is a defect the branch introduced (byte-identical logic at `325478a`).

## What would unblock it

A decision on the shape: mark a non-envelope 2xx chunk as failed with `may_have_applied=True` (and invert the
pinning test), and catch every exception per chunk into `_whole_chunk_failure(..., may_have_applied=True)`.
Check first that no live write route answers a 2xx without a per-record `results` list.

## Files

`src/combocurve_api_helper/base.py` (`_request_batched`), `src/combocurve_api_helper/_batch.py`,
`src/combocurve_api_helper/_transport.py` (`_send_batch_chunk`), `tests/test_transport_module.py`
