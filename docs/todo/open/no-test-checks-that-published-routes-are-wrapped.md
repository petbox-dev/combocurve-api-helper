# No test checks that published routes are wrapped

Severity: low
Opened: 2026-11-05

## What happens now

The list in `published-routes-without-a-method.md` came from a one-time audit. No test repeats it.
A new published route stays unnoticed until a person compares the collection with the code.

## Decision

Approved 2026-11-05, for after 3.0.0.

## Method

The audit was call-based: call every public method on a fake transport, record the sent verb and path,
and compare the set with the verbs and paths in the Postman collection. Make this a network-gated test
in the style of `tests/test_route_paths.py` (skip when the collection is unreachable). Keep a reviewed
list of routes with no method, so a new route fails the test and a decision is recorded.

## Limit

The v2 type-curve routes are not in the collection (see `v2-type-curve-routes-have-no-postman-source.md`).
The test cannot cover them.

## Files

`tests/test_route_paths.py`, `tests/http_fakes.py`
